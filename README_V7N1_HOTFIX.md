# V7N.1 hotfix - PowerShell 5.1 encoding

Cause:
PowerShell 5.1 interprets a UTF-8 .ps1 without BOM as an ANSI script.
The literal Unicode musical-rest glyphs in the V7N preflight were therefore
mis-decoded before execution.

Fix:
- preflight script contains ASCII only;
- Twig/engine/controller files are read explicitly as UTF-8;
- musical rest symbols are generated at runtime from:
  - U+1D13D MUSICAL SYMBOL QUARTER REST
  - U+1D13E MUSICAL SYMBOL EIGHTH REST
- no EZScore file is modified.

Apply:

cd H:\EZChords_Benchmark

tar -xf "$env:USERPROFILE\Downloads\EZChords_Benchmark_V7N1_PREFLIGHT_ENCODING.zip" `
  -C H:\EZChords_Benchmark `
  --strip-components=1

powershell -ExecutionPolicy Bypass -File .\scripts\preflight-v7n.ps1

H:\Python\pythoncore-3.14-64\python.exe .\python\engine.py --self-test
