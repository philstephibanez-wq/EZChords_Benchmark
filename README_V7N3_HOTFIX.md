# V7N.3 hotfix - self-test AST

Cause:
The V7N.2 self-test still searched for the literal text
`def harmonic_silence_mask(` in the source. That literal was present inside
the assertion itself, so the test necessarily failed.

Fix:
The self-test now parses `engine.py` with Python `ast` and checks the actual
set of defined function names. It fails only if a real
`harmonic_silence_mask` function exists.

No algorithmic change.
No metric change.
No EZScore modification.

Apply:

cd H:\EZChords_Benchmark

tar -xf "$env:USERPROFILE\Downloads\EZChords_Benchmark_V7N3_SELFTEST_AST.zip" `
  -C H:\EZChords_Benchmark `
  --strip-components=1

powershell -ExecutionPolicy Bypass -File .\scripts\preflight-v7n.ps1

H:\Python\pythoncore-3.14-64\python.exe .\python\engine.py --self-test
