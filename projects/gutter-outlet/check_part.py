# /// script
# requires-python = ">=3.11"
# dependencies = ["cadquery", "numpy", "trimesh", "rtree"]
# ///
"""Spot the things a render hides: thin walls, knife edges, device collisions, overhangs.

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

import cadquery as cq
import numpy as np
import trimesh


def load_model(path):
    path = Path(path).resolve()
    os.chdir(path.parent)
    sys.path.insert(0, str(path.parent))
    code = compile(path.read_text(encoding="utf-8"), str(path), "exec")
    ns = {"__name__": "model", "__file__": str(path)}
    exec(code, ns)
    return ns


def to_trimesh(shape, tol=0.05):
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, "m.stl")
        cq.exporters.export(shape, f, tolerance=tol, angularTolerance=0.2)
        return trimesh.load(f, force="mesh")


def thin_walls(mesh, min_wall, samples=4000, seed=0):
    """Cast a ray inward from a sample of faces.

    Returns (min thickness, its point, thin area in mm2): the area is the surface
    whose sampled rays came back under min_wall, scaled from the sample to the
    whole mesh. A hairline notch where a fillet ends gives a tiny minimum but
    almost no area; a real sliver or a blocked channel gives area.
    """
    rng = np.random.default_rng(seed)
    n = len(mesh.faces)
    idx = rng.choice(n, size=min(samples, n), replace=False, p=mesh.area_faces / mesh.area)
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
    """Edges where the outward normals of the two faces differ by more than limit degrees."""
    from OCP.TopAbs import TopAbs_EDGE, TopAbs_FACE
    from OCP.TopExp import TopExp
    from OCP.TopTools import TopTools_IndexedDataMapOfShapeListOfShape
    amap = TopTools_IndexedDataMapOfShapeListOfShape()
    TopExp.MapShapesAndAncestors_s(shape.wrapped, TopAbs_EDGE, TopAbs_FACE, amap)
    found = []
    for e in shape.Edges():
        if e.Length() < 0.2:
            continue
        faces = [cq.Face(f) for f in amap.FindFromKey(e.wrapped)]
        if len(faces) != 2:
            continue
        p = e.positionAt(0.5)
        try:
            n1, n2 = (f.normalAt(p) for f in faces)
        except Exception:
            continue
        ang = math.degrees(n1.getAngle(n2))
        if ang > limit_deg:
            found.append((ang, e.Length(), p))
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
    x, y, z = (float(v) for v in (p if isinstance(p, np.ndarray) else p.toTuple()))
    return f"({x:.1f}, {y:.1f}, {z:.1f})"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("model")
    ap.add_argument("--min-wall", type=float, default=0.9, help="mm; thinner is a sliver")
    ap.add_argument("--knife", type=float, default=150.0, help="degrees between face normals")
    ap.add_argument("--overhang", type=float, default=45.0, help="degrees from vertical")
    ap.add_argument("--max-thin-area", type=float, default=5.0, help="mm2 of surface with a wall under --min-wall allowed")
    ap.add_argument("--max-overlap", type=float, default=0.05, help="cm3 the part may share with the device or a keep-clear volume")
    ap.add_argument("--max-overhang-area", type=float, default=100.0, help="mm2 of unsupported faces allowed")
    a = ap.parse_args()

    ns = load_model(a.model)
    part = ns["build"]()
    fails = []

    def report(ok, text):
        print(("ok   " if ok else "FAIL ") + text)
        if not ok:
            fails.append(text)

    def check_shape(shape, label, stl):
        solid = shape.val()
        report(solid.isValid(), f"{label}valid")
        n_solids = len(shape.solids().vals())
        report(n_solids == 1, f"{label}{n_solids} solid(s)")
        bb = solid.BoundingBox()
        print(f"     {label}size {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm, volume {solid.Volume() / 1000:.1f} cm3")
        mesh = to_trimesh(shape)
        t, at, thin_area = thin_walls(mesh, a.min_wall)
        if t is None:
            report(False, f"{label}thin walls: no ray hit anything, is the mesh closed?")
        else:
            report(thin_area <= a.max_thin_area,
                   f"{label}walls under {a.min_wall} mm cover about {thin_area:.0f} mm2; thinnest {t:.2f} mm at {fmt_pt(at)}")
        knives = knife_edges(solid, a.knife)
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
        for name, shape in parts().items():
            check_shape(shape, f"{name}: ", Path(f"{stem}_{name}.stl"))
        abb = part.val().BoundingBox()
        print(f"     assembly size {abb.xlen:.1f} x {abb.ylen:.1f} x {abb.zlen:.1f} mm")
    else:
        check_shape(part, "", stem.with_suffix(".stl"))

    device = ns.get("device")
    if callable(device):
        inter = part.intersect(device())
        vol = sum(s.Volume() for s in inter.solids().vals()) / 1000 if inter.solids().vals() else 0.0
        if vol > a.max_overlap:
            ib = inter.val().BoundingBox()
            report(False, f"part overlaps the device by {vol:.2f} cm3 in x {ib.xmin:.1f}..{ib.xmax:.1f}, "
                          f"y {ib.ymin:.1f}..{ib.ymax:.1f}, z {ib.zmin:.1f}..{ib.zmax:.1f}")
        else:
            report(True, "no overlap with the device")
    else:
        print("     no device() in the model, overlap not checked")

    clear = ns.get("keep_clear")
    if callable(clear):
        for i, shape in enumerate(clear()):
            inter = part.intersect(shape)
            vol = sum(s.Volume() for s in inter.solids().vals()) / 1000 if inter.solids().vals() else 0.0
            if vol > a.max_overlap:
                ib = inter.val().BoundingBox()
                report(False, f"keep-clear volume {i + 1} is blocked by {vol:.2f} cm3 in x {ib.xmin:.1f}..{ib.xmax:.1f}, "
                              f"y {ib.ymin:.1f}..{ib.ymax:.1f}, z {ib.zmin:.1f}..{ib.zmax:.1f}")
            else:
                report(True, f"keep-clear volume {i + 1} is empty")

    print(f"\n{len(fails)} problem(s)" if fails else "\nall checks passed")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
