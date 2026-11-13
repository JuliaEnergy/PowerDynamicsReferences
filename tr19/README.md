# TR19 cases

Data of the Nordic test system of IEEE PES-TR19, published by the report authors. Downloaded
2026-10-26 from the IEEE PES Power System Dynamic Performance Committee page
https://cmte.ieee.org/pes-psdp/489-2/, which links the archives on Google Drive. The files are as
published, the curves gzipped.

| Archive (link text on the page) | sha256 | Files here |
| --- | --- | --- |
| `Nordic_ramses_dat.zip` ("Input data for RAMSES") | `bfa98173…cd641d1e` | `ramses/` except `lf_*.dat` |
| `Nordic_resultsaA.zip` ("Sample output results in ASCII format") | `26c84c32…cf7836` | `A_line_trip/*.cur.gz` |

`ramses/lf_A.dat` and `ramses/lf_B.dat` are the power flow inputs with the explicit loads and
generation. They come from `Nordic.zip` (sha256 `d045df3e…b8a03c12f23e`) on Van Cutsem's software
page, https://thierryvancutsem.github.io/home/software.html, downloaded the same day. The other
files of that zip are a later variant with restorative loads and are not used.

## ramses

RAMSES input of both operating points: `dyn_A.dat`, `dyn_B.dat` (network and dynamic models),
`volt_rat_A.dat`, `volt_rat_B.dat` (power flow voltages and transformer ratios), `lf_A.dat`,
`lf_B.dat`, and the run of `A_line_trip`: `sim.cfg`, `settings1.dat`, `short_trip_branch.dst`.

## A_line_trip

Operating point A, solid fault at bus 4032 at t = 1.0 s, cleared at 1.1 s by opening line
4032-4044 (TR19 §3.1). RAMSES output in 10 ms steps with 7 digits, which ends at 163.9 s, just
after the collapse. Each row is `t`, the signals and a `;`, without header. The last row is
repeated.

| File | Columns after `t` | TR19 |
| --- | --- | --- |
| `volt_fig3.1.cur.gz` | voltage at 1041, 1042, 4012, 4062 [pu] | Fig. 3.1 |
| `ifd_fig3.2.cur.gz` | field current of g12, g14, g7, g11, g6, g15, g16 [pu] | Fig. 3.2 |
| `ifd_fig3.3.cur.gz` | field current of g8, g18, g9 [pu] | Fig. 3.3 |
| `ifd_g5.cur.gz` | field current of g5 [pu] | none |

The field currents are on the base of TR19 §2.4, 1 pu at no load and rated voltage on the air-gap
line.

## printed

The curves of TR19 Figs. 3.1 to 3.13, read off the PDF of the report (PDF pages 39 to 47). The figures are gnuplot plots embedded as vector graphics, so the curves come straight from
the drawn paths, and the axes from the plot frame and the tick labels. `extract_figures.py`
writes the gzipped CSVs. It needs poppler and the PDF, which is not part of this repository:
`python3 -I tr19/printed/extract_figures.py <PDF of the report>`.

Each CSV has the columns `signal,t,value` with t in s. The points are kept as drawn, in drawing
order, and rounded to the coordinate grid of the PDF, about 0.03 s and 1/4400 of the y range.
Where a curve leaves the frame it is cut on the frame line and continues where it comes back,
as during the fault in Figs. 3.1, 3.6, 3.9 and 3.10 or for V_1 after 139 s.

Figs. 3.1 to 3.8 show operating point A with the line trip of `A_line_trip`. Figs. 3.9 and 3.10
show operating point B with the same disturbance, Figs. 3.11 to 3.13 point B with the outage of
g6, in Fig. 3.13 followed by two 80 Mvar shunts switched in at bus 1042.

| File | Signals | TR19 |
| --- | --- | --- |
| `fig3.1.csv.gz` | `V_1041`, `V_1042`, `V_4012`, `V_4062`: voltage at these buses [pu] | Fig. 3.1 |
| `fig3.2.csv.gz` | `g12`, `g14`, `g7`, `g11`, `g6`, `g15`, `g16`: field current [pu] | Fig. 3.2 |
| `fig3.3.csv.gz` | `g8`, `g18`, `g9`: field current [pu] | Fig. 3.3 |
| `fig3.4.csv.gz` | `g6`, `g7`: terminal voltage [pu] | Fig. 3.4 |
| `fig3.5.csv.gz` | `41-4041`, `42-4042`, `43-4043`, `1-1041`, `2-1042`, `3-1043`: transformer ratio [pu] | Fig. 3.5 |
| `fig3.6.csv.gz` | `V_1`: voltage at distribution bus 1 [pu], `1-1041`: ratio of its transformer [pu] | Fig. 3.6 |
| `fig3.7.csv.gz` | `g6`, `g7`, `g17`, `g20`: rotor speed deviation [pu] | Fig. 3.7 |
| `fig3.8.csv.gz` | `g6`, `g7`, `g17`, `g20`: rotor angle with respect to the COI [deg] | Fig. 3.8 |
| `fig3.9.csv.gz` | `V_1041`: voltage at this bus [pu] | Fig. 3.9 |
| `fig3.10.csv.gz` | `V_1`, `V_2`, `V_3`, `V_4`, `V_5`: voltage at these distribution buses [pu] | Fig. 3.10 |
| `fig3.11.csv.gz` | `V_1042`, `V_1041`, `V_1043`, `V_1044`, `V_1045`: voltage at these buses [pu] | Fig. 3.11 |
| `fig3.12.csv.gz` | `V_2`, `V_1`, `V_3`, `V_4`, `V_5`: voltage at these distribution buses [pu] | Fig. 3.12 |
| `fig3.13.csv.gz` | `V_1042`, `V_2`: voltage at these buses [pu] | Fig. 3.13 |

Up to about 100 s, the printed Figs. 3.1 to 3.3 show the same run as `A_line_trip`. Between 2 and
100 s the extracted curves differ from it by 0.0003 to 0.001 pu RMS for the voltages and 0.002 to
0.008 pu for the field currents, with no offset in time or value. The rest are small differences
between the two runs, in the phase of the swings and around the limiter takeovers.
