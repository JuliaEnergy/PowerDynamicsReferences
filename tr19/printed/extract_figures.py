#!/usr/bin/env python3
"""Extract the curves of the printed figures 3.1 to 3.13 of IEEE PES-TR19 from the PDF.

    python3 -I tr19/printed/extract_figures.py <PDF of the report>

The figures are gnuplot plots embedded as vector graphics. pdftocairo turns a page into SVG, where
each curve is a run of stroked paths with its own dash pattern, drawn in legend order. The tick
labels, read with pdftotext, give the map from path coordinates to data coordinates.

Writes one gzipped CSV per figure next to this script, `fig3.N.csv.gz`. The PDF of the report is
not part of this repository and has to be provided. Needs poppler and the standard library only.
"""

import gzip
import math
import os
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))

# Each figure: number, PDF page, position on the page counted from the top, and the signals in
# legend order. The second entry of a signal is a piece of its legend text, checked on the page.
FIGURES = [
    ("3.1", 39, 0, [("V_1041", "bus 1041"),
                    ("V_1042", "bus 1042"),
                    ("V_4012", "bus 4012"),
                    ("V_4062", "bus 4062")]),
    ("3.2", 40, 0, [("g12", "generator g12"),
                    ("g14", "generator g14"),
                    ("g7", "generator g7"),
                    ("g11", "generator g11"),
                    ("g6", "generator g6"),
                    ("g15", "generator g15"),
                    ("g16", "generator g16")]),
    ("3.3", 40, 1, [("g8", "generator g8"),
                    ("g18", "generator g18"),
                    ("g9", "generator g9")]),
    ("3.4", 41, 0, [("g6", "generator g6"),
                    ("g7", "generator g7")]),
    ("3.5", 42, 0, [("41-4041", "transformer 41-4041"),
                    ("42-4042", "transformer 42-4042"),
                    ("43-4043", "transformer 43-4043"),
                    ("1-1041", "transformer 1-1041"),
                    ("2-1042", "transformer 2-1042"),
                    ("3-1043", "transformer 3-1043")]),
    ("3.6", 42, 1, [("V_1", "voltage magnitude at bus 1"),
                    ("1-1041", "ratio of transformer 1-1041")]),
    ("3.7", 43, 0, [("g6", "generator g6"),
                    ("g7", "generator g7"),
                    ("g17", "generator g17"),
                    ("g20", "generator g20")]),
    ("3.8", 44, 0, [("g6", "generator g6"),
                    ("g7", "generator g7"),
                    ("g17", "generator g17"),
                    ("g20", "generator g20")]),
    ("3.9", 45, 0, [("V_1041", "bus 1041")]),
    ("3.10", 46, 0, [("V_1", "bus 1"),
                     ("V_2", "bus 2"),
                     ("V_3", "bus 3"),
                     ("V_4", "bus 4"),
                     ("V_5", "bus 5")]),
    ("3.11", 46, 1, [("V_1042", "bus 1042"),
                     ("V_1041", "bus 1041"),
                     ("V_1043", "bus 1043"),
                     ("V_1044", "bus 1044"),
                     ("V_1045", "bus 1045")]),
    ("3.12", 47, 0, [("V_2", "bus 2"),
                     ("V_1", "bus 1"),
                     ("V_3", "bus 3"),
                     ("V_4", "bus 4"),
                     ("V_5", "bus 5")]),
    ("3.13", 47, 1, [("V_1042", "bus 1042"),
                     ("V_2", "bus 2")]),
]

CURVE_WIDTH = "2.5"   # grid lines are thinner, border and ticks thicker
BORDER_WIDTH = "5"
GRID_STEP = 0.5       # gnuplot wrote all path coordinates in steps of 0.5


def main():
    with tempfile.TemporaryDirectory() as tmp:
        for page in sorted({f[1] for f in FIGURES}):
            plots, _ = page_plots(page, tmp)
            words = page_words(page, tmp)
            figures = [f for f in FIGURES if f[1] == page]
            assert len(plots) == len(figures), f"{len(plots)} plots on page {page}"
            for name, _, pos, signals in figures:
                fig = extract_figure(plots[pos], words, signals)
                write_csv(os.path.join(HERE, f"fig{name}.csv.gz"), fig, signals)
                npoints = sum(len(p) for c in fig["curves"] for p in c)
                print(f"Fig. {name}: {len(signals)} curves, {npoints} points, "
                      f"ticks off by {fig['xmap'][2]:.2f} (x), {fig['ymap'][2]:.2f} (y) units")


def page_plots(page, tmp):
    """The stroked paths of each plot on a page, top plot first.

    All paths of one plot share the transform of the embedded form. Each path becomes
    (width, dash, subpaths) with the subpaths as point lists in form coordinates.
    """
    svg = os.path.join(tmp, f"p{page}.svg")
    subprocess.run(["pdftocairo", "-svg", "-f", str(page), "-l", str(page), PDF, svg],
                   check=True)
    root = ET.parse(svg).getroot()
    height = float(root.get("viewBox").split()[3])
    groups = {}
    for el in root.iter("{http://www.w3.org/2000/svg}path"):
        style = el.get("style", "")
        if "fill:none" not in style or not el.get("transform", "").startswith("matrix"):
            continue
        width = re.search(r"stroke-width:([\d.]+)", style).group(1)
        dash = re.search(r"stroke-dasharray:([\d.,]+)", style)
        dash = dash.group(1) if dash else ""
        groups.setdefault(el.get("transform"), []).append((width, dash, _subpaths(el.get("d"))))
    plots = []
    for transform, paths in groups.items():
        if any(w == BORDER_WIDTH and _is_closed(sp) for w, _, sps in paths for sp in sps):
            a, b, c, d, e, f = map(float, re.findall(r"-?[\d.]+", transform))
            assert b == 0 and c == 0
            plots.append({"matrix": (a, d, e, f), "paths": paths})
    plots.sort(key=lambda p: p["matrix"][3])
    return plots, height


def _subpaths(d):
    tokens = re.findall(r"[A-Za-z]|-?[\d.]+", d)
    subpaths, i = [], 0
    while i < len(tokens):
        cmd = tokens[i]
        if cmd == "Z":
            subpaths[-1].append(subpaths[-1][0])
            i += 1
            continue
        assert cmd in "ML", f"unexpected path command {cmd}"
        point = (float(tokens[i + 1]), float(tokens[i + 2]))
        if cmd == "M":
            subpaths.append([point])
        else:
            subpaths[-1].append(point)
        i += 3
    return [sp for sp in subpaths if len(sp) > 1]


def _is_closed(sp):
    return len(sp) == 5 and sp[0] == sp[-1]


def page_words(page, tmp):
    """Words on the page as (text, xmin, ymin, xmax, ymax) in points from the top left."""
    html = os.path.join(tmp, f"p{page}.html")
    subprocess.run(["pdftotext", "-bbox", "-f", str(page), "-l", str(page), PDF, html],
                   check=True)
    pattern = r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]*)<'
    return [(m[4], float(m[0]), float(m[1]), float(m[2]), float(m[3]))
            for m in re.findall(pattern, open(html).read())]


def extract_figure(plot, words, signals):
    """Frame, axis maps, legend lines and curves of one plot.

    The axis maps take form coordinates to data. A curve is a list of pieces; a new piece starts
    where gnuplot lifted the pen, e.g. where the curve leaves the frame.
    """
    a, d, e, f = plot["matrix"]
    to_page = lambda x, y: (a * x + e, d * y + f)
    border = next(sp for w, _, sps in plot["paths"] for sp in sps
                  if w == BORDER_WIDTH and _is_closed(sp))
    frame = (min(x for x, _ in border), min(y for _, y in border),
             max(x for x, _ in border), max(y for _, y in border))
    xticks, yticks = _ticks(plot["paths"], frame)
    left, top = to_page(frame[0], frame[3])
    right, bottom = to_page(frame[2], frame[1])
    numbers = [(float(t), x0, y0, x1, y1) for t, x0, y0, x1, y1 in words
               if re.fullmatch(r"-?\d+(\.\d+)?", t)]
    xlabels = [(v, (x0 + x1) / 2) for v, x0, y0, x1, y1 in numbers
               if bottom < y0 < bottom + 15 and left - 10 < x0 < right]
    ylabels = [(v, (y0 + y1) / 2) for v, x0, y0, x1, y1 in numbers
               if left - 30 < x1 < left and top - 5 < y0 < bottom]
    xmap = _axis_map(frame[0], frame[2], [(x, a * x + e) for x in xticks], xlabels)
    ymap = _axis_map(frame[1], frame[3], [(y, d * y + f) for y in yticks], ylabels)
    inside = [w for w in words if left < w[1] and w[3] < right and top < w[2] and w[4] < bottom]

    # gnuplot draws the curves one after the other, each with its legend sample first
    runs = []
    for width, dash, sps in plot["paths"]:
        if width != CURVE_WIDTH:
            continue
        if not runs or runs[-1][0] != dash:
            runs.append((dash, []))
        runs[-1][1].extend(sps)
    assert len(runs) == len(signals), f"{len(runs)} curves for {len(signals)} signals"
    curves, legend = [], []
    for (dash, sps), (_, token) in zip(runs, signals):
        sample, *pieces = _join(sps)
        legend.append(_legend_text(sample, inside, to_page, token))
        curves.append([[(_apply(xmap, x), _apply(ymap, y)) for x, y in p] for p in pieces])
    return {"frame": frame, "matrix": plot["matrix"], "to_page": to_page,
            "xmap": xmap, "ymap": ymap, "curves": curves, "legend": legend}


def _ticks(paths, frame):
    # A tick is a short segment that starts on the left or the bottom side of the frame.
    xticks, yticks = set(), set()
    for width, _, sps in paths:
        for sp in sps:
            if width != BORDER_WIDTH or len(sp) != 2:
                continue
            (x0, y0), (x1, y1) = sp
            if y0 == y1 and abs(x0 - frame[0]) < 0.1:
                yticks.add(y0)
            if x0 == x1 and abs(y0 - frame[1]) < 0.1:
                xticks.add(x0)
    return sorted(xticks), sorted(yticks)


def _axis_map(lo, hi, ticks, labels):
    """Linear map from form coordinates to data on one axis, as (scale, offset, worst tick).

    The frame ends lo and hi are the axis range. Their values come from a straight line through
    the labelled ticks, rounded to the coarsest decimal that stays within one grid step. Every
    labelled tick then has to sit on the map within one grid step too.
    """
    pairs = []
    for value, center in labels:
        coord, page = min(ticks, key=lambda t: abs(t[1] - center))
        assert abs(page - center) < 2, f"no tick for label {value}"
        pairs.append((coord, value))
    assert len(pairs) >= 2
    n = len(pairs)
    mc = sum(c for c, _ in pairs) / n
    mv = sum(v for _, v in pairs) / n
    scale = (sum((c - mc) * (v - mv) for c, v in pairs) /
             sum((c - mc) ** 2 for c, _ in pairs))
    vlo = _round_within(scale * (lo - mc) + mv, GRID_STEP * abs(scale))
    vhi = _round_within(scale * (hi - mc) + mv, GRID_STEP * abs(scale))
    scale = (vhi - vlo) / (hi - lo)
    offset = vlo - scale * lo
    worst = max(abs(scale * c + offset - v) / abs(scale) for c, v in pairs)
    assert worst <= GRID_STEP, f"ticks off the map by {worst} units"
    return (scale, offset, worst)


def _round_within(value, tol):
    digits = 0
    while abs(round(value, digits) - value) > tol:
        digits += 1
    return round(value, digits)


def _apply(axis, coord):
    return axis[0] * coord + axis[1]


def _join(subpaths):
    # The PDF cuts a curve into chunks; a chunk that starts where the previous one ended
    # continues it.
    pieces = []
    for sp in subpaths:
        if pieces and math.dist(pieces[-1][-1], sp[0]) < 0.1:
            pieces[-1].extend(sp[1:])
        else:
            pieces.append(list(sp))
    return pieces


def _legend_text(sample, words, to_page, token):
    """Text of the legend line left of a curve's sample line, checked to name the signal."""
    assert len(sample) == 2 and sample[0][1] == sample[1][1], \
        "first piece of a curve is not a legend sample"
    (x0, y0), (x1, _) = sample
    xs, ys = to_page(min(x0, x1), y0)
    line = sorted((w for w in words if w[3] < xs and abs((w[2] + w[4]) / 2 - ys) < 2),
                  key=lambda w: w[1])
    text = " ".join(w[0] for w in line)
    assert f" {token} " in f" {text} ", f"legend line '{text}' does not name '{token}'"
    return text


def write_csv(path, fig, signals):
    xdig, ydig = _digits(fig["xmap"]), _digits(fig["ymap"])
    rows = ["signal,t,value"]
    for (name, _), curve in zip(signals, fig["curves"]):
        for piece in curve:
            rows += [f"{name},{_fmt(t, xdig)},{_fmt(v, ydig)}" for t, v in piece]
    # mtime=0 keeps the gzip header, and so the file, the same on every run
    with open(path, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as io:
        io.write(("\n".join(rows) + "\n").encode())


def _digits(axis):
    # decimals that resolve one step of the coordinate grid
    return max(0, math.ceil(-math.log10(GRID_STEP * abs(axis[0]))))


def _fmt(value, digits):
    s = f"{value:.{digits}f}"
    return s[1:] if re.fullmatch(r"-0\.?0*", s) else s


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python3 -I extract_figures.py <PDF of IEEE PES-TR19>")
    PDF = sys.argv[1]
    main()
