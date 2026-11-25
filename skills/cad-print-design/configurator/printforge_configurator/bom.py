"""Read a bill of materials from the `BOM.md` that lies beside a model, for the BOM view of the configurator.

The file is plain Markdown in one fixed shape, so a person can read it on GitHub and the page can show it as tables:

    # Title
    One or more paragraphs about the whole list.

    ## Section
    | | Part | Qty | Size | Note |
    | --- | --- | --- | --- | --- |
    | ![](bom/part.png) | Name of the part | 4 | 30 × 20 mm | Free text with a [link](https://example.com). |

    ## Not in the list
    A section may also be plain text, without a table.

The rules:

- One `#` title, then one `##` heading for each section. A section holds text, one table, or both.
- A column without a name holds the picture of the part. The path is relative to the folder of `BOM.md`.
- `Part` names the part and `Qty` is a whole number. Any other columns are free, but keep them the same in every table.
- A cell may hold text, `code`, **bold**, a link and a picture, written as Markdown or as `<a href>` and `<img src>`.

`parse` returns the list as plain data and names what does not follow the rules in `problems`.
"""

import html
import re
from pathlib import Path

NAMES = ("BOM.md", "bom.md", "Bom.md")
PICTURES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".gif": "image/gif"}
INLINE = re.compile(
    r"""<img\b[^>]*?\bsrc=["'](?P<src>[^"']+)["'][^>]*>"""
    r"""|!\[(?P<alt>[^\]]*)\]\((?P<msrc>[^)\s]+)\)"""
    r"""|<a\b[^>]*?\bhref=["'](?P<href>[^"']+)["'][^>]*>(?P<atext>.*?)</a>"""
    r"""|\[(?P<mtext>[^\]]+)\]\((?P<mhref>[^)\s]+)\)"""
    r"""|`(?P<code>[^`]+)`|<code>(?P<hcode>.*?)</code>"""
    r"""|\*\*(?P<bold>[^*]+)\*\*""",
    re.S,
)


def find(model):
    """The BOM.md beside a model file, or None."""
    for name in NAMES:
        path = Path(model).parent / name
        if path.is_file():
            return path
    return None


def plain(text):
    """Text without tags and with its entities resolved."""
    return html.unescape(re.sub(r"<[^>]+>", "", text))


def inline(text):
    """One cell or paragraph as a list of pieces: text, code, bold, link and image."""
    pieces, at = [], 0

    def add(kind, **fields):
        if kind == "text" and not fields["text"]:
            return
        pieces.append({"kind": kind, **fields})

    for m in INLINE.finditer(text):
        add("text", text=plain(text[at:m.start()]))
        at = m.end()
        if m["src"] or m["msrc"]:
            add("image", src=html.unescape(m["src"] or m["msrc"]), alt=m["alt"] or "")
        elif m["href"] or m["mhref"]:
            url = html.unescape(m["href"] or m["mhref"])
            label = plain(m["atext"] if m["href"] else m["mtext"])
            if url.startswith(("http://", "https://", "mailto:")):
                add("link", text=label, url=url)
            else:                                   # Never hand the page a script or a local address to open.
                add("text", text=label)
        elif m["code"] or m["hcode"]:
            add("code", text=plain(m["code"] or m["hcode"]))
        else:
            add("bold", text=plain(m["bold"]))
    add("text", text=plain(text[at:]))
    return pieces


def cells(line):
    """The cells of one table row. A pipe inside a cell is written as a backslash and a pipe."""
    row = re.split(r"(?<!\\)\|", line.strip())
    if row and not row[0].strip():
        row = row[1:]
    if row and not row[-1].strip():
        row = row[:-1]
    return [c.strip().replace("\\|", "|") for c in row]


def text_of(pieces):
    return "".join(p.get("text", "") for p in pieces).strip()


def parse(text):
    """The list as plain data: title, lead paragraphs, sections with columns and rows, totals and problems."""
    title, lead, sections, problems = "", [], [], []
    section, para = None, []

    def flush():
        if para:
            (section["text"] if section else lead).append(inline(" ".join(para)))
            para.clear()

    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        i += 1
        if line.startswith("# ") and not title:
            flush()
            title = plain(line[2:].strip())
        elif line.startswith("## "):
            flush()
            section = {"heading": plain(line[3:].strip()), "text": [], "columns": [], "rows": []}
            sections.append(section)
        elif line.lstrip().startswith("|") and i < len(lines) and re.fullmatch(r"\s*\|?[\s:|-]+\|?\s*", lines[i]) and "-" in lines[i]:
            flush()
            if section is None:
                section = {"heading": "", "text": [], "columns": [], "rows": []}
                sections.append(section)
            if section["columns"]:
                problems.append(f"{section['heading'] or 'the list'}: more than one table, the rows are joined")
            columns = cells(line)
            section["columns"] = section["columns"] or columns
            i += 1
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                row = cells(lines[i])
                row += [""] * (len(columns) - len(row))
                section["rows"].append([inline(c) for c in row[:len(section["columns"])]])
                i += 1
        elif not line.strip():
            flush()
        else:
            para.append(line.strip())
    flush()

    if not title:
        problems.append("no # title")
    parts = pieces = 0
    for s in sections:
        if not s["columns"]:
            continue
        names = [c.lower() for c in s["columns"]]
        s["picture"] = names.index("") if "" in names else None
        s["part"] = names.index("part") if "part" in names else None
        s["qty"] = names.index("qty") if "qty" in names else None
        if s["part"] is None or s["qty"] is None:
            problems.append(f"{s['heading']}: the table needs a Part and a Qty column")
            continue
        total = 0
        for row in s["rows"]:
            value = text_of(row[s["qty"]])
            if re.fullmatch(r"\d+", value):
                total += int(value)
            else:
                problems.append(f"{s['heading']}: Qty of {text_of(row[s['part']]) or 'a row'} is not a whole number")
        s["pieces"] = total
        parts += len(s["rows"])
        pieces += total
    return {"title": title, "lead": lead, "sections": sections, "parts": parts, "pieces": pieces, "problems": problems}


def read(model):
    """The parsed BOM.md of a model, with its picture addresses made relative to the server, or None without a file."""
    path = find(model)
    if path is None:
        return None
    data = parse(path.read_text(encoding="utf-8"))

    def fix(pieces):
        for p in pieces:
            if p["kind"] == "image" and not p["src"].startswith(("http://", "https://")):
                p["src"] = "/api/bom/file/" + p["src"].lstrip("./")

    for block in data["lead"]:
        fix(block)
    for s in data["sections"]:
        for block in s["text"]:
            fix(block)
        for row in s["rows"]:
            for cell in row:
                fix(cell)
    data["file"] = path.name
    data["stale"] = path.stat().st_mtime < Path(model).stat().st_mtime
    return data


def picture(model, name):
    """The bytes and type of a picture of the list. Only pictures inside the folder of the model are served."""
    root = Path(model).parent.resolve()
    path = (root / name).resolve()
    kind = PICTURES.get(path.suffix.lower())
    if kind is None or root not in path.parents or not path.is_file():
        return None, None
    return path.read_bytes(), kind
