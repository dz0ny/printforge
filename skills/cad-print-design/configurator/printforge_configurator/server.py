"""Serve a live parameter configurator for an smlibpy model script on 127.0.0.1.

Two ways in:
- `python -m printforge_configurator path/to/model.py [--port 8765]` for any script.
- `from printforge_configurator import serve; serve(__file__)` from the script itself,
  for example behind a `--serve` flag in its `__main__` block.
The page lists the top-level constants of the model, rebuilds the model with new
values in a worker process, and serves the shell and device meshes. Save writes the
values back into the model file and keeps each line's comment.

The server itself needs no CAD library. The worker runs with `uv run --project` in
the model's own project (the folder with its pyproject.toml), so it builds with the
same locked smlibpy as `uv run model.py`. Without a project it falls back to the
interpreter that runs the server.
"""
import argparse
import ast
import hashlib
import json
import math
import os
import re
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

RANGE = re.compile(r"\[\s*(-?\d+(?:\.\d+)?)\s*:\s*(-?\d+(?:\.\d+)?)\s*\]\s*\.?\s*$")
DEF_NODES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


class BadRequest(Exception):
    pass


def head_nodes(tree):
    """Top-level statements above the first def or class."""
    out = []
    for node in tree.body:
        if isinstance(node, DEF_NODES):
            break
        out.append(node)
    return out


def literal(node):
    """The number or bool literal an assignment holds, or None. `-8.0` counts as a literal."""
    v = node.value
    if isinstance(v, ast.UnaryOp) and isinstance(v.op, ast.USub) and isinstance(v.operand, ast.Constant) \
            and type(v.operand.value) in (int, float):
        return -v.operand.value
    if isinstance(v, ast.Constant) and type(v.value) in (bool, int, float):
        return v.value
    return None


def is_param(node):
    return (isinstance(node, ast.Assign) and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name) and literal(node) is not None)


def clean_title(line):
    """The first sentence of a heading comment, without the final period, as (icon, title).

    A heading may start with an emoji, for example `# 🎛️ Mixer body size in mm.`;
    that leading symbol is the group's icon.
    """
    text = line.lstrip("#").strip()
    text = text.split(". ")[0].rstrip(".").strip()
    icon = None
    parts = text.split(None, 1)
    if len(parts) == 2 and not any(ch.isalnum() for ch in parts[0]):
        icon, text = parts
    return icon, text


def num(text):
    return float(text) if "." in text else int(text)


def param_of(node, lines):
    value = literal(node)
    raw = lines[node.end_lineno - 1].encode("utf-8")
    rest = raw[node.end_col_offset:].decode("utf-8", "replace")
    desc = rest.split("#", 1)[1].strip() if "#" in rest else ""
    p = {"name": node.targets[0].id, "value": value,
         "type": "bool" if isinstance(value, bool) else "number", "description": desc}
    m = RANGE.search(desc)
    if m:
        p["description"] = desc[:m.start()].strip()
        p["min"] = num(m.group(1))
        p["max"] = num(m.group(2))
    return p


def parse_model(path):
    """Return (groups, has_device) for the model file. Re-reads the file on every call."""
    src = Path(path).read_text(encoding="utf-8")
    lines = src.splitlines()
    tree = ast.parse(src, filename=str(path))
    head = head_nodes(tree)
    stop = tree.body[len(head)].lineno if len(head) < len(tree.body) else len(lines) + 1
    starts, covered = {}, set()
    for node in head:
        starts.setdefault(node.lineno, []).append(node)
        covered.update(range(node.lineno + 1, node.end_lineno + 1))
    groups, icons, pending, title = {}, {}, [], None
    for lineno in range(1, stop):
        if lineno in starts:
            for node in starts[lineno]:
                # A comment block directly above a statement starts a new group,
                # which runs until the next such block. Blank lines do not end it.
                if pending and isinstance(node, ast.Assign):
                    icon, text = clean_title(pending[0])
                    if text:
                        title = text
                        icons[title] = icon
                pending = []
                if is_param(node):
                    groups.setdefault(title or "Settings", []).append(param_of(node, lines))
            continue
        if lineno in covered:
            continue
        text = lines[lineno - 1].strip()
        if text.startswith("#"):
            pending.append(text)
        elif not text:
            pending = []
    has_device = any(isinstance(n, ast.FunctionDef) and n.name == "device" for n in tree.body)
    return [{"title": t, "icon": icons.get(t), "params": ps} for t, ps in groups.items()], has_device


def param_table(path):
    groups, _ = parse_model(path)
    return {p["name"]: p for g in groups for p in g["params"]}


def check_values(values, table):
    if not isinstance(values, dict):
        raise BadRequest("values must be an object")
    for name, v in values.items():
        if name not in table:
            raise BadRequest(f"unknown parameter: {name}")
        if table[name]["type"] == "bool":
            ok = isinstance(v, bool)
        else:
            ok = isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
        if not ok:
            raise BadRequest(f"bad value for {name}: {v!r}")


def coerce(old, new):
    if type(old) is bool:
        return bool(new)
    if type(old) is int:
        return int(new) if float(new).is_integer() else float(new)
    return float(new)


def fmt(old, new):
    """Source text for a new value, following the type of the old literal."""
    if type(old) is bool:
        return "True" if new else "False"
    if type(old) is int and float(new).is_integer():
        return str(int(new))
    return repr(float(new))


def _text(x):
    if x is None:
        return ""
    return x.decode("utf-8", "replace") if isinstance(x, bytes) else x


def worker_command(model):
    """The interpreter for the worker: the model's uv project when it has one."""
    project = Path(model).resolve().parent
    if (project / "pyproject.toml").exists() and shutil.which("uv"):
        return ["uv", "run", "--project", str(project), "python"]
    return [sys.executable]


# ---- worker: a long-lived subprocess that loads the CAD library once and builds on request ----

def is_smlibpy(shape):
    """Return True for an smlibpy shape, or a list of smlibpy shapes."""
    if isinstance(shape, (list, tuple)):
        return bool(shape) and is_smlibpy(shape[0])
    return type(shape).__module__.split(".")[0] == "smlibpy"


class SmlibpyBackend:
    """Export and measure smlibpy parts."""

    def __init__(self):
        import smlibpy
        self.sm = smlibpy
        self.meshes = {}  # The STL bytes of each piece, keyed by a hash of its exact body.

    def pieces(self, shape):
        """Return the pieces of an assembly as a list. The worker never fuses them."""
        return list(shape) if isinstance(shape, (list, tuple)) else [shape]

    def stl(self, shape, path):
        """Write one binary STL of all pieces, from a mesh per piece.

        The worker keeps the mesh of each piece in memory, keyed by a hash of its exact body.
        A slider change thus meshes only the pieces it changed: the 1,000 sieve holes of the cocoa body take seconds.
        The chord tolerance of 0.02 mm sets the smoothness, and the angle of 30 degrees only limits tiny holes.
        """
        import hashlib
        import struct
        tris, count = [], 0
        for piece in self.pieces(shape):
            key = hashlib.sha1(self.sm.to_smb(piece, ascii=False)).hexdigest()
            data = self.meshes.get(key)
            if data is None:
                tmp = Path(path).with_suffix(".piece.stl")
                self.sm.export_stl(piece, str(tmp), tolerance=0.02, angle=30.0)
                data = tmp.read_bytes()
                tmp.unlink()
                self.meshes[key] = data
                while len(self.meshes) > 64:
                    del self.meshes[next(iter(self.meshes))]
            n = struct.unpack("<I", data[80:84])[0]
            tris.append(data[84:84 + 50 * n])
            count += n
        Path(path).write_bytes(b"printforge configurator".ljust(80, b" ") + struct.pack("<I", count) + b"".join(tris))

    def step(self, shape, path):
        self.sm.export_step(self.pieces(shape), str(path))

    def info(self, shape):
        ps = self.pieces(shape)
        assert all(p.is_valid() for p in ps), "invalid solid"
        boxes = [p.bbox() for p in ps]
        size = [max(b.max[i] for b in boxes) - min(b.min[i] for b in boxes) for i in range(3)]
        return size, sum(p.volume for p in ps) / 1000

    def drawing(self, shape, out):
        return smlibpy_drawing_views(self.sm, self.pieces(shape))


_BACKEND = []


def backend_for(shape):
    """Return the smlibpy backend. Stop with a clear message for a shape from another library."""
    if not is_smlibpy(shape):
        raise TypeError(f"build() returned a {type(shape).__module__}.{type(shape).__name__}. "
                        "The configurator builds smlibpy models only: return an smlibpy Part or a list of parts.")
    if not _BACKEND:
        _BACKEND.append(SmlibpyBackend())
    return _BACKEND[0]


def build_once(model, overrides, out):
    """Build the model with the overridden constants and export the meshes to out."""
    tree = ast.parse(model.read_text(encoding="utf-8"), filename=str(model))
    for node in head_nodes(tree):
        if is_param(node) and node.targets[0].id in overrides:
            name = node.targets[0].id
            node.value = ast.Constant(coerce(literal(node), overrides[name]))
    code = compile(ast.fix_missing_locations(tree), str(model), "exec")
    ns = {"__name__": "model", "__file__": str(model)}
    exec(code, ns)
    part = ns["build"]()
    be = backend_for(part)
    size, volume = be.info(part)
    be.stl(part, out / "shell.stl")
    device = ns.get("device")
    if callable(device):
        be.stl(device(), out / "device.stl")
    info = {"bbox": size, "volume_cm3": volume, "features": feature_list(ns)}
    return part, info, callable(device), ns


def feature_list(ns):
    """The model's features() as a list the page can use, or [] when it has none.

    features() returns {name: {"at": (x, y, z), "normal": (nx, ny, nz), "params": [names]}}
    in the same frame as the exported meshes.
    """
    fn = ns.get("features")
    if not callable(fn):
        return []
    out = []
    for name, f in fn().items():
        out.append({"name": name, "at": [float(v) for v in f["at"]],
                    "normal": [float(v) for v in f.get("normal", (0, 0, 1))],
                    "params": list(f.get("params", []))})
    return out


DRAWING_VIEWS = {
    "top": ((0, 0, 1), (0, 1, 0)),
    "front": ((0, -1, 0), (0, 0, 1)),
    "right": ((1, 0, 0), (0, 0, 1)),
    "iso": ((1, -1, 0.8), (0, 0, 1)),
}


def _iso_turn(sm, part, direction):
    """Turn the part, or each piece of a list, so that the iso camera direction looks from the front (-Y)."""
    if isinstance(part, (list, tuple)):
        return [_iso_turn(sm, p, direction) for p in part]
    x, y, z = direction
    yaw = math.degrees(math.atan2(-x, -y))
    turned = part.rotate(sm.Axis.Z, yaw)
    tilt = math.degrees(math.atan2(z, math.hypot(x, y)))
    return turned.rotate(sm.Axis.X, tilt)


def _guard_child(fn, conn):
    try:
        conn.send(fn())
    except Exception:
        conn.send(None)
    finally:
        conn.close()


def guarded(fn, timeout=60.0):
    """Run fn() in a forked copy of this process and return its result.

    Return None when the copy crashes, raises or takes longer than timeout.
    The hidden-line step of the kernel can crash on some parts, and the worker must stay alive.
    """
    import multiprocessing as mp
    ctx = mp.get_context("fork")
    recv, send = ctx.Pipe(duplex=False)
    proc = ctx.Process(target=_guard_child, args=(fn, send))
    proc.start()
    send.close()
    result = None
    try:
        if recv.poll(timeout):
            result = recv.recv()
    except EOFError:
        result = None  # The copy crashed before it sent an answer.
    proc.join(1.0)
    if proc.is_alive():
        proc.kill()
    return result


# Iso directions to try in turn: the kernel often draws a near direction where it crashed on the first.
ISO_TRIES = [(1, -1, 0.8), (1, -0.9, 0.8), (1, -1, 0.7)]


def smlibpy_drawing_views(sm, part):
    """Return smlibpy's own SVG of each hidden-line view, keyed by view.

    The SVG has its viewBox in model mm, arcs as exact A commands and other curves as polylines.
    It draws the hidden lines dashed, and the page reads this format directly.
    Each view runs in a forked copy, because the hidden-line step can crash the process.
    A view that fails is an empty string, and the page shows that view as unavailable.
    """
    def svg_of(shape, view):
        dv = sm.drawing_views(shape, (view,))
        return sm.to_svg(dv) if (dv[0].visible or dv[0].hidden) else ""

    views = {}
    for name in DRAWING_VIEWS:
        if name == "iso":
            svg = None
            for direction in ISO_TRIES:
                t0 = time.monotonic()
                svg = guarded(lambda d=direction: svg_of(_iso_turn(sm, part, d), "front"))
                if svg is not None or time.monotonic() - t0 > 50:
                    break  # A view that ran out of time on one direction runs out of time on the others too.
        else:
            svg = guarded(lambda n=name: svg_of(part, n))
        if svg is None:
            print(f"drawing: the {name} view failed in the kernel")
        views[name] = svg or ""
    return views


def worker(model_path):
    """Read one JSON request per line on stdin and answer one JSON line on stdout.

    {"cmd": "build", "values": {...}, "out": dir} -> {"ok", "log", "info", "device"}
    {"cmd": "step", "out": file}                  -> {"ok", "log"}
    The model's own prints go into "log", never onto the protocol stream.
    """
    import contextlib
    import io
    import traceback

    proto = sys.stdout
    sys.stdout = sys.stderr  # Stray prints from imports must not corrupt the protocol.

    model = Path(model_path).resolve()
    os.chdir(model.parent)
    sys.path.insert(0, str(model.parent))
    last, last_ns = None, {}
    for line in sys.stdin:
        req = json.loads(line)
        buf = io.StringIO()
        reply = {"ok": False}
        try:
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                if req["cmd"] == "build":
                    last, info, has_device, last_ns = build_once(model, req["values"], Path(req["out"]))
                    reply = {"ok": True, "info": info, "device": has_device}
                elif req["cmd"] == "step":
                    if last is None:
                        raise RuntimeError("no build yet")
                    backend_for(last).step(last, req["out"])
                    reply = {"ok": True}
                elif req["cmd"] == "drawing":
                    if last is None:
                        raise RuntimeError("no build yet")
                    # A model can give lighter shapes for the drawing, for example a sieve without its holes.
                    hook = last_ns.get("drawing_shapes")
                    shapes = hook() if callable(hook) else last
                    reply = {"ok": True, "views": backend_for(shapes).drawing(shapes, Path(req["out"]))}
        except AssertionError as e:
            # A design rule from the model's own asserts: say it plainly, no traceback.
            buf.write(f"Design rule: {e}\n")
        except Exception:
            buf.write(traceback.format_exc())
        reply["log"] = buf.getvalue()
        proto.write(json.dumps(reply) + "\n")
        proto.flush()


class Worker:
    """The server's handle on the worker process. Restarts it when it died."""

    def __init__(self, model):
        self.model = model
        self.proc = None
        self.queue = None

    def _start(self):
        cmd = worker_command(self.model) + [str(Path(__file__).resolve()), "--worker", str(self.model)]
        # Drop the server's own uv environment, so uv picks the project's without a warning.
        env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, text=True, bufsize=1, env=env)
        self.queue = queue.Queue()
        threading.Thread(target=self._pump, args=(self.proc,), daemon=True).start()
        threading.Thread(target=self._drain, args=(self.proc,), daemon=True).start()

    def _pump(self, proc):
        for line in proc.stdout:
            self.queue.put(line)
        self.queue.put(None)

    def _drain(self, proc):
        for line in proc.stderr:
            sys.stderr.write("worker: " + line)

    def request(self, req, timeout=600):
        if self.proc is None or self.proc.poll() is not None:
            self._start()
        try:
            self.proc.stdin.write(json.dumps(req) + "\n")
            self.proc.stdin.flush()
            line = self.queue.get(timeout=timeout)
        except (BrokenPipeError, queue.Empty, ValueError):
            self.stop()
            return {"ok": False, "log": f"worker gave no answer within {timeout} s; restarted\n"}
        if line is None:
            code = self.proc.poll()
            self.stop()
            return {"ok": False, "log": f"worker exited with code {code}; it restarts on the next build\n"}
        return json.loads(line)

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.kill()
        self.proc = None


# ---- server ----

class Server(ThreadingHTTPServer):
    def __init__(self, addr, handler, model, page):
        super().__init__(addr, handler)
        self.model = model
        self.page = page
        self.lock = threading.Lock()
        self.count = 0
        self.last = None  # The current build entry, see run_build.
        self.cache = {}  # key -> entry, in memory only, newest last. See build_key.
        self.worker = Worker(model)
        self.worker_key = None  # The key of the build the worker holds for STEP export.


CACHE_SIZE = 8  # Builds kept in memory; a mesh is a few MB.


def build_key(model, values):
    """A build is the model source plus the values, so the same input never builds twice."""
    h = hashlib.sha256(model.read_bytes())
    h.update(json.dumps(values, sort_keys=True).encode("utf-8"))
    return h.hexdigest()


def run_build(srv, values):
    with srv.lock:
        key = build_key(srv.model, values)
        entry = srv.cache.get(key)
        if entry is None:
            entry = build_entry(srv, key, values)
            if not entry["ok"]:
                return {"ok": False, "log": entry["log"]}
            srv.cache[key] = entry
            while len(srv.cache) > CACHE_SIZE:
                del srv.cache[next(iter(srv.cache))]
        else:
            srv.cache[key] = srv.cache.pop(key)  # Mark it as the newest.
        srv.count += 1
        n = srv.count
        srv.last = entry
        cached = entry.get("served", False)
        entry["served"] = True
        return {"ok": True, "build": n, "key": key, "seconds": 0.0 if cached else entry["seconds"], "cached": cached,
                "log": entry["log"], "bbox": entry["info"]["bbox"], "volume_cm3": entry["info"]["volume_cm3"],
                "features": entry["info"].get("features", []),
                "shell": f"/api/mesh/shell.stl?build={n}",
                "device": f"/api/mesh/device.stl?build={n}" if entry["device"] is not None else None}


def build_entry(srv, key, values):
    """Run the worker once and keep everything it produced in memory."""
    root = Path(tempfile.mkdtemp(prefix="cad-configurator-"))
    try:
        t0 = time.monotonic()
        reply = srv.worker.request({"cmd": "build", "values": values, "out": str(root)})
        secs = time.monotonic() - t0
        log = reply.get("log", "")
        if not reply.get("ok"):
            return {"ok": False, "log": log}
        srv.worker_key = key
        device = root / "device.stl"
        return {"ok": True, "key": key, "values": values, "seconds": round(secs, 2), "log": log,
                "info": reply["info"], "shell": (root / "shell.stl").read_bytes(),
                "device": device.read_bytes() if device.exists() else None, "step": None}
    finally:
        shutil.rmtree(root, ignore_errors=True)


def export_drawing(srv):
    """The drawing views of the current build, made on demand and kept with the entry."""
    with srv.lock:
        entry = srv.last
        if not entry:
            return None, "no build yet"
        if entry.get("drawing") is None:
            if srv.worker_key != entry["key"]:
                fresh = build_entry(srv, entry["key"], entry["values"])
                if not fresh["ok"]:
                    return None, fresh["log"]
            root = Path(tempfile.mkdtemp(prefix="cad-configurator-"))
            try:
                reply = srv.worker.request({"cmd": "drawing", "out": str(root)})
                if not reply.get("ok"):
                    return None, reply.get("log", "drawing failed")
                entry["drawing"] = reply["views"]
            finally:
                shutil.rmtree(root, ignore_errors=True)
        return {"ok": True, "key": entry["key"], "bbox": entry["info"]["bbox"], "views": entry["drawing"]}, None


def export_step(srv):
    """The STEP of the current build, exported on demand and then kept in memory."""
    with srv.lock:
        entry = srv.last
        if not entry:
            return None, "no build yet"
        if entry["step"] is None:
            if srv.worker_key != entry["key"]:
                # The worker holds another build (a cache hit): rebuild it there first.
                fresh = build_entry(srv, entry["key"], entry["values"])
                if not fresh["ok"]:
                    return None, fresh["log"]
            root = Path(tempfile.mkdtemp(prefix="cad-configurator-"))
            try:
                f = root / "shell.step"
                reply = srv.worker.request({"cmd": "step", "out": str(f)})
                if not reply.get("ok"):
                    return None, reply.get("log", "STEP export failed")
                entry["step"] = f.read_bytes()
            finally:
                shutil.rmtree(root, ignore_errors=True)
        return entry["step"], None


def save_values(srv, values):
    with srv.lock:
        src = srv.model.read_text(encoding="utf-8")
        tree = ast.parse(src, filename=str(srv.model))
        lines = src.splitlines(keepends=True)
        table = {}
        targets = []
        for node in head_nodes(tree):
            if is_param(node):
                table[node.targets[0].id] = node
                if node.targets[0].id in values:
                    targets.append(node)
        check_values(values, {k: {"type": "bool" if type(literal(n)) is bool else "number"}
                              for k, n in table.items()})
        changed = []
        # Edit later columns first so earlier offsets on the same line stay valid.
        for node in sorted(targets, key=lambda n: (n.lineno, n.value.col_offset), reverse=True):
            name = node.targets[0].id
            c = node.value
            if c.lineno != c.end_lineno:
                raise BadRequest(f"{name} spans several lines")
            raw = lines[c.lineno - 1].encode("utf-8")
            old_text = raw[c.col_offset:c.end_col_offset].decode("utf-8")
            new_text = fmt(literal(node), values[name])
            if new_text != old_text:
                changed.append(name)
            lines[c.lineno - 1] = (raw[:c.col_offset] + new_text.encode("utf-8")
                                   + raw[c.end_col_offset:]).decode("utf-8")
        srv.model.write_bytes("".join(lines).encode("utf-8"))
        order = {n.targets[0].id: i for i, n in enumerate(targets)}
        return sorted(changed, key=lambda name: order[name])


class Handler(BaseHTTPRequestHandler):
    server_version = "CadConfigurator/1.0"

    def handle_one_request(self):
        try:
            super().handle_one_request()
        except (ConnectionResetError, BrokenPipeError, OSError):
            # A client that dropped the connection, or a connection the macOS
            # firewall cut off: nothing to serve, nothing to print.
            self.close_connection = True

    def _send(self, code, body, ctype, headers=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code, obj):
        self._send(code, json.dumps(obj).encode("utf-8"), "application/json")

    def _body(self):
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        try:
            data = json.loads(raw or b"{}")
        except json.JSONDecodeError as e:
            raise BadRequest(f"invalid JSON: {e}")
        if not isinstance(data, dict):
            raise BadRequest("body must be a JSON object")
        return data

    def _mesh(self, name):
        last = self.server.last
        data = last and last[name]
        if not data:
            return self._json(404, {"ok": False, "error": "no mesh for the last build"})
        self._send(200, data, "model/stl", {"Cache-Control": "no-store"})

    def do_GET(self):
        srv = self.server
        path = urlsplit(self.path).path
        try:
            if path == "/":
                if not srv.page.is_file():
                    return self._json(404, {"ok": False, "error": f"page not found: {srv.page}"})
                return self._send(200, srv.page.read_bytes(), "text/html; charset=utf-8")
            if path == "/api/params":
                groups, has_device = parse_model(srv.model)
                return self._json(200, {"model": srv.model.name, "groups": groups,
                                        "has_device": has_device})
            if path == "/api/mesh/shell.stl":
                return self._mesh("shell")
            if path == "/api/mesh/device.stl":
                return self._mesh("device")
            if path == "/api/drawing":
                data, err = export_drawing(srv)
                if err:
                    return self._json(200, {"ok": False, "log": err})
                return self._json(200, data)
            if path == "/api/step":
                data, err = export_step(srv)
                if err:
                    return self._json(404, {"ok": False, "error": err})
                return self._send(200, data, "application/step", {
                    "Content-Disposition": f'attachment; filename="{srv.model.stem}.step"'})
            return self._json(404, {"ok": False, "error": f"not found: {path}"})
        except Exception as e:
            return self._json(500, {"ok": False, "error": str(e)})

    def do_POST(self):
        srv = self.server
        path = urlsplit(self.path).path
        try:
            if path == "/api/build":
                body = self._body()
                values = body.get("values", {})
                check_values(values, param_table(srv.model))
                return self._json(200, run_build(srv, values))
            if path == "/api/save":
                body = self._body()
                values = body.get("values", {})
                changed = save_values(srv, values)
                return self._json(200, {"ok": True, "changed": changed})
            return self._json(404, {"ok": False, "error": f"not found: {path}"})
        except BadRequest as e:
            return self._json(400, {"ok": False, "error": str(e)})
        except Exception as e:
            return self._json(500, {"ok": False, "error": str(e)})


PAGE = Path(__file__).resolve().parent / "configurator.html"


def lan_ip():
    """This machine's address on the local network, for a phone to reach the page."""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return None


def serve(model, port=8765, page=None, open_browser=False, host="127.0.0.1"):
    """Serve the configurator for a model script until Ctrl-C.

    `model` is the script's path, usually `__file__`. The call blocks.
    `host="0.0.0.0"` opens it to the local network, for a phone or a tablet.
    """
    model = Path(model).resolve()
    if not model.is_file():
        raise FileNotFoundError(f"no such model: {model}")
    page = Path(page).resolve() if page else PAGE
    srv = Server((host, port), Handler, model, page)
    url = f"http://127.0.0.1:{port}/"
    print(f"serving {model.name} at {url}", flush=True)
    if host == "0.0.0.0" and lan_ip():
        print(f"on the local network: http://{lan_ip()}:{port}/", flush=True)
    if open_browser:
        import webbrowser
        webbrowser.open(url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
        srv.worker.stop()


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    if len(argv) == 2 and argv[0] == "--worker":
        worker(argv[1])
        return
    ap = argparse.ArgumentParser(prog="printforge_configurator",
                                 description="Serve a parameter configurator for an smlibpy model.")
    ap.add_argument("model", help="the model script, for example mixer_sleeve.py")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--page", default=None, help="an HTML page to serve at / instead of the built-in one")
    ap.add_argument("--open", action="store_true", help="open the page in the default browser")
    ap.add_argument("--host", default="127.0.0.1", help="0.0.0.0 to reach it from a phone on the same network")
    a = ap.parse_args(argv)
    try:
        serve(a.model, port=a.port, page=a.page, open_browser=a.open, host=a.host)
    except FileNotFoundError as e:
        ap.error(str(e))


if __name__ == "__main__":
    main()
