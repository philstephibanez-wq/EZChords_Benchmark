# Timing diagnostic R16A

Fixes the previous diagnostic reader: cached stems are IEEE float WAV
(format tag 3), so Python's standard `wave` module cannot read them.

This version uses `soundfile`, already available in the EZChords analysis environment.

Run:

```powershell
cd H:\EZChords_Benchmark

H:\Python\pythoncore-3.14-64\python.exe `
  .\scripts\diagnose-run-timing.py `
  --run-id 16
```

Output:
`diagnostics\run-16-timing.json`
