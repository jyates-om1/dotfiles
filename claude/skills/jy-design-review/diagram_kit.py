"""Emit Claude Docs diagram modules that pass the widget validator.

Every <text> gets a literal data-claude-text-id and literal words, so the
generated module is safe even though this script loops. Print the result with
json.dumps and paste it as the widget's "code".

    from diagram_kit import bands, markers
    code = bands("Title as a finding", [
        {"id": "launch", "head": "Launch · per click", "boxes": [
            ("epic", "Epic opens app", "iss + launch", "inside a frame"),
            ("edge", "CloudFront edge", "frame-ancestors", "per customer", True),  # True = accent
        ]},
    ], key="Highlighted: the open decision.")
"""
import json

XS4 = [40, 218, 396, 574]  # four 154-wide boxes, gap 24
INK, QUIET = "ink", "quiet"

HEAD = ("const edge = 'var(--cds-chart-axis)', accent = 'var(--cds-chart-categorical-1)', "
        "ink = 'var(--cds-text-primary)', quiet = 'var(--cds-text-secondary)', "
        "tint = 'var(--cds-chart-reference-tint)', crit = 'var(--cds-chart-status-critical)'; "
        "const box = (x, y, w, h, main) => <rect x={x} y={y} width={w} height={h} rx='8' fill={main ? accent : 'none'} "
        "fillOpacity={main ? 0.12 : 1} stroke={main ? accent : edge} strokeWidth={main ? 2 : 1.25}/>; "
        "const band = (x, y, w, h) => <rect x={x} y={y} width={w} height={h} rx='8' fill={tint} stroke={edge} strokeWidth='1'/>; "
        "const mark = (cx, cy) => <circle cx={cx} cy={cy} r='10' fill={crit} fillOpacity='0.15' stroke={crit} strokeWidth='1.5'/>; ")


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(tid, x, y, words, size=None, weight=None, fill=INK, anchor=None):
    a = f"<text data-claude-text-id='{tid}' x='{x}' y='{y}'"
    if anchor:
        a += f" textAnchor='{anchor}'"
    if size:
        a += f" fontSize='{size}'"
    if weight:
        a += f" fontWeight='{weight}'"
    return a + f" fill={{{fill}}}>{esc(words)}</text>"


def box(bid, x, y, name, l1, l2, main=False, w=154):
    """A named box with two body lines; 72 tall. Name ≤ 17 chars, lines ≤ 21 chars at w=154."""
    return (f"<g data-claude-anchor='{bid}'>{{box({x}, {y}, {w}, 72, {'true' if main else 'false'})}}"
            + text(bid, x + 12, y + 24, name, weight="600")
            + text(bid + "-1", x + 12, y + 44, l1, size="11.5", fill=QUIET)
            + text(bid + "-2", x + 12, y + 60, l2, size="11.5", fill=QUIET) + "</g>")


def _wrap(title, height, body, marker_id):
    svg = (f"<svg viewBox='0 0 760 {height}' role='img' aria-label='{esc(title)}' fontSize='13'>"
           f"<defs><marker id='{marker_id}' viewBox='0 0 10 10' refX='9' refY='5' markerWidth='6' markerHeight='6' "
           f"orient='auto-start-reverse'><path d='M0 0L10 5L0 10z' fill={{edge}}/></marker></defs>"
           + text("title", 24, 34, title, size="15", weight="600") + body + "</svg>")
    return "export default () => { " + HEAD + "return " + svg + "; };"


def bands(title, band_list, key=None, extra_paths=(), extra_texts=()):
    """Pattern A. Each band: {"id", "head", "boxes": [(id, name, l1, l2[, main])]} with up to 4 boxes.
    Bands are 128 tall with a 24 gap. extra_paths are raw <path d=...> strings (e.g. dashed elbows
    between bands, run along the gap); extra_texts are (id, x, y, words) quiet labels."""
    body, conn, y0 = [], [], 56
    for b in band_list:
        body.append(f"<g data-claude-anchor='band-{b['id']}'>{{band(24, {y0}, 712, 128)}}"
                    + text(f"{b['id']}-head", 40, y0 + 24, b["head"], weight="600") + "</g>")
        by = y0 + 40
        xs = XS4[:len(b["boxes"])]
        for spec, x in zip(b["boxes"], xs):
            bid, name, l1, l2, *rest = spec
            body.append(box(bid, x, by, name, l1, l2, main=bool(rest and rest[0])))
        for a, c in zip(xs, xs[1:]):
            conn.append(f"<path d='M{a + 154} {by + 36}H{c}' markerEnd='url(#shape-arrow)'/>")
        y0 += 152
    conn += list(extra_paths)
    body.append("<g data-claude-anchor='connectors' fill='none' stroke={edge} strokeWidth='1.25'>" + "".join(conn) + "</g>")
    for tid, x, y, words in extra_texts:
        body.append(text(tid, x, y, words, size="11.5", fill=QUIET))
    height = y0 + 16
    if key:
        body.append(text("key", 24, y0 - 8, key, size="11.5", fill=QUIET))
        height += 8
    return _wrap(title, height, "".join(body), "shape-arrow")


def markers(title, boxes, marks, footer_box=None, key="Each red marker is a cost of this option; the numbers match the list below."):
    """Pattern B. boxes: up to 4 (id, name, l1, l2) in a row at y=72; footer_box: (id, words) full-width
    48-tall box at y=184 joined by dashed lines to boxes 2 and 4; marks: [(n, cx, cy)] placed on box corners
    (top-right corner of box i = (XS4[i] + 154 - 2, 76); bottom-right = (XS4[i] + 154 - 2, 140))."""
    body, conn = [], []
    xs = XS4[:len(boxes)]
    for (bid, name, l1, l2), x in zip(boxes, xs):
        body.append(box(bid, x, 72, name, l1, l2))
    for a, c in zip(xs, xs[1:]):
        conn.append(f"<path d='M{a + 154} 108H{c}' markerEnd='url(#alt-arrow)'/>")
    height = 184
    if footer_box:
        fid, words = footer_box
        body.append(f"<g data-claude-anchor='{fid}'>{{box(40, 184, 688, 48, false)}}" + text(fid, 56, 213, words, size="11.5") + "</g>")
        conn += ["<path d='M295 144V184' strokeDasharray='4 3'/>", "<path d='M651 144V184' strokeDasharray='4 3'/>"]
        height = 248
    body.append("<g data-claude-anchor='connectors' fill='none' stroke={edge} strokeWidth='1.25'>" + "".join(conn) + "</g>")
    for n, cx, cy in marks:
        body.append(f"<g data-claude-anchor='mark-{n}'>{{mark({cx}, {cy})}}"
                    + text(f"mark-{n}-n", cx, cy + 4, str(n), size="11.5", weight="600", anchor="middle") + "</g>")
    body.append(text("key", 24, height + 12, key, size="11.5", fill=QUIET))
    return _wrap(title, height + 24, "".join(body), "alt-arrow")


if __name__ == "__main__":
    print(json.dumps(bands("Example: one band", [{"id": "a", "head": "Band · what it is", "boxes": [
        ("one", "First", "line one", "line two"), ("two", "Second", "line one", "line two", True)]}],
        key="Highlighted: the open decision.")))
