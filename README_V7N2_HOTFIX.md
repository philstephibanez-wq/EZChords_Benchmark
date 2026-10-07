# V7N.2 hotfix - contract test false positive

Cause:
V7N.1 searched the literal text "harmonic_silence_mask".
The V7N engine self-test itself contained that text in an assertion, so the
preflight reported the old RMS implementation although the function was gone.

The engine self-test had the same self-reference problem.

Fix:
- preflight now searches only an actual Python function definition:
  ^\s*def\s+harmonic_silence_mask\s*\(
- engine self-test checks "def harmonic_silence_mask(" instead of the bare name.
- no algorithmic change.
- no EZScore modification.

Apply:

cd H:\EZChords_Benchmark

tar -xf "$env:USERPROFILE\Downloads\EZChords_Benchmark_V7N2_CONTRACT_HOTFIX.zip" `
  -C H:\EZChords_Benchmark `
  --strip-components=1

powershell -ExecutionPolicy Bypass -File .\scripts\preflight-v7n.ps1

H:\Python\pythoncore-3.14-64\python.exe .\python\engine.py --self-test
