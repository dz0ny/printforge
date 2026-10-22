# /// script
# dependencies = []
# ///
"""Write a Bambu Studio / OrcaSlicer 3MF project from an STL and recommended settings.

Usage: `uv run make_3mf.py part.stl --settings print.json --out part.3mf [--template saved.3mf]`.
The settings file holds slicer keys, for example {"layer_height": "0.28", "wall_loops": "3"}.
The script stores the settings on the object, and object settings override the project process.
With `--template`, the file also gets the printer, filament and process of a saved project.
The template is a saved .3mf or the `Metadata/project_settings.config` file from one.
"""
import argparse
import json
import struct
import uuid
import zipfile
from pathlib import Path

XML = '<?xml version="1.0" encoding="UTF-8"?>'
NS_3MF = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
NS_BBL = "http://schemas.bambulab.com/package/2021"
NS_PKG = "http://schemas.openxmlformats.org/package/2006"
REL_MODEL = "http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"


def read_stl(path):
    """Return vertices and triangles from a binary or ASCII STL. Shared vertices merge."""
    data = Path(path).read_bytes()
    tris = []
    if data[:5] == b"solid" and b"facet" in data[:400]:
        pts = [tuple(float(v) for v in line.split()[1:4])
               for line in data.decode().splitlines() if line.strip().startswith("vertex")]
        tris = [pts[i:i + 3] for i in range(0, len(pts), 3)]
    else:
        n = struct.unpack("<I", data[80:84])[0]
        for i in range(n):
            o = 84 + i * 50 + 12
            v = struct.unpack("<9f", data[o:o + 36])
            tris.append([v[0:3], v[3:6], v[6:9]])
    index, verts, faces = {}, [], []
    for t in tris:
        f = []
        for p in t:
            key = tuple(round(c, 5) for c in p)
            if key not in index:
                index[key] = len(verts)
                verts.append(key)
            f.append(index[key])
        if len(set(f)) == 3:
            faces.append(f)
    return verts, faces


def model_xml(verts, faces, app, center):
    xs, ys, zs = zip(*verts)
    # Centre the mesh on its bounding box, as Bambu Studio does, and lift the item by half its height.
    cx, cy, cz = ((min(c) + max(c)) / 2 for c in (xs, ys, zs))
    height = max(zs) - min(zs)
    lines = [XML, f'<model unit="millimeter" xml:lang="en-US" xmlns="{NS_3MF}" xmlns:BambuStudio="{NS_BBL}">',
             f' <metadata name="Application">{app}</metadata>',
             ' <metadata name="BambuStudio:3mfVersion">1</metadata>',
             ' <resources>', '  <object id="1" type="model">', '   <mesh>', '    <vertices>']
    lines += [f'     <vertex x="{x - cx:.5f}" y="{y - cy:.5f}" z="{z - cz:.5f}"/>' for x, y, z in verts]
    lines += ['    </vertices>', '    <triangles>']
    lines += [f'     <triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in faces]
    lines += ['    </triangles>', '   </mesh>', '  </object>', ' </resources>', ' <build>',
              f'  <item objectid="1" transform="1 0 0 0 1 0 0 0 1 {center[0]} {center[1]} {height / 2:.4f}" printable="1"/>',
              ' </build>', '</model>']
    return "\n".join(lines), height


def settings_xml(name, settings, faces, height, center):
    lines = [XML, '<config>', '  <object id="1">',
             f'    <metadata key="name" value="{name}"/>',
             '    <metadata key="extruder" value="1"/>']
    lines += [f'    <metadata key="{k}" value="{v}"/>' for k, v in settings.items()]
    lines += [f'    <part id="1" subtype="normal_part" uuid="{uuid.uuid4()}">',
              f'      <metadata key="name" value="{name}"/>',
              '      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>',
              f'      <mesh_stat face_count="{len(faces)}" edges_fixed="0" degenerate_facets="0"'
              ' facets_removed="0" facets_reversed="0" backwards_edges="0"/>',
              '    </part>', '  </object>', '  <plate>',
              '    <metadata key="plater_id" value="1"/>',
              '    <metadata key="plater_name" value=""/>',
              '    <metadata key="locked" value="false"/>',
              '    <model_instance>', '      <metadata key="object_id" value="1"/>',
              '      <metadata key="instance_id" value="0"/>', '    </model_instance>', '  </plate>',
              '  <assemble>',
              f'   <assemble_item object_id="1" instance_id="0" transform="1 0 0 0 1 0 0 0 1'
              f' {center[0]} {center[1]} {height / 2:.4f}" offset="0 0 0" />',
              '  </assemble>', '</config>']
    return "\n".join(lines)


def package_files():
    types = "\n".join([XML, f'<Types xmlns="{NS_PKG}/content-types">',
                       f' <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
                       ' <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>',
                       ' <Default Extension="png" ContentType="image/png"/>', '</Types>'])
    rels = "\n".join([XML, f'<Relationships xmlns="{NS_PKG}/relationships">',
                      f' <Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="{REL_MODEL}"/>',
                      '</Relationships>'])
    return types, rels


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stl")
    ap.add_argument("--settings", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--template", help="a Bambu Studio project (.3mf) or its project_settings.config")
    a = ap.parse_args()

    settings = {k: str(v) for k, v in json.loads(Path(a.settings).read_text()).items()
                if not k.startswith("_")}
    verts, faces = read_stl(a.stl)
    # Bambu Studio reads object settings from any 3MF, but only a template brings a printer preset.
    app, project, center = "PrintForge", None, (128.0, 128.0)

    if a.template:
        if a.template.endswith(".3mf"):
            with zipfile.ZipFile(a.template) as z:
                project = json.loads(z.read("Metadata/project_settings.config"))
        else:
            project = json.loads(Path(a.template).read_text())
        app = "BambuStudio-" + project.get("version", "02.08.03.66")
        area = project.get("printable_area")
        if area:
            pts = [tuple(float(c) for c in p.split("x")) for p in area]
            center = (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
        changed = []
        for k, v in settings.items():
            if k in project:
                project[k] = [v] * len(project[k]) if isinstance(project[k], list) else v
                changed.append(k)
        diff = project.get("different_settings_to_system", ["", "", ""])
        diff[0] = ";".join(sorted(set(filter(None, diff[0].split(";"))) | set(changed)))
        project["different_settings_to_system"] = diff

    model, height = model_xml(verts, faces, app, center)
    types, rels = package_files()
    name = Path(a.stl).name
    with zipfile.ZipFile(a.out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", types)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", model)
        z.writestr("Metadata/model_settings.config", settings_xml(name, settings, faces, height, center))
        if project:
            z.writestr("Metadata/project_settings.config", json.dumps(project, indent=4))
    extra = ", printer and filament from the template" if project else ""
    print(f"wrote {a.out}: {len(faces)} triangles, {len(settings)} settings{extra}")


if __name__ == "__main__":
    main()
