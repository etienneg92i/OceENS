# Lab 1 — Récapitulatif (OcéENS, 25 septembre 2026)

Notes personnelles pour pouvoir expliquer ce qui a été fait, et pourquoi. Fork : <https://github.com/etienneg92i/OceENS>.

## La règle du jour

> Nettoyer ne pose aucune seam. Rien n'est conçu tant qu'un nombre ne le demande pas.

Aujourd'hui, on avait le droit de **déplacer, renommer et découper** des fichiers, et de **nommer** une seam dans le Design Document. On n'avait pas le droit de concevoir une interface ni d'approfondir un module : c'est pour le 2 octobre. Le test en cas de doute : si je suis en train de choisir *ce qu'un appelant doit voir*, c'est du design, donc je m'arrête. Si je range du code existant là où il doit être, je continue.

## L'ordre du Backlog, et pourquoi

Chaque étape rend la suivante possible :

1. **Rendre le README vrai (#91)** vient en premier parce que tant que les instructions pour lancer le projet sont fausses, on ne peut suivre aucune autre étape.
2. **Seeder la base (#84)** vient avant le packaging parce qu'un projet qui tourne sur une base vide ne montre rien sur quoi vérifier que les changements suivants n'ont rien cassé.
3. **Packager (#90)** vient avant les frontières parce que le check a besoin d'un paquet racine importable, et que le packaging supprime les imports qui ne marchaient que grâce au dossier courant.
4. **Mettre les packages derrière des frontières (#96)** vient en dernier parce qu'on ne peut poser de frontières qu'entre des packages qui existent.

Le Lab 2 cassera cet ordre exprès et demandera pourquoi c'était sans danger : il faut donc connaître ces quatre phrases.

## Étape 1a — Faire tourner la fork (smoke test)

`docs/smoke-test.md` est la source de vérité pour lancer le projet. Il contient des vérifications statiques, puis cinq étapes : démarrage local, Docker, codes de sortie sur une configuration invalide, démarrage sans clé LLM, puis avec une clé LLM.

**Ce qui s'est passé sous Windows ARM64** (mon PC, avec un processeur Snapdragon) :

- `py -3.12` ne trouvait aucun Python 3.12. Le smoke test supposait qu'il était installé, sans le dire.
- Avec le Python 3.12 **ARM64**, `pip install` échouait sur `cryptography` 50.0.1, tirée par `msal` : il n'existe pas de wheel `win_arm64`, donc pip essayait de la compiler avec Rust, et Windows bloquait Rust (`WinError 4551`, contrôle d'application).
- **Solution** : installer Python **3.12.10 x64** depuis python.org. Il tourne en émulation, et toutes les dépendances ont un wheel x64. Pour vérifier, `sysconfig.get_platform()` doit afficher `win-amd64`, alors que `platform.machine()` affiche `ARM64` dans tous les cas.
- Ces trouvailles ont été ajoutées au smoke test, dans une section « Prerequisites ».

**Résultat** : les étapes 1, 3, 4 et 5 passent. L'étape 2 (Docker) reste **à faire**.

**Incident à retenir** : j'ai collé ma clé LLM dans un chat. Une clé collée ailleurs que dans `.env` est compromise, il faut la révoquer et en générer une nouvelle. C'est exactement l'incident dont parlait la Lecture 1. La clé ne va que dans `.env`, qui est ignoré par Git.

## Étape 1b — Rendre le README vrai (#91) — commit `a8cef96`

**Pourquoi** : un README auquel on ne peut pas faire confiance coûte plus cher que pas de README du tout.

**Ce qui était faux, et a été corrigé** :

- Le démarrage manuel : `python -m venv env`, `env/scripts/activate` (bloqué sous Windows), puis `fastapi dev`, qui ne marche pas parce que `fastapi-cli` n'est pas installé.
- Docker : le README disait que le conteneur rechargeait le code (`--reload`), c'était faux. Il proposait aussi une commande `docker run` avec une image que rien ne construit.
- La configuration : il ne listait que la moitié des variables d'environnement. Maintenant, elles y sont toutes, en cohérence avec `.env.example`.
- Le premier lancement : rien ne disait qu'on peut démarrer sans identifiants Entra ni clé LLM (`AUTH_MODE=dev`).
- Les coûts LLM : le README parlait de dollars, alors que le code stocke les tarifs **en euros**, et que `gemma4:26b` a un forfait de 2 à 5 centimes par synthèse, pas 0 $.
- La structure du projet : il manquait des fichiers (`settings_store.py`, `docs/`…).

**Ce qui a été ajouté** :

- Un **lien vers le smoke test**, au lieu de recopier ses commandes. Une seule source de vérité, donc les deux documents ne peuvent plus se contredire.
- **Un piège Docker trouvé dans le code** : si `LOCAL_DATABASE_DIR` a une valeur dans `.env`, `docker compose` l'utilise pour le montage, mais la passe aussi au conteneur via `env_file`. L'application écrit alors la base *hors* du volume monté, et les données sont perdues avec le conteneur. Il faut laisser la variable vide avec Compose.
- La note Windows ARM64.

**Traduction** : README, `CONTEXT.md`, l'ADR et le smoke test sont passés en anglais. Les mots du produit restent en français (*sondage*, *synthèse*, *verbatim*, *filière*), parce que l'application est en français. `CONTEXT.md` explique cette règle. L'ADR a été renommé `0001-course-2026-default-branch.md`.

## Étape 1c — Seeder la base (#84) — commit `d5a70e7`

**Le problème** : pour tester un écran avec les droits d'un rôle, il faut se connecter (via `/dev/login`) en tant qu'utilisateur qui n'a *que* ce rôle. Le seed n'avait aucun `facilitator`, et le responsable de programme comme la directrice de campus étaient aussi `admin`. En se connectant avec eux, on avait tous les droits, donc on ne testait rien.

**Ce qui a été fait** : trois utilisateurs ajoutés dans `core/seed.py`, avec les identifiants 23, 24 et 25, **après le dernier existant (22)**, pour ne toucher à aucune soumission ni à aucun répondant :

| Utilisateur | Rôle unique |
|---|---|
| `facilitator.mdai5@epf.fr` | `facilitator:MDAI5` |
| `program.manager.mdai5@epf.fr` | `program_manager:MDAI5` |
| `campus.manager.montpellier@epf.fr` | `campus_manager:Montpellier` |

MDAI5 et Montpellier sont le programme et le campus du sondage 1, donc chacun voit des données tout de suite. Il y avait déjà un « admin seul » (`arnaud.jousset@epf.fr`) et un « étudiant seul » (`bob.leponge@epfedu.fr`).

**Vérifié** : chacun arrive sur son dashboard et est refusé sur `/dashboard/admin`. Il y a toujours 40 soumissions et 40 répondants.

**À savoir** : le seed de démo ne s'exécute que si la base est **vide**. Pour le relancer, il faut supprimer `database/` (après avoir arrêté uvicorn, sinon Windows refuse, car le fichier est ouvert).

## Étape 1d — Packager (#90)

**Le problème** : il n'y avait ni `pyproject.toml` ni paquet racine. Tous les imports et tous les chemins (`templates`, `static`, `import`) dépendaient du **dossier courant** : l'application ne démarrait que depuis la racine du dépôt, et aucun outil ne pouvait l'importer.

**Ce qui a été fait** :

- **Un seul paquet racine**, `src/oceens/`. `core/`, `models/`, `routers/`, `services/` et les 4 modules racine y ont été déplacés, et tous les imports s'écrivent maintenant `from oceens.…`.
- Le `__init__.py` manquant ajouté dans `services/`.
- Les deux imports locaux de `core.database` dans `core/auth.py` remontés en haut du fichier : ils n'avaient plus besoin d'être locaux.
- **uv** comme gestionnaire. Les dépendances passent de `requirements.txt` (supprimé) à `pyproject.toml`, avec un `uv.lock` commité, et `.python-version` fixe `3.12`.
- `templates/`, `static/` et `import/` sont retrouvés **par rapport au paquet** (`Path(__file__)`), plus par rapport au dossier courant.
- **La base reste où elle était**, dans `database/` à la racine. `PROJECT_ROOT` a été corrigé : sans ça, la base aurait silencieusement déménagé dans `src/oceens/`, en laissant l'ancienne derrière elle.
- **Des commandes installées** : `oceens` (l'application) et `oceens-summaries-daemon`. Le Dockerfile installe depuis `uv.lock`, et `launch.sh` utilise ces commandes.
- **Le smoke test mis à jour dans le même commit**, parce que le packaging cassait ses commandes (`uvicorn main:app`, les chemins de `compileall`, `from services import llm_client`).
- **Un piège corrigé** : le `.gitignore` contenait `oceens/`, ce qui aurait fait ignorer par Git tout nouveau fichier créé dans le paquet. La ligne est devenue `/oceens/`, limitée à la racine.

**Vérifié** : le smoke test passe tel qu'il est écrit, sur un clone neuf. `import oceens` fonctionne. L'application démarre depuis un autre dossier. Les **pages rendues et le schéma de la base sont identiques** avant et après, donc aucun changement de comportement.

**Pas vérifié**, à dire dans une PR : le build Docker (seules ses étapes `uv` ont été simulées) et `launch.sh` (relu, pas exécuté). **Un écart avec l'issue** : le daemon est lancé par `python -m oceens.summaries_generator_daemon`, avec le même interpréteur qu'uvicorn, plutôt que par sa commande installée. C'est plus sûr sous Windows.

**Sur ma machine**, la commande est : `uv sync --python "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"`, pour forcer le Python x64.

## Étape 1e — Le check d'architecture (#96)

`/setup-py-deep-modules` (une skill Claude Code, installée **au niveau utilisateur**, jamais dans le projet) a écrit `tach.toml` et `scripts/check_cycles.py`. Commit de mise en place : `112eb80`.

**Ce que le check impose** :

- **Pas de nom privé** (qui commence par `_`) importé depuis l'extérieur de son package. `uv run tach check`.
- **Pas de cycle d'imports entre packages**. `uv run python scripts/check_cycles.py`.

**La procédure, pour chaque violation, dans l'ordre** :

1. Lancer le check et copier la ligne de la violation.
2. **Écrire la Finding avant de toucher au code.** Si je ne sais pas remplir « What the code did » et « What it risked », c'est que je n'ai pas compris la violation.
3. Identifier sa nature, et appliquer **le seul déplacement autorisé** pour cette nature.
4. Vérifier que le comportement n'a pas changé : relancer le smoke test jusqu'à la page d'accueil, et relancer le check.
5. **Un commit par violation**, avec la première ligne de la Finding comme message.
6. **Le panneau stop** : si la correction demande une nouvelle fonction, une signature modifiée, ou un choix sur ce que voit l'appelant, c'est du design. On le note dans le Design Document, et on s'arrête.

Avec Claude Code, en **mode manuel** : j'écris la Finding moi-même, l'agent fait le déplacement, puis je relis son diff. Chaque ligne doit être un déplacement ou un chemin d'import, et je rejette tout le reste.

### Violation 1 — un nom privé — commit `079d0b7`

- **Le check** : `oceens.core.security._check_sondage_access_and_status` n'est pas dans l'interface publique de `oceens.core`.
- **La nature** : un nom privé. Est-ce que plus d'un module extérieur au package en a besoin ? Oui : `routers/summaries.py` et `routers/surveys.py`. **Il fait donc partie de l'interface.**
- **Le déplacement autorisé** : retirer le `_`, le ré-exporter dans `core/__init__.py`, l'ajouter à `__all__`, et mettre à jour les imports et les 4 appels. Pas de nouveau corps, pas de nouvelle signature.
- **Le risque** : quelqu'un qui modifie cette fonction « privée » croit que personne ne s'en sert à l'extérieur, et casse sans le savoir le contrôle d'accès aux sondages dans deux routeurs.
- *Si un seul module avait eu besoin de ce nom, la réponse aurait été différente* : l'appelant n'aurait pas dû l'avoir, donc panneau stop, et une question de seam pour le 2 octobre.

### Violation 2 — un cycle — commit `80b7f4a`

- **Le check** : `Circular dependency between packages: oceens.core <-> oceens.services`.
- **Les deux imports** : `core/seed.py` importe `services.settings_store`, et `services/visualisation_data.py` importe `core.database.engine`.
- **Quel package est le plus bas ?** `core`, parce que c'est lui qui détient la base de données, et que les autres en ont besoin.
- **Quel import remonte ?** Celui qui part du bas vers le haut : `core/seed.py` → `services.settings_store`. L'autre sens (`services` → `core`) est normal.
- **Le déplacement autorisé** : plusieurs noms traversent la frontière, dont des fonctions, donc on déplace **le fichier entier**. `services/settings_store.py` va dans `core/settings_store.py`, sans modification. Ça a du sens : il ne dépend que de `models` et lit et écrit la table `settings`, comme le reste de `core`. Les deux fichiers qui l'importent (`core/seed.py` et `routers/llm/prices.py`) ne changent que leur chemin d'import.
- **Le risque** : avec un cycle, l'ordre de chargement devient fragile. Le prochain import ajouté au mauvais endroit peut faire planter toute l'application au démarrage, avec une erreur du type « partially initialized module » qui pointe vers la mauvaise ligne. Et on ne peut plus comprendre `core`, le socle, sans lire aussi `services`.

**Résultat** : `tach check` → `[OK]`, et `check_cycles.py` → aucun cycle.

## Étape 2 — Le Design Document

C'est une **issue publique sur le dépôt upstream** (EPF-MDE/OceENS), pas sur ma fork, et elle doit être liée depuis la section « About » de ma fork. Elle contient :

- **What we inherited** : les deux Findings.
- **Clarifying questions** : mes questions au product owner (le prof), avec pour chacune une réponse ou une **hypothèse écrite**, et le type d'exigence.
  - **Fonctionnelle** : ce que l'application *fait*. Exemple : qui peut lire une synthèse.
  - **Non fonctionnelle** : *à quel niveau* elle le fait, en délai, volume, coût ou confidentialité. Exemple : synthèses prêtes en 24 h.
- **One number** (étape 3, ci-dessous).

« Je ne sais pas encore, j'ai demandé » est une réponse de design valable. Quand l'Owner répondra, sa réponse remplacera mon hypothèse. En cas de désaccord, la réponse de l'Owner l'emporte sur le Project Brief, et celle de l'IT Manager l'emporte sur les deux.

## Étape 3 — Un nombre : combien de temps avant que les synthèses d'un sondage fermé soient prêtes ?

**Ce que dit le code** :

- **Combien de jobs ?** Un par combinaison (module, enseignant, question ouverte) ayant des réponses. C'est donc la structure du sondage qui décide, pas le nombre d'étudiants : 85 par sondage dans le seed. **Fermer un sondage ne lance rien** : c'est le responsable qui clique sur « générer » (`routers/summaries.py`).
- **Combien en même temps ?** **Un seul.** Un seul daemon, une seule file commune à tous les sondages, et une attente de 30 s quand la file est vide (`summaries_generator_daemon.py`).
- **Combien de temps chacun ?** Au plus 120 s. Au-delà, le job est marqué en échec et **n'est jamais relancé**.
- **Et la deuxième fois ?** Les réponses sont mises en cache **pour toujours**, avec une graine fixe (42). Régénérer avec le même prompt redonne donc les mêmes synthèses instantanément, sans appel au LLM. Le cache est contourné si le prompt, les réponses ou **la clé API** changent.

**Mon hypothèse** : 20 s par synthèse, et les 52 programmes qui génèrent le même jour.

**Le nombre** : 52 × 85 × 20 s ≈ **25 h** pour la campagne, alors que mon objectif supposé est **24 h**. Et dans le pire cas (toutes les requêtes à 120 s) : environ **6 jours**. **Conclusion** : le goulot, c'est la file qui traite une seule synthèse à la fois.

**La seam que je propose** : la file de synthèses, entre `routers/summaries.py` (qui dépose les jobs) et le daemon (qui les traite). C'est là que vivent le « un à la fois », l'attente de 30 s et le timeout de 120 s. **Je la nomme seulement** : décider ce que voient ses appelants, c'est pour le 2 octobre.

**L'hypothèse est à moi** : un agent peut lire le code à ma place, mais l'hypothèse est une affirmation sur le produit, et c'est à moi de la défendre.

## Ce qui reste à faire

- [ ] L'étape 2 du smoke test (Docker), d'autant que le Dockerfile a changé avec le packaging.
- [ ] Vérifier que le Design Document est lié depuis la section « About » de la fork.
- [ ] Poster mes questions sur EPF-MDE/OceENS#98.
- [ ] **Autonomy slot 1 (2 octobre)** : écrire le workflow CI qui lance `tach check` et le check de cycles à chaque push (c'est le dernier critère de #96).
- [ ] **Avant le 2 octobre** : lire les réponses de l'Owner sur #98, et remplacer mes hypothèses là où il a répondu.
- [ ] Facultatif : une PR contre `course-2026` avec les trouvailles Windows ARM64 du smoke test.

## Commandes utiles (Windows, depuis `C:\dev\OceENS`)

```powershell
uv sync --python "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"   # installer
.venv\Scripts\uvicorn.exe oceens.main:app --port 8000                       # lancer
uv run tach check                                                           # interfaces
uv run python scripts/check_cycles.py                                       # cycles
Get-NetTCPConnection -LocalPort 8000 -State Listen | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }   # libérer le port 8000
```
