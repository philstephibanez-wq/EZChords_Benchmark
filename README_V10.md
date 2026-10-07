# EZChords Benchmark V10 — Observability Platform

Baseline: `d303b6d`  
Engine analysis baseline intentionally preserved: `r9-positive-harmonic-support`.

## Scope

This delivery adds a real observability layer **outside `engine.py`**. The six validated metric/downbeat methods are not modified.

Every future benchmark run now automatically:

1. runs the existing V9 analysis;
2. computes exhaustive per-track / per-beat diagnostic features;
3. persists structured data in local MongoDB;
4. generates reconstructible numerical artifacts (`.npz`, `.json`, `.jsonl`);
5. renders diagnostic plots;
6. detects notable events;
7. creates one upload-ready scientific ZIP.

## MongoDB

Local only:

- URI: `mongodb://127.0.0.1:27017`
- database: `ezchords_benchmark`
- collections:
  - `runs`
  - `beat_features`
  - `events`

MongoDB stores structured observability data. Audio/stem binaries remain on disk.

## Numeric features

For master + bass/guitar/piano/other:

- RMS
- spectral centroid
- spectral rolloff
- spectral flatness
- onset strength
- CQT chroma
- chroma strength / energy
- Tonnetz
- log-mel spectrogram
- 100 Hz waveform envelope

The numerical arrays are saved in compressed NPZ, so every generated diagnostic plot is reproducible from exported data.

## Generated plots

- log-mel spectrogram per track
- chromagram per track
- stem RMS timeline
- positive harmonic support timeline
- metric phase methods
- automatic zoom around every chord→N and N→chord transition

## Event Inspector data

Automatic structured events include:

- `chord_to_N`
- `N_to_chord`
- `stem_label_divergence`
- `positive_support_observation`
- `metric_phase_divergence`

This makes the current V9 late-N problem directly queryable from Mongo and from the scientific ZIP.

## Scientific export

Generated automatically:

`H:\temp\EZChords_Benchmark\exports\EZChords_Run_XXXXXX_Scientific.zip`

No separate diagnostic script is needed for future runs. Upload that single ZIP for analysis.

The bundle contains:

- `manifest.json`
- `run.json`
- `environment.json`
- `audio.json`
- `stems.json`
- raw engine result
- per-beat JSONL tables
- NPZ feature matrices
- diagnostic PNGs

Audio binaries are intentionally not copied into the ZIP.

## Installation

Apply the package:

```powershell
cd H:\EZChords_Benchmark

tar -xf "$env:USERPROFILE\Downloads\EZChords_Benchmark_V10_OBSERVABILITY.zip" `
  -C H:\EZChords_Benchmark `
  --strip-components=1
```

Install MongoDB + Python observability dependencies once:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install-observability-v10.ps1
```

Validate:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\preflight-v10.ps1
```

Then run the benchmark normally. The next run automatically produces the Mongo records and scientific ZIP.

## Important contracts

- EZScore is untouched.
- V10 observability has no path under `H:\EZScore`.
- Stems remain benchmark-owned under `H:\temp\EZChords_Benchmark`.
- No negative timing offset.
- No modification of the six metric/downbeat methods.
- Mongo binds to localhost only.
