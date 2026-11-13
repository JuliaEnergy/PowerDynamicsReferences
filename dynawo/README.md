# Dynawo cases

Reference simulations from [Dynawo](https://dynawo.github.io) v1.7.0, the precompiled release
https://github.com/dynawo/dynawo/releases/download/v1.7.0/Dynawo_Linux_gcc11_v1.7.0.zip
with sha256 `dfafc3eb3625d0f30f31748dfc7145c8fca22f544d5df4cf546ada3d6bc10c5f`. Unpack it and point
`DYNAWO_DIR` at the folder that holds `dynawo.sh`.

## Running a case

```sh
DYNAWO_DIR=/path/to/dynawo python3 dynawo/run_case.py OLTCTransformer_2bus
```

The driver needs only Python 3. It runs Dynawo on a copy of the case folder and replaces the
outputs only when the run succeeded. On failure it keeps the scratch directory and prints its path.

## What a case holds

A case folder is self-contained: one `.jobs` file and every input it names (`.dyd`, `.par`,
`.crv`, a network file if there is one). The `.jobs` file exports the curves as CSV, and the
timeline as CSV or not at all. The driver adds:

- `curves.csv.gz`: the curve export, `;`-separated, a `time` column and one column per curve
  named `<model id>_<variable>`. Values have 9 significant digits. At an event there are two rows
  with the same time, before and after it.
- `timeline.csv`: the timeline, columns `time;model;event`.
- `meta.toml`: the Dynawo version and the sha256 of each compiled model the case ran.

Cases set `precision="1e-9"` on the job's `simulation`, and the tests rely on it. It is the number
of decimals in the outputs and Dynawo's tolerance for event comparisons (default 1e-6). Event
times then come out a few ns early instead of a few µs.

## Adding a case

Make a new folder and copy a template or an existing case into it. Write its `.jobs`, `.dyd`,
`.par` and `.crv` files and run the driver. The test reads the curves with `read_dynawo_curves`
and a `SignalMap`.

Inputs copied from Dynawo's `examples` or `nrt` keep their MPL-2.0 header and get one line naming
the source file. Hand-written inputs need no header.

## OLTCTransformer_2bus

A stiff source feeds a voltage dependent load through a transformer with a tap changer, all in pu
on 100 MVA. The transformer has X = 0.1 and 17 taps with ratio 0.92 + 0.01·tap, starting at tap 9.
The load draws P = 0.5·(U/U₀) and Q = 0.1·(U/U₀)². The tap changer holds the load bus at
1 ± 0.01, with the first tap after 20 s and further taps every 10 s. The source steps from 1 to
0.92 at t = 10 s and back at t = 120 s. Before the return, the taps reach their upper limit.
