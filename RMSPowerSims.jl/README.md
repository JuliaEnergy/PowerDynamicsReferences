# RMSPowerSims.jl cases

Reference simulations from [RMSPowerSims.jl](https://github.com/tphilpott2/RMSPowerSims.jl) at
commit `376f25a`, pinned in `Project.toml`. The package is not registered, so the project pulls it
straight from GitHub.

## ieee39_load_step

The IEEE 39-bus system from the RMSPowerSims examples (`ieee39.json`, PowerModels data extended by
the dynamic models, 100 MVA, 60 Hz). The file is copied unchanged from
`data/example_test_systems/` of the package, see `LICENSE`. The PowerDynamics test builds its model
from it as well.

Ten machines, all but the one at bus 39 with AVR and governor. Load 16 steps up by 20 % of its
active power at t = 1 s, simulated until t = 15 s.

`bus30.csv.gz` … `bus39.csv.gz` hold one file per generator bus: a `t` column, then the states of
the bus (`V`, `θ`), of a load at that bus and of the generator with its controllers, under the
RMSPowerSims names.

To regenerate:

```sh
julia --project=RMSPowerSims.jl -e 'using Pkg; Pkg.instantiate()'
julia --project=RMSPowerSims.jl RMSPowerSims.jl/ieee39_load_step/run_case.jl
```
