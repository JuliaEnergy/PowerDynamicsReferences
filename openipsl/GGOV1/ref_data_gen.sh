#!/bin/bash

# Get script directory
SCRIPTDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Set temporary directory
TMPDIR="/tmp/ggov1_sim"

# Create temporary directory
mkdir -p "$TMPDIR" && cd "$TMPDIR"

# Remove existing OpenIPSL directory if it exists
rm -rf OpenIPSL

# Clone OpenIPSL at specific commit for reproducibility
git clone --depth 1 https://github.com/OpenIPSL/OpenIPSL.git
cd OpenIPSL
git fetch --depth 1 origin fe8aa5c
git checkout fe8aa5c
cd ..

# Set OpenIPSL library path
export OPENIPSL_PATH="$TMPDIR/OpenIPSL/OpenIPSL"

# First run: OpenIPSL as it is, with the engine dead time Teng as a true fixed delay
omc "$SCRIPTDIR/model_simulation.mos"
mv modelica_results.csv modelica_results_truedelay.csv

# Second run: the Pade delay (n = m = 2) instead. OpenIPSL builds it with a delay time of C.eps,
# so it also gets Teng.
TG="$OPENIPSL_PATH/Electrical/Controls/PSSE/TG"
sed -i 's/delayTime=C.eps,/delayTime=Teng,/' "$TG/BaseClasses/GGOV1/Turbine.mo"
sed -i 's/DelayType delay=Types.DelayType.FixedDelay/DelayType delay=Types.DelayType.PadeDelay/' "$TG/GGOV1.mo"
omc "$SCRIPTDIR/model_simulation.mos"

# Copy results back, compress, and cleanup
for f in modelica_results.csv modelica_results_truedelay.csv; do
    cp "$f" "$SCRIPTDIR/" || { echo "Error: Failed to copy $f"; exit 1; }
    rm -f "$SCRIPTDIR/$f.gz"
    gzip "$SCRIPTDIR/$f"
done

rm -rf "$TMPDIR"
