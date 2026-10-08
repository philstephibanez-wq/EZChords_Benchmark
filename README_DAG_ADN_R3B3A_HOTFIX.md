# EZStudio_lab — DAG ADN R3B3A HOTFIX

## Cause exacte

`migrate-dag-adn-r3b3.php` bootait le Kernel Symfony puis faisait :

```php
$kernel->getContainer()->get(DnaRegistry::class)
```

`DnaRegistry` est un service privé/autowiré. En environnement compilé Symfony peut l'inliner ou le supprimer du container public, d'où :

```text
ServiceNotFoundException:
The "App\Service\DnaRegistry" service or alias has been removed or inlined
```

Le préflight R3B3 ne vérifiait pas la présence réelle des tables ADN, donc il pouvait passer après l'échec de la migration.

## Correctif

- la migration n'accède plus au container Symfony ;
- elle instancie directement `Database` avec le chemin canonique :
  `data/benchmark.sqlite`;
- elle instancie `DnaRegistry($db)` puis exécute `ensureSchema()`;
- elle vérifie immédiatement les 6 tables ADN ;
- le préflight vérifie désormais le schéma réel SQLite.

Aucun moteur, worker, orchestrator, run existant ou résultat scientifique n'est modifié.

## Application

```powershell
cd H:\EZStudio_lab

tar -xf "$env:USERPROFILE\Downloads\EZStudio_lab_DAG_ADN_R3B3A_HOTFIX.zip" `
  -C H:\EZStudio_lab `
  --strip-components=1

powershell -ExecutionPolicy Bypass -File .\scripts\apply-dag-adn-r3b3.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\preflight-dag-adn-r3b3.ps1
```
