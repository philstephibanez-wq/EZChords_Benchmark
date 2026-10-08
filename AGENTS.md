# AGENTS.md

## ⛔ RÈGLE ABSOLUE — FICHIERS TEMPORAIRES

- **Aucun fichier temporaire, test ponctuel, installateur ponctuel, script apply/migrate/preflight/hotfix/rollback, backup, ZIP de livraison, log, dump, cache, export de diagnostic, artefact généré ou fichier de migration intermédiaire ne doit être créé dans ce dépôt.**
- Tous ces fichiers doivent être créés sous `H:\temp`.
- `H:\temp` est **jetable** et peut être purgé régulièrement **sans préavis**.
- Le produit ne doit donc **jamais dépendre** d'un fichier présent dans `H:\temp`.
- Seuls les composants durables et réellement nécessaires au produit ont leur place dans le dépôt.
- Avant tout staging/commit : vérifier `git status --short` et exclure toute pollution.
- Ne pas utiliser `git add .` ou `git add -A` tant que des fichiers non vérifiés sont présents.
- Si le caractère durable d'un fichier est douteux, **il va dans `H:\temp` par défaut**.

Voir aussi `REPOSITORY_HYGIENE.md`.
