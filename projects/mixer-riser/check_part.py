# /// script
# dependencies = ["smlibpy==0.6.2", "numpy", "trimesh", "rtree"]
# ///
"""Spot the things a render hides in a smlibpy model: thin walls, knife edges, collisions, overhangs.

Usage: `uv run check_part.py model.py [--min-wall 0.9] [--knife 150] [--overhang 45]`.
The script runs the model's build(), and device() when it exists, and prints a report:

- validity and solid count,
- the thinnest wall, found by casting rays inward from the surface (a sample of faces),
- knife edges, where two faces meet at a dihedral angle above --knife degrees,
- device interference, the volume the part shares with device(),
- keep-clear volumes: shapes from keep_clear(), such as a water channel or screw
  access, that the part must not enter,
- overhangs in the print orientation, read from <stem>.stl next to the model when it
  exists: faces that point down more than --overhang degrees and are not on the bed.

A model with several printed parts defines parts() -> {name: shape} in print
orientation; then validity, walls, knife edges and overhangs (<stem>_<name>.stl)
run per part, and the device and keep-clear checks run on the assembly from build().

Exit code 1 when a check fails, so it can gate a commit. Thresholds default to a
0.4 mm nozzle: a wall under two lines (0.9 mm) is a sliver.
"""
import argparse
import math
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import trimesh
from smlibpy import export_stl


def load_model(path):
    path = Path(path).resolve()
    os.chdir(path.parent)
    sys.path.insert(0, str(path.parent))
    code = compile(path.read_text(encoding="utf-8"), str(path), "exec")
    ns = {"__name__": "model", "__file__": str(path)}
    exec(code, ns)
    return ns


def as_part(shape):
    """Return one smlibpy part. Fuse a list of parts into one part."""
    if isinstance(shape, (list, tuple)):
        out = shape[0]
        for s in shape[1:]:
            out = out + s
        return out
    return shape


def to_trimesh(shape, tol=0.05):
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, "m.stl")
        export_stl(shape, f, tolerance=tol, angle=12.0)
        return trimesh.load(f, force="mesh")


def members(shape):
    """Return the pieces of an assembly as a list. A single part gives a list of one part."""
    return list(shape) if isinstance(shape, (list, tuple)) else [shape]


def shared_volume(a, b):
    """Return the volume in mm3 that a part or assembly shares with b, and the largest overlap box.

    The check intersects each piece of an assembly alone and never fuses the pieces.
    """
    total, box, worst = 0.0, None, 0.0
    for piece in members(a):
        try:
            inter = piece & b
        except Exception:
            continue
        vol = float(getattr(inter, "volume", 0.0) or 0.0)
        total += vol
        if vol > worst:
            worst, box = vol, inter.bbox()
    return total, box


def assembly_size(shape):
    """Return the size of the box around all pieces of a part or an assembly."""
    boxes = [p.bbox() for p in members(shape)]
    return [max(b.max[i] for b in boxes) - min(b.min[i] for b in boxes) for i in range(3)]


def thin_walls(mesh, min_wall, samples=4000, seed=0):
    """Cast a ray inward from a sample of faces.

    Returns (min thickness, its point, thin area in mm2): the area is the surface
    whose sampled rays came back under min_wall, scaled from the sample to the
    whole mesh. A hairline notch where a fillet ends gives a tiny minimum but
    almost no area; a real sliver or a blocked channel gives area.
    """
    rng = np.random.default_rng(seed)
    good = np.flatnonzero(mesh.area_faces > 0)  # Degenerate triangles cannot be sampled.
    idx = rng.choice(good, size=min(samples, len(good)), replace=False,
                     p=mesh.area_faces[good] / mesh.area_faces[good].sum())
    origins = mesh.triangles_center[idx] - mesh.face_normals[idx] * 1e-3
    dirs = -mesh.face_normals[idx]
    locs, ray_ids, _ = mesh.ray.intersects_location(origins, dirs, multiple_hits=False)
    if len(ray_ids) == 0:
        return None, None, 0.0
    dist = np.linalg.norm(locs - origins[ray_ids], axis=1)
    k = int(np.argmin(dist))
    thin = dist < min_wall
    area = float(mesh.area_faces[idx[ray_ids][thin]].sum() * mesh.area / mesh.area_faces[idx].sum())
    return float(dist[k]), origins[ray_ids[k]], area


def knife_edges(shape, limit_deg):
    """Return the edges where the outward normals of the two faces differ by more than limit degrees."""
    found = []
    for e in shape.edges():
        if e.length < 0.2:
            continue
        faces = e.faces()
        if len(faces) != 2:
            continue
        p = e.point_at(0.5)
        try:
            n1, n2 = (np.asarray(tuple(f.normal_at(p)), float) for f in faces)
        except Exception:
            continue
        cos = float(np.dot(n1, n2) / (np.linalg.norm(n1) * np.linalg.norm(n2)))
        ang = math.degrees(math.acos(max(-1.0, min(1.0, cos))))
        if ang > limit_deg:
            found.append((ang, e.length, p))
    return sorted(found, key=lambda t: -t[0])


def overhangs(stl, limit_deg, bed_tol=0.3):
    m = trimesh.load(stl, force="mesh")
    # Two degrees of slack: the facets of a cone at exactly the limit must pass.
    down = m.face_normals[:, 2] < -math.cos(math.radians(90 - limit_deg - 2.0))
    off_bed = m.triangles_center[:, 2] > m.bounds[0][2] + bed_tol
    sel = down & off_bed
    area = float(m.area_faces[sel].sum())
    low = m.triangles_center[sel][:, 2].min() if sel.any() else None
    return area, low, m


def fmt_pt(p):
    x, y, z = (float(v) for v in tuple(p))
    return f"({x:.1f}, {y:.1f}, {z:.1f})"


def fmt_box(bb):
    lo, hi = tuple(bb.min), tuple(bb.max)
    return f"x {lo[0]:.1f}..{hi[0]:.1f}, y {lo[1]:.1f}..{hi[1]:.1f}, z {lo[2]:.1f}..{hi[2]:.1f}"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("model")
    ap.add_argument("--min-wall", type=float, default=0.9, help="mm; thinner is a sliver")
    ap.add_argument("--knife", type=float, default=150.0, help="degrees between face normals")
    ap.add_argument("--overhang", type=float, default=45.0, help="degrees from vertical")
    ap.add_argument("--max-thin-area", type=float, default=5.0, help="mm2 of surface with a wall under --min-wall allowed")
    ap.add_argument("--max-overlap", type=float, default=0.05, help="cm3 the part may share with the device or a keep-clear volume")
    ap.add_argument("--skip", default="", help="comma-separated part names to leave out, e.g. a printed spring that bends by design")
    ap.add_argument("--max-overhang-area", type=float, default=100.0, help="mm2 of unsupported faces allowed")
    a = ap.parse_args()

    ns = load_model(a.model)
    part = ns["build"]()  # A part, or a list of separate pieces for an assembly.
    fails = []

    def report(ok, text):
        print(("ok   " if ok else "FAIL ") + text)
        if not ok:
            fails.append(text)

    def check_shape(shape, label, stl):
        shape = as_part(shape)
        report(shape.is_valid(), f"{label}valid")
        n_solids = len(shape.solids())
        report(n_solids == 1, f"{label}{n_solids} solid(s)")
        sx, sy, sz = shape.bbox().size
        print(f"     {label}size {sx:.1f} x {sy:.1f} x {sz:.1f} mm, volume {shape.volume / 1000:.1f} cm3")
        mesh = to_trimesh(shape)
        t, at, thin_area = thin_walls(mesh, a.min_wall)
        if t is None:
            report(False, f"{label}thin walls: no ray hit anything, is the mesh closed?")
        else:
            report(thin_area <= a.max_thin_area,
                   f"{label}walls under {a.min_wall} mm cover about {thin_area:.0f} mm2; thinnest {t:.2f} mm at {fmt_pt(at)}")
        knives = knife_edges(shape, a.knife)
        if knives:
            worst = knives[0]
            report(False, f"{label}{len(knives)} knife edge(s): worst {worst[0]:.0f} deg over {worst[1]:.1f} mm at {fmt_pt(worst[2])}")
        else:
            report(True, f"{label}no knife edges above {a.knife:.0f} deg")
        if stl.exists():
            area, low, m = overhangs(stl, a.overhang)
            report(area <= a.max_overhang_area,
                   f"{label}overhangs past {a.overhang:.0f} deg in {stl.name}: {area:.0f} mm2"
                   + (f", lowest at z = {low:.1f}" if low is not None else ""))
            print(f"     {label}print size {m.extents[0]:.1f} x {m.extents[1]:.1f} x {m.extents[2]:.1f} mm")
        else:
            print(f"     {label}no {stl.name} next to the model, overhangs not checked")

    stem = Path(a.model).with_suffix("")
    parts = ns.get("parts")
    if callable(parts):
        skip = {n.strip() for n in a.skip.split(",") if n.strip()}
        for name, shape in parts().items():
            if name in skip:
                print(f"     {name}: skipped")
                continue
            stl = Path(f"{stem}_{name}.stl")
            if not stl.exists() and (stem.parent / f"{name}.stl").exists():
                stl = stem.parent / f"{name}.stl"  # Models that export plain <name>.stl per part.
            check_shape(shape, f"{name}: ", stl)
        ax, ay, az = assembly_size(part)
        print(f"     assembly size {ax:.1f} x {ay:.1f} x {az:.1f} mm")
    else:
        check_shape(part, "", stem.with_suffix(".stl"))

    device = ns.get("device")
    if callable(device):
        vol, ib = shared_volume(part, as_part(device()))  # A device of several pieces may fuse.
        vol /= 1000
        if vol > a.max_overlap:
            report(False, f"part overlaps the device by {vol:.2f} cm3 in {fmt_box(ib)}")
        else:
            report(True, "no overlap with the device")
    else:
        print("     no device() in the model, overlap not checked")

    clear = ns.get("keep_clear")
    if callable(clear):
        for i, shape in enumerate(clear()):
            vol, ib = shared_volume(part, as_part(shape))
            vol /= 1000
            if vol > a.max_overlap:
                report(False, f"keep-clear volume {i + 1} is blocked by {vol:.2f} cm3 in {fmt_box(ib)}")
            else:
                report(True, f"keep-clear volume {i + 1} is empty")

    print(f"\n{len(fails)} problem(s)" if fails else "\nall checks passed")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
