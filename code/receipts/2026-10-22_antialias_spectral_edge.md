# Receipt: measured spectral edge vs documented 400 Hz anti-aliasing cutoff

**Claim**: Keep high_cutoff 400 Hz; document the measured spectral edge (-3 dB at 213-214 Hz) (v1.0.3)

## Source
- NEMAR nm000354 `origin/main` at `d087d49338027830f05eb17152c5fef19501a57a`, all 20 recordings
  `sub-P*/ieeg/sub-P*_task-arithmetic_ieeg.{vhdr,eeg,vmrk}` with their `_events.tsv` and `_channels.tsv`.
- Read from a full copy of that tree. Identity with `origin/main`: sha256 of the 20 `.eeg` and 20 `.vhdr` files (printed
  by the script) equal the `SHA256E` git-annex keys at `d087d49` (40/40); the 20 `.vmrk`, 20 `_events.tsv`,
  20 `_channels.tsv` and 20 `_ieeg.json` are byte-identical to `git show d087d49:<path>` (80/80).
- Documented value: Kalinova et al. 2026, Sci Rep 16:5587, doi:10.1038/s41598-026-36122-z, Methods: low-pass 8th-order
  Chebyshev Type I IIR, cutoff 400 Hz, zero phase, then downsampling from 2048 Hz to 512 Hz.
- At this PR head the 20 `_channels.tsv` are byte-identical to `d087d49` (`high_cutoff` 400 on all 1518 rows) and the
  20 `_ieeg.json` differ from it only by the measured note appended to
  `SoftwareFilters["Anti-aliasing low-pass"]["Description"]` (`"Cutoff (Hz)"` stays 400).

## Method
- Script: `2026-10-22_antialias_spectral_edge.py <bids_root>` (mne 1.13.2, scipy 1.18.1, numpy 2.5.4), run on Slurm.
- Reader: `mne.io.read_raw_brainvision(preload=True)`; MNE's µV-to-V scaling is applied, which does not affect the
  relative dB values below.
- Each file holds equal-length epochs written back to back; the script asserts that `_events.tsv` onsets are contiguous
  multiples of the epoch length (4609 samples) covering the whole file, and that `_channels.tsv` names equal the header.
- PSD: `scipy.signal.welch` per channel and epoch, Hann window, 512 samples (1 Hz bins), 256-sample overlap, windows
  kept inside each epoch; averaged over epochs and windows, converted to dB.
- Recording spectrum: median over channels of the per-channel dB spectra.
- Reference level: mean of the recording spectrum over 190-200 Hz. "-N dB" = first frequency >= 200 Hz at which the
  spectrum is at least N dB below the reference; "drop F Hz" = reference minus spectrum at F Hz.
- Per-channel -3 dB: same definition applied to each channel's own spectrum (min/median/max over channels).

## Result
| recording               |   channels |   epochs |   high_cutoff in channels.tsv |   -1 dB (Hz) |   -3 dB (Hz) |   -10 dB (Hz) |   drop 220 Hz (dB) |   drop 240 Hz (dB) | per-channel -3 dB min/median/max (Hz)   |
|:------------------------|-----------:|---------:|------------------------------:|-------------:|-------------:|--------------:|-------------------:|-------------------:|:----------------------------------------|
| sub-P1_task-arithmetic  |         32 |      114 |                           400 |        209.0 |        214.0 |         221.0 |                9.0 |               33.7 | 213/214/215                             |
| sub-P10_task-arithmetic |         90 |       49 |                           400 |        209.0 |        214.0 |         221.0 |                9.2 |               33.7 | 213/214/215                             |
| sub-P11_task-arithmetic |        104 |       92 |                           400 |        209.0 |        213.0 |         221.0 |                9.3 |               34.4 | 212/213/215                             |
| sub-P12_task-arithmetic |         75 |      112 |                           400 |        209.0 |        214.0 |         221.0 |                9.2 |               33.9 | 213/214/215                             |
| sub-P13_task-arithmetic |         59 |       72 |                           400 |        209.0 |        214.0 |         221.0 |                9.5 |               34.1 | 200/214/215                             |
| sub-P14_task-arithmetic |         81 |       98 |                           400 |        209.0 |        214.0 |         221.0 |                9.4 |               33.7 | 212/214/215                             |
| sub-P15_task-arithmetic |         86 |       94 |                           400 |        209.0 |        213.0 |         221.0 |                9.4 |               34.2 | 212/214/215                             |
| sub-P16_task-arithmetic |        116 |       96 |                           400 |        209.0 |        214.0 |         221.0 |                9.3 |               33.8 | 213/214/215                             |
| sub-P17_task-arithmetic |        104 |       94 |                           400 |        208.0 |        213.0 |         221.0 |                9.6 |               34.6 | 212/213/215                             |
| sub-P18_task-arithmetic |         73 |       94 |                           400 |        209.0 |        214.0 |         221.0 |                9.0 |               33.5 | 212/214/215                             |
| sub-P19_task-arithmetic |         55 |      111 |                           400 |        209.0 |        213.0 |         221.0 |                9.5 |               34.1 | 212/213/215                             |
| sub-P2_task-arithmetic  |         56 |      117 |                           400 |        208.0 |        213.0 |         221.0 |                9.4 |               34.3 | 213/213/214                             |
| sub-P20_task-arithmetic |         65 |       98 |                           400 |        209.0 |        214.0 |         221.0 |                8.9 |               33.6 | 213/214/215                             |
| sub-P3_task-arithmetic  |         39 |      102 |                           400 |        209.0 |        214.0 |         221.0 |                9.2 |               34.3 | 213/214/215                             |
| sub-P4_task-arithmetic  |         48 |      100 |                           400 |        209.0 |        214.0 |         221.0 |                9.3 |               34.1 | 213/214/215                             |
| sub-P5_task-arithmetic  |         97 |      108 |                           400 |        209.0 |        214.0 |         221.0 |                9.2 |               33.9 | 213/214/215                             |
| sub-P6_task-arithmetic  |         75 |       84 |                           400 |        209.0 |        214.0 |         221.0 |                9.0 |               33.6 | 207/214/215                             |
| sub-P7_task-arithmetic  |         59 |      123 |                           400 |        209.0 |        214.0 |         221.0 |                9.0 |               33.7 | 212/214/215                             |
| sub-P8_task-arithmetic  |         93 |      100 |                           400 |        210.0 |        214.0 |         222.0 |                8.7 |               33.3 | 213/214/215                             |
| sub-P9_task-arithmetic  |        111 |       67 |                           400 |        209.0 |        213.0 |         221.0 |                9.4 |               34.6 | 212/213/215                             |

Across recordings:
|                  |   min |   median |   max |
|:-----------------|------:|---------:|------:|
| -1 dB (Hz)       | 208.0 |    209.0 | 210.0 |
| -3 dB (Hz)       | 213.0 |    214.0 | 214.0 |
| -10 dB (Hz)      | 221.0 |    221.0 | 222.0 |
| drop 220 Hz (dB) |   8.7 |      9.3 |   9.6 |
| drop 240 Hz (dB) |  33.3 |     33.9 |  34.6 |

The README and `*_ieeg.json` quote the across-recordings ranges: -1 dB at 208-210 Hz, -3 dB at 213-214 Hz,
-10 dB at 221-222 Hz, 33.3-34.6 dB down at 240 Hz.

## Coverage
20 of 20 recordings (1518 of 1518 channels, 1925 of 1925 epochs); 20 of 20 `_channels.tsv` and 20 of 20 `_ieeg.json`.
