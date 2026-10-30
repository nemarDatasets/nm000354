"""Add the per-trial columns of the source table D.stimuliValues to events.tsv (fix-20261030).

Source: sourcedata/zenodo-19550714/raw_data/trials_P<k>.mat (Zenodo 10.5281/zenodo.19550714, MATLAB v7.3).
D.stimuliValues is a MATLAB `table` (MCOS object) with one row per trial, in the order of the third dimension of
D.trials; the events.tsv rows (trial-001 ... trial-NNN) follow the same order. The table is decoded with mat-io
(https://github.com/foreverallama/matio, 1.0.0); this table version has no props.versionSavedFrom, so its raw
properties are converted with matio's `to_dataframe`.

Usage:
  python fix-20261030_stimuliValues_to_events.py <bids_root> --mat <dir with trials_P*.mat>
  python fix-20261030_stimuliValues_to_events.py <bids_root> --tsv <dir with nm000354_P<k>_stimuliValues.tsv>
The second form reads the tables already extracted by the first step (same decoder, written with pandas.to_csv).
Columns added verbatim (names as in the source): N1, N2, N3, O1, O2, RT, stimType. Nothing else changes.
"""
import argparse
import ast
import csv
import glob
import math
import os

COLS = ["N1", "N2", "N3", "O1", "O2", "RT", "stimType"]


def from_mat(path):
    import numpy as np
    from matio import load_from_mat
    from matio.utils.matclass import MatlabOpaque
    from matio.utils.converters.mattables import to_dataframe

    t = load_from_mat(path, variable_names=["D"])["D"]["stimuliValues"]
    if isinstance(t, np.ndarray) and t.dtype == object and t.size == 1:
        t = t.item()
    if isinstance(t, MatlabOpaque):
        p = t.properties
        t = to_dataframe(p["data"], int(np.ravel(p["nvars"])[0]), p["varnames"])
    return [{c: t[c].iloc[i] for c in COLS} for i in range(len(t))]


def from_tsv(path):
    return list(csv.DictReader(open(path), delimiter="\t"))


def fmt(col, v):
    if isinstance(v, str) and v.startswith("["):
        v = ast.literal_eval(v)
    if isinstance(v, (list, tuple)):
        assert len(v) == 1, (col, v)
        v = v[0]
    if hasattr(v, "tolist"):
        v = v.tolist()
        if isinstance(v, list):
            assert len(v) == 1
            v = v[0]
    if col in ("N1", "N2", "N3"):
        f = float(v)
        assert f == int(f), (col, v)
        return str(int(f))
    if col == "RT":
        f = float(v)
        return "n/a" if math.isnan(f) else repr(f)
    s = str(v)
    return s if s else "n/a"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--mat")
    g.add_argument("--tsv")
    a = ap.parse_args()
    for ev in sorted(glob.glob(os.path.join(a.root, "sub-P*/ieeg/sub-P*_task-arithmetic_events.tsv"))):
        k = os.path.basename(ev).split("_")[0][len("sub-P"):]
        table = from_mat(os.path.join(a.mat, f"trials_P{k}.mat")) if a.mat else \
            from_tsv(os.path.join(a.tsv, f"nm000354_P{k}_stimuliValues.tsv"))
        with open(ev, newline="") as f:
            rows = list(csv.DictReader(f, delimiter="\t"))
            header = list(rows[0].keys())
        assert len(rows) == len(table), (ev, len(rows), len(table))
        for i, r in enumerate(rows):
            assert r["trial_type"] == f"trial-{i + 1:03d}", (ev, i, r["trial_type"])
            for c in COLS:
                r[c] = fmt(c, table[i][c])
        out = [c for c in header if c not in COLS] + COLS
        with open(ev, "w", newline="") as f:
            w = csv.DictWriter(f, out, delimiter="\t", lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
        print(ev, len(rows))


if __name__ == "__main__":
    main()
