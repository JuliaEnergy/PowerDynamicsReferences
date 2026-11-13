#!/usr/bin/env python3
"""Run one Dynawo case and write its outputs into the case folder.

    DYNAWO_DIR=/path/to/dynawo python3 dynawo/run_case.py <case>

The case folder holds one .jobs file and the inputs it names. Dynawo runs on a copy of the folder
in a scratch directory. Only when the run succeeded are curves.csv.gz, timeline.csv and meta.toml
replaced in the case folder. On failure the scratch directory is kept for inspection.
Only the standard library is used.
"""

import gzip
import hashlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
NS = {"dyn": "http://www.rte-france.com/dynawo"}


def main(argv):
    if len(argv) != 2:
        sys.exit(__doc__)
    dynawo_dir = os.environ.get("DYNAWO_DIR")
    if not dynawo_dir:
        sys.exit("Set DYNAWO_DIR to the Dynawo distribution (the folder with dynawo.sh).")
    launcher = os.path.join(dynawo_dir, "dynawo.sh")
    if not os.path.isfile(launcher):
        sys.exit(f"No dynawo.sh in DYNAWO_DIR={dynawo_dir}.")
    case_dir = os.path.join(HERE, argv[1])
    if not os.path.isdir(case_dir):
        sys.exit(f"No case folder {case_dir}.")
    jobs = [f for f in os.listdir(case_dir) if f.endswith(".jobs")]
    if len(jobs) != 1:
        sys.exit(f"Expected exactly one .jobs file in {case_dir}, found {jobs}.")
    outdir, dyd, has_timeline = read_jobs(os.path.join(case_dir, jobs[0]))
    version = subprocess.run([launcher, "version"], capture_output=True, text=True)
    if version.returncode != 0:
        sys.exit(f"`dynawo.sh version` failed:\n{version.stdout}{version.stderr}")

    work = tempfile.mkdtemp(prefix="dynawo_case_")
    shutil.copytree(case_dir, work, dirs_exist_ok=True)
    with open(os.path.join(work, "console.log"), "w") as log:
        rc = subprocess.run([launcher, "jobs", os.path.join(work, jobs[0])],
                            stdout=log, stderr=subprocess.STDOUT).returncode
    console = open(os.path.join(work, "console.log")).read()
    if rc != 0 or "succeeded" not in console:
        print("\n".join(console.splitlines()[-20:]), file=sys.stderr)
        sys.exit(f"Dynawo failed. Scratch directory kept: {work}\n"
                 f"Log: {os.path.join(work, outdir, 'logs', 'dynawo.log')}")

    out = os.path.join(work, outdir)
    files = {"curves.csv.gz": curves(os.path.join(out, "curves", "curves.csv")),
             "meta.toml": meta(version.stdout.strip(), dynawo_dir, case_dir, dyd)}
    if has_timeline:
        files["timeline.csv"] = timeline(os.path.join(out, "timeLine", "timeline.csv"))
    elif os.path.exists(os.path.join(case_dir, "timeline.csv")):
        os.remove(os.path.join(case_dir, "timeline.csv"))
    for name, data in files.items():
        with open(os.path.join(case_dir, name), "wb") as f:
            f.write(data)
    shutil.rmtree(work)
    print(f"wrote {', '.join(files)} to {case_dir}")


def read_jobs(path):
    """Output directory, .dyd file and whether a timeline is exported. Curves must be exported
    as CSV, a timeline as CSV or not at all."""
    job = ET.parse(path).getroot().find("dyn:job", NS)
    outputs = job.find("dyn:outputs", NS)
    crv = outputs.find("dyn:curves", NS)
    if crv is None or crv.get("exportMode") != "CSV":
        sys.exit(f"{path}: the driver needs <curves exportMode=\"CSV\"/>.")
    tl = outputs.find("dyn:timeline", NS)
    if tl is not None and tl.get("exportMode") != "CSV":
        sys.exit(f"{path}: the driver handles only a CSV timeline, "
                 f"not exportMode=\"{tl.get('exportMode')}\".")
    dyd = job.find("dyn:modeler/dyn:dynModels", NS).get("dydFile")
    return outputs.get("directory"), dyd, tl is not None


def curves(src):
    """Dynawo's `;`-separated export without the trailing `;`, values with 9 significant
    digits. The time column is kept as Dynawo printed it."""
    with open(src) as f:
        lines = [ln.rstrip("\n").rstrip(";") for ln in f if ln.strip()]
    rows = [lines[0]]
    for ln in lines[1:]:
        t, *vals = ln.split(";")
        rows.append(";".join([t] + ["%.9g" % float(v) for v in vals]))
    # mtime=0 keeps the file byte-identical when the data does not change
    buf = io.BytesIO()
    with gzip.GzipFile("curves.csv", "wb", fileobj=buf, mtime=0) as gz:
        gz.write(("\n".join(rows) + "\n").encode())
    return buf.getvalue()


def timeline(src):
    with open(src) as f:
        lines = [ln.rstrip("\n").rstrip(";") for ln in f if ln.strip()]
    return ("time;model;event\n" + "".join(ln + "\n" for ln in lines)).encode()


def meta(version, dynawo_dir, case_dir, dyd):
    """Dynawo version and the sha256 of each compiled model the case ran."""
    root = ET.parse(os.path.join(case_dir, dyd)).getroot()
    libs = sorted({bb.get("lib") for bb in root.findall("dyn:blackBoxModel", NS)})
    out = [f'dynawo_version = "{version}"', "", "[lib_sha256]"]
    for lib in libs:
        so = os.path.join(dynawo_dir, "ddb", lib + ".so")
        sha = hashlib.sha256(open(so, "rb").read()).hexdigest() if os.path.isfile(so) else "none"
        out.append(f'{lib} = "{sha}"')
    return ("\n".join(out) + "\n").encode()


if __name__ == "__main__":
    main(sys.argv)
