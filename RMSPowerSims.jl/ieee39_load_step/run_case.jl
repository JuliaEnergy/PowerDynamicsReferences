# Regenerates bus30.csv.gz … bus39.csv.gz. Run from the repository root:
#
#     julia --project=RMSPowerSims.jl -e 'using Pkg; Pkg.instantiate()'
#     julia --project=RMSPowerSims.jl RMSPowerSims.jl/ieee39_load_step/run_case.jl

using RMSPowerSims, DataFrames, CSV
using RMSPowerSims.Sundials: BrownFullBasicInit

net = parse_network_json(joinpath(@__DIR__, "ieee39.json"))
simulation = prepare_simulation(net)

# load 16 sits at index 9 in the PowerModels data and steps up by 20 % at t = 1 s
simulation.disturbances = Disturbance[
    LoadStep(9, 1, 0.2 * net["load"]["9"]["pd"]),
]

soln = run_RMS_simulation(
    simulation,
    (0.0, 15.0);
    reltol = 1e-9,
    abstol = 1e-8,
    maxiters = 10000,
    dtmax = 0.01,
    # the u0/du0 from RMSPowerSims are not consistent enough for the strict default CheckInit
    initializealg = BrownFullBasicInit(),
)
add_simulation_results!(net, soln)

# One file per generator bus: the bus states followed by those of the load and generator there.
for i in 30:39
    df = DataFrame(t = net["t_vec"])
    components = [net["bus"][string(i)]]
    append!(components, [l for l in values(net["load"]) if l["load_bus"] == i])
    append!(components, [g for g in values(net["gen"]) if g["gen_bus"] == i])
    for comp in components, (sym, vals) in comp["sol"]
        df[!, sym] = vals
    end

    file = joinpath(@__DIR__, "bus$i.csv")
    CSV.write(file, df)
    run(`gzip -nf $file`)
end
