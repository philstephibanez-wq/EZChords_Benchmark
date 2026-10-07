# EZChords Benchmark V9 — Positive Harmonic Support

## Goal
Reduce false `N` detections introduced by the V8 `3-of-4 silence votes` rule.

## Active rule
Stems used:
- bass
- guitar
- piano
- other

Vocals and drums remain excluded.

Each stem is analysed by lv-chordia `ismir2017`.

A stem that returns `N` does not vote against the chord.

The active rule is:

`N only if NONE of bass/guitar/piano/other reports a non-N label on the beat.`

So:
- 1 supporting stem => keep chord
- 2 supporting stems => keep chord
- 3 supporting stems => keep chord
- 4 supporting stems => keep chord
- 0 supporting stems => N

There is no new RMS threshold and no post-song ad-hoc correction.

## Diagnostics
`E_positive_harmonic_support` records, for every beat:
- `support_count`
- `supporting_stems`
- each stem's label
- final `is_no_chord`

## Cache
Existing stems are reused from:
`H:\temp\EZChords_Benchmark\stems\<sha256>\current.json`

No stem regeneration is needed when the cache exists.

## Frozen scope
The six metric methods are not modified.
EZScore remains read-only.

## Apply

```powershell
cd H:\EZChords_Benchmark

tar -xf "$env:USERPROFILE\Downloads\EZChords_Benchmark_V9_POSITIVE_HARMONIC_SUPPORT.zip" `
  -C H:\EZChords_Benchmark `
  --strip-components=1

powershell -ExecutionPolicy Bypass -File .\scripts\preflight-v9.ps1
```

Then use the existing `Ré-analyser avec stems en cache` action.
