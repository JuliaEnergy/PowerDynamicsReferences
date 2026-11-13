# PowerDynamicsReferences

[![check-export](https://github.com/JuliaEnergy/PowerDynamicsReferences/actions/workflows/check-export.yml/badge.svg?branch=main)](https://github.com/JuliaEnergy/PowerDynamicsReferences/actions/workflows/check-export.yml)

Reference simulations for the validation tests of
[PowerDynamics.jl](https://github.com/JuliaEnergy/PowerDynamics.jl). The tests name a commit of
this repository and download it; nobody who only uses PowerDynamics needs it.

| Folder | What | How it is produced |
| --- | --- | --- |
| `openipsl/` | OpenIPSL models, one SMIB case per model | `ref_data_gen.sh` in each case, OpenModelica |
| `dynawo/` | Dynawo cases | `run_case.py`, see `dynawo/README.md` |
| `RMSPowerSims.jl/` | IEEE 39-bus load step from RMSPowerSims.jl | `run_case.jl` in the case, see `RMSPowerSims.jl/README.md` |
| `tr19/` | Nordic test system of IEEE PES-TR19 | published by the report authors, see `tr19/README.md` |
| `external/` | PowerFactory results | exported from a private repository, see below |

Everything except `external/` is edited here directly, and pull requests are welcome.

## external/

The PowerFactory projects cannot be published, so their results come from an export out of a
private repository. The export cuts each result down to the signals the tests read, and writes
`external/EXPORT.toml` with the private commit it came from and a checksum of every file. A check
on GitHub (`check-export`, runs locally too) only accepts an export from a committed and pushed
state whose files match those checksums. Nobody edits `external/` by hand.
