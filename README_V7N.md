# EZChords Benchmark V7N — Native N + stems benchmark

## Contrat

Cette livraison remplace V6b.

- `N` reste **interne** jusqu'au rendu.
- `/4` affiche `𝄽`.
- `/8` affiche `𝄾`.
- `N` ne déclenche aucune note MIDI.
- aucune logique finale `RMS faible => silence`.
- les **6 algorithmes métriques R5/R6 ne sont pas modifiés**.
- la grille active utilise uniquement le `N` natif de **lv-chordia / ismir2017** sur le master.
- HPSS et stems sont des variantes de **benchmark**, pas encore des décisions de production.

## EZScore : strictement aucune modification

Le benchmark peut exécuter :

`H:\EZScore\analysis\stems_only.py`

mais EZScore est traité en **READ-ONLY**.

Aucune sortie n'est dirigée vers `H:\EZScore`.

Les stems du benchmark vont dans :

`H:\temp\EZChords_Benchmark\stems\<sha256>\...`

Le script EZScore reçoit donc son propre `--storage-root` de benchmark.

Cela réutilise :
- BS-RoFormer ;
- MelBand-RoFormer ;
- les mêmes 7 stems analytiques WAV ;
- `current.json` / `manifest.json` ;
- le cache par hash ;
- `timebase=original_audio_seconds`.

Aucun Opus n'est utilisé pour l'analyse N.

## Variantes enregistrées

- A `master / lv-chordia ismir2017` — **active**
- B `master HPSS / lv-chordia ismir2017`
- C `bass+guitar+piano+other / lv-chordia ismir2017`
- D un diagnostic séparé sur `bass`, `guitar`, `piano`, `other`
- E matrice de votes `N` par beat — diagnostic uniquement

Le résultat JSON conserve les indices `N` et les votes par beat.

## Application

```powershell
cd H:\EZChords_Benchmark

tar -xf "$env:USERPROFILE\Downloads\EZChords_Benchmark_V7N_NATIVE_STEMS.zip" `
  -C H:\EZChords_Benchmark `
  --strip-components=1

powershell -ExecutionPolicy Bypass -File .\scripts\preflight-v7n.ps1
```

Puis test Python direct :

```powershell
H:\Python\pythoncore-3.14-64\python.exe .\python\engine.py --self-test
```

Résultat attendu :

```text
ENGINE_SELF_TEST_OK
N_INTERNAL_CONTRACT_OK
EZSCORE_READ_ONLY_CONTRACT_OK
```

## Variables optionnelles

Pour déplacer uniquement les sorties benchmark :

```powershell
$env:EZCHORDS_STEMS_CACHE_ROOT = "H:\temp\EZChords_Benchmark\stems"
```

Pour pointer vers un autre emplacement du script **sans le copier/modifier** :

```powershell
$env:EZCHORDS_EZSCORE_STEMS_SCRIPT = "H:\EZScore\analysis\stems_only.py"
```

## Test Aline

Après purge/recréation habituelle du benchmark :
1. importer Aline ;
2. lancer l'analyse ;
3. vérifier en haut de la vue les comptes `N` A/B/C/D ;
4. écouter la grille ;
5. vérifier que `𝄽`/`𝄾` coupe bien le piano ;
6. noter dans l'issue #2 les beats de break corrects/faux positifs.

Référence de conception :
https://github.com/philstephibanez-wq/EZChords_Benchmark/issues/2
