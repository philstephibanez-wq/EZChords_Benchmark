# TERMINOLOGY GREP — R2A

Audit effectué après le checkpoint poussé sur `main`.

## Résultat du grep

- 453 occurrences collectées dans l'artefact de grep accidentel.
- 48 fichiers actifs contiennent encore au moins une occurrence de l'ancien vocabulaire.
- 38 chemins de fichiers contiennent eux-mêmes `adn`, `dna`, `chromosome`, `genome`, `gene` ou `region`.
- un fichier de 65 405 octets correspondant à la sortie colorée du grep a été commité accidentellement à la racine ; R2A le supprime automatiquement.

## R2A traite maintenant

### Persistance SQLite
- genome → preset
- region → phase
- gene → module

Tables migrées :
- `genome_gene_revisions` → `preset_module_revisions`
- `genome_region_revisions` → `preset_phase_revisions`
- `genome_region_revision_genes` → `preset_phase_revision_modules`
- `genome_region_revision_parents` → `preset_phase_revision_parents`
- `scientific_run_genome` → `scientific_run_preset`
- `genome_region_baselines` → `preset_phase_baselines`

Validation humaine :
- `scope=region/gene` → `phase/module`
- `gene_key` → `module_key`
- `region_revision_ref` → `phase_revision_ref`
- `gene_revision_ref` → `module_revision_ref`
- sujets `region:*` → `phase:*`

Resource locks :
- colonne `region` → `phase`

### Couche applicative
- `AnalysisRunRegistry` devient l'implémentation canonique ;
- `PresetRegistry` devient l'implémentation canonique ;
- `DnaRegistry` / `GenomeRegistry` ne restent que comme aliases de compatibilité ;
- l'export actif devient `export-presets.py` / `PresetExportController`;
- le catalogue affiche `Chaîne d’analyse`;
- les derniers libellés ADN visibles sont nettoyés.

## R2A ne traite PAS encore

Les internals Python PROFILE profonds restent volontairement pour R2B :
- `gene.py`
- `gene_registry.py`
- `genes/*`
- `gene_spec.py`
- `perf_probe.py`
- clés sérialisées historiques `gene_registry`, `genome`, `genes`
- schémas historiques `ezstudio.gene-spec.v1`, `ezstudio.genome.region.v1`

Raison : séparer la migration de persistance de la migration du contrat Python afin de pouvoir isoler toute régression.
