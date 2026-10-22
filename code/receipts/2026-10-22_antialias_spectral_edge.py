import argparse
import hashlib
from pathlib import Path

import mne
import numpy as np
import pandas as pd
import scipy
from scipy import signal

REF_BAND_HZ = (190, 200)
DROPS_DB = (1, 3, 10)
PROBES_HZ = (220, 240)


def roll_off(db: np.ndarray, freqs: np.ndarray) -> dict[str, float]:
    ref = db[(freqs >= REF_BAND_HZ[0]) & (freqs <= REF_BAND_HZ[1])].mean()
    drop = ref - db
    above = freqs >= REF_BAND_HZ[1]
    out = {f"-{d} dB (Hz)": float(freqs[above & (drop >= d)][0]) for d in DROPS_DB}
    out |= {f"drop {f} Hz (dB)": float(drop[freqs == f][0]) for f in PROBES_HZ}
    return out


def measure(vhdr: Path) -> dict[str, object]:
    raw = mne.io.read_raw_brainvision(vhdr, preload=True, verbose="error")
    sfreq = raw.info["sfreq"]
    events = pd.read_csv(
        vhdr.with_name(vhdr.name.replace("_ieeg.vhdr", "_events.tsv")), sep="\t"
    )
    channels = pd.read_csv(
        vhdr.with_name(vhdr.name.replace("_ieeg.vhdr", "_channels.tsv")), sep="\t"
    )
    lengths = np.round(events["duration"].to_numpy() * sfreq).astype(int)
    n = int(lengths[0])
    contiguous = (lengths == n).all() and (
        events["sample"].to_numpy() == np.arange(len(events)) * n
    ).all()
    assert contiguous and len(events) * n == raw.n_times, (
        f"{vhdr.name}: epochs not back-to-back"
    )
    assert channels["name"].tolist() == raw.ch_names, (
        f"{vhdr.name}: channels.tsv names != header"
    )
    # shape: (channels, epochs, samples); Welch windows stay inside each epoch
    data = raw.get_data().reshape(len(raw.ch_names), len(events), n)
    freqs, psd = signal.welch(
        data, fs=sfreq, nperseg=int(sfreq), noverlap=int(sfreq) // 2, axis=-1
    )
    db = 10 * np.log10(psd.mean(axis=1))
    per_channel = np.array([roll_off(ch, freqs)["-3 dB (Hz)"] for ch in db])
    return {
        "recording": vhdr.name.removesuffix("_ieeg.vhdr"),
        "channels": len(raw.ch_names),
        "epochs": len(events),
        "high_cutoff in channels.tsv": "/".join(
            f"{v:g}" for v in sorted(channels["high_cutoff"].unique())
        ),
        **roll_off(np.median(db, axis=0), freqs),
        "per-channel -3 dB min/median/max (Hz)": "/".join(
            f"{v:g}" for v in np.percentile(per_channel, [0, 50, 100])
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path, help="BIDS root of nm000354")
    root = parser.parse_args().root
    vhdrs = sorted(root.glob("sub-*/ieeg/*_ieeg.vhdr"))
    print(f"mne {mne.__version__}, scipy {scipy.__version__}, numpy {np.__version__}")
    table = pd.DataFrame([measure(v) for v in vhdrs])
    print(f"{len(table)} recordings, {table['channels'].sum()} channels\n")
    print(table.to_markdown(index=False, floatfmt=".1f"))
    numeric = table.select_dtypes("number").drop(columns=["channels", "epochs"])
    print("\nacross recordings:")
    print(numeric.agg(["min", "median", "max"]).T.to_markdown(floatfmt=".1f"))
    print("\nsha256:")
    for path in sorted(
        p for v in vhdrs for p in v.parent.glob("*_ieeg.*") if p.suffix != ".json"
    ):
        print(hashlib.sha256(path.read_bytes()).hexdigest(), path.relative_to(root))


if __name__ == "__main__":
    main()
