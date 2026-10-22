# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Serve a live parameter configurator for a CadQuery model script on 127.0.0.1.

Usage: `uv run serve.py path/to/model.py [--port 8765] [--page configurator.html]`.
The page lists the top-level constants of the model, rebuilds the model with new
values in a worker process, and serves the shell and device meshes. Save writes the
values back into the model file and keeps each line's comment.

The server itself needs no CadQuery. The worker runs with `uv run --project` in the
model's own project (the folder with its pyproject.toml), so it builds with the
same locked CadQuery as `uv run model.py`. Without a project it falls back to the
interpreter that runs the server.
"""
import argparse
import ast
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

RANGE = re.compile(r"\[\s*(-?\d+(?:\.\d+)?)\s*:\s*(-?\d+(?:\.\d+)?)\s*\]\s*$")
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


def is_param(node):
    return (isinstance(node, ast.Assign) and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and isinstance(node.value, ast.Constant)
            and type(node.value.value) in (bool, int, float))


def clean_title(line):
    """The first sentence of a heading comment, without the final period."""
    text = line.lstrip("#").strip()
    return text.split(". ")[0].rstrip(".").strip()


def num(text):
    return float(text) if "." in text else int(text)


def param_of(node, lines):
    value = node.value.value
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
    groups, pending, title = {}, [], None
    for lineno in range(1, stop):
        if lineno in starts:
            for node in starts[lineno]:
                # A comment block directly above a statement starts a new group,
                # which runs until the next such block. Blank lines do not end it.
                if pending and isinstance(node, ast.Assign):
                    title = clean_title(pending[0]) or title
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
    return [{"title": t, "params": ps} for t, ps in groups.items()], has_device


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


# ---- worker: a long-lived subprocess that imports CadQuery once and builds on request ----

def build_once(cq, model, overrides, out):
    """Build the model with the overridden constants and export the meshes to out."""
    tree = ast.parse(model.read_text(encoding="utf-8"), filename=str(model))
    for node in head_nodes(tree):
        if is_param(node) and node.targets[0].id in overrides:
            name = node.targets[0].id
            node.value.value = coerce(node.value.value, overrides[name])
    code = compile(ast.fix_missing_locations(tree), str(model), "exec")
    ns = {"__name__": "model", "__file__": str(model)}
    exec(code, ns)
    part = ns["build"]()
    solid = part.val()
    assert solid.isValid(), "invalid solid"
    cq.exporters.export(part, str(out / "shell.stl"), tolerance=0.02, angularTolerance=0.1)
    device = ns.get("device")
    if callable(device):
        cq.exporters.export(device(), str(out / "device.stl"), tolerance=0.02, angularTolerance=0.1)
    bb = solid.BoundingBox()
    info = {"bbox": [bb.xlen, bb.ylen, bb.zlen], "volume_cm3": solid.Volume() / 1000}
    return part, info, callable(device)


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
    import cadquery as cq

    model = Path(model_path).resolve()
    os.chdir(model.parent)
    sys.path.insert(0, str(model.parent))
    last = None
    for line in sys.stdin:
        req = json.loads(line)
        buf = io.StringIO()
        reply = {"ok": False}
        try:
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                if req["cmd"] == "build":
                    last, info, has_device = build_once(cq, model, req["values"], Path(req["out"]))
                    reply = {"ok": True, "info": info, "device": has_device}
                elif req["cmd"] == "step":
                    if last is None:
                        raise RuntimeError("no build yet")
                    cq.exporters.export(last, req["out"])
                    reply = {"ok": True}
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
        self.last = None  # {"n", "root", "out", "device"} of the last successful build
        self.worker = Worker(model)


def run_build(srv, values):
    with srv.lock:
        srv.count += 1
        n = srv.count
        root = Path(tempfile.mkdtemp(prefix="cad-configurator-"))
        out = root / f"build-{n}"
        out.mkdir()
        t0 = time.monotonic()
        reply = srv.worker.request({"cmd": "build", "values": values, "out": str(out)})
        secs = time.monotonic() - t0
        log = reply.get("log", "")
        if not reply.get("ok"):
            shutil.rmtree(root, ignore_errors=True)
            return {"ok": False, "log": log}
        info = reply["info"]
        has_device = reply["device"]
        prev = srv.last
        srv.last = {"n": n, "root": root, "out": out, "device": has_device}
        if prev:
            shutil.rmtree(prev["root"], ignore_errors=True)
        return {"ok": True, "build": n, "seconds": round(secs, 2), "log": log,
                "bbox": info["bbox"], "volume_cm3": info["volume_cm3"],
                "shell": f"/api/mesh/shell.stl?build={n}",
                "device": f"/api/mesh/device.stl?build={n}" if has_device else None}


def export_step(srv):
    """Write the STEP of the last build on demand; it is too slow to do on every build."""
    with srv.lock:
        last = srv.last
        if not last:
            return None, "no build yet"
        f = last["out"] / "shell.step"
        if not f.exists():
            reply = srv.worker.request({"cmd": "step", "out": str(f)})
            if not reply.get("ok"):
                return None, reply.get("log", "STEP export failed")
        return f.read_bytes(), None


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
        check_values(values, {k: {"type": "bool" if type(n.value.value) is bool else "number"}
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
            new_text = fmt(c.value, values[name])
            if new_text != old_text:
                changed.append(name)
            lines[c.lineno - 1] = (raw[:c.col_offset] + new_text.encode("utf-8")
                                   + raw[c.end_col_offset:]).decode("utf-8")
        srv.model.write_bytes("".join(lines).encode("utf-8"))
        order = {n.targets[0].id: i for i, n in enumerate(targets)}
        return sorted(changed, key=lambda name: order[name])


class Handler(BaseHTTPRequestHandler):
    server_version = "CadConfigurator/1.0"

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
        f = last and last["out"] / name
        if not f or not f.exists():
            return self._json(404, {"ok": False, "error": "no mesh for the last build"})
        try:
            data = f.read_bytes()
        except FileNotFoundError:
            return self._json(404, {"ok": False, "error": "build was replaced"})
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
                return self._mesh("shell.stl")
            if path == "/api/mesh/device.stl":
                return self._mesh("device.stl")
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


def main():
    ap = argparse.ArgumentParser(description="Serve a parameter configurator for a CadQuery model.")
    ap.add_argument("model", help="the model script, for example mixer_sleeve.py")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--page", default=str(Path(__file__).resolve().parent / "configurator.html"),
                    help="the HTML page to serve at /")
    a = ap.parse_args()

    model = Path(a.model).resolve()
    if not model.is_file():
        ap.error(f"no such model: {model}")
    srv = Server(("127.0.0.1", a.port), Handler, model, Path(a.page).resolve())
    print(f"serving {model.name} at http://127.0.0.1:{a.port}/", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
        srv.worker.stop()
        if srv.last:
            shutil.rmtree(srv.last["root"], ignore_errors=True)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        worker(sys.argv[2])
    else:
        main()
