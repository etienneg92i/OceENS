# OcéEns II

Course-evaluation platform for the EPF engineering school.

## Overview

**OcéEns II** lets program managers, facilitators, campus managers and administrators create and manage course-evaluation surveys (*sondages*) for EPF's programs (*filières*), and lets students answer them. Answers can be exported, visualised, and summarised by an LLM (*synthèses*). The interface uses EPF's official visual identity.

The application's own interface is in French. This documentation is in English and keeps a few French product words; `CONTEXT.md` says where that boundary lies.

### Tech stack

| Component | Technology |
|---|---|
| **Framework** | FastAPI (Python 3.12) |
| **Authentication** | Microsoft Entra ID (Azure AD) via OAuth 2.0 / MSAL and Microsoft Graph, or a development login (`AUTH_MODE=dev`) |
| **Database** | SQLite (SQLAlchemy + SQLModel) |
| **Templating** | Jinja2 (server-side rendering) |
| **Frontend** | HTML / CSS / JavaScript, no framework |
| **Server** | Uvicorn |
| **Logging** | Python's standard `logging`, through Uvicorn's handlers |
| **Exports** | Pandas (CSV) |
| **Summaries of free-text answers** | A separate daemon calling an LLM (`requests-cache`, `markdown-it-py`) |

---

## Roles

- `student`: answers the surveys they are enrolled in.
- `program_manager:<code>`: manages the surveys of their program(s).
- `facilitator:<code>`: runs the surveys of their program(s).
- `campus_manager:<campus>`: campus-wide scope.
- `admin`: general administration.

A user may hold several roles, each with its own scope (program or campus codes separated by `;`).

---

## Main pages and routes

| Route | Description |
|---|---|
| `/` | Home page, authentication hub. |
| `/login`, `/auth/callback`, `/logout` | Microsoft Entra ID authentication flow. |
| `/dev/login` | Development login: user picker on `GET`, login on `POST` (only with `AUTH_MODE=dev`, see [Development login](#development-login)). |
| `/dashboard/student` | Student dashboard. |
| `/dashboard/program-manager` | Program manager dashboard. |
| `/dashboard/facilitator` | Facilitator dashboard. |
| `/dashboard/campus-manager` | Campus manager dashboard. |
| `/dashboard/teachers/analytics` | Satisfaction score per teacher, filterable by year / semester / program. For `campus_manager` and `program_manager`, scoped to each one's perimeter. |
| `/dashboard/admin` | Administrator dashboard. |
| `/dashboard/survey-create` | Survey creation and settings. |
| `/api/surveys/{survey_id}` | Questionnaire (answering a survey). |
| `/api/surveys/{survey_id}/status` | Change a survey's status. |
| `/api/surveys/{survey_id}/students` | Manage the students enrolled in a survey. |
| `/api/surveys/{survey_id}/export` | CSV export of the answers. |
| `/api/surveys/{survey_id}/visualisation` | Answer visualisation. Accepts `?teacher=<name>` to open already filtered on one teacher. |
| `/api/surveys/{survey_id}/generate-summaries` | Queue LLM summary generation. |
| `/api/surveys/{survey_id}/destroy-summaries` | Delete the generated summaries. |
| `/api/users/{user_id}/role` | Change a user's role. |
| `/backend/prompts` | LLM prompt list (admin only). |
| `/backend/prompts/new` | Prompt creation form. |
| `/backend/prompts/{id}/edit` | Prompt edit form. |
| `/api/prompts` | Create a prompt (POST, form). |
| `/api/prompts/{id}` | Update a prompt (PUT, fetch). Refused if the prompt is referenced in `summaries`. |
| `/api/prompts/{id}/delete` | Delete a prompt (POST, form). Refused if the prompt is referenced in `summaries`. |
| `/backend/providers` | LLM providers (admin only), see [LLM providers](#llm-providers). |
| `/backend/llm/prices` | Price list per model (admin only). |
| `/backend/llm/costs` | Overall summary cost, per survey and per model (admin only). |

---

## Getting started

A fresh clone of `course-2026` runs in `dev` mode with **no Entra credentials and no LLM key**. The exact commands, for Windows (PowerShell) and for macOS / Linux, with the expected responses, are in **[`docs/smoke-test.md`](docs/smoke-test.md)**: this README does not repeat them. In short:

1. **Copy `.env.example` to `.env`.** It ships `AUTH_MODE=dev`, which needs no Entra credentials, and an empty `LLM_API_KEY`. `docker compose` refuses to start without a `.env` (`env file .env not found`), on purpose.
2. **Run it**, either way:
   - **With Docker Compose**: one command, which builds the image and serves the app on port 8000 (smoke test, step 2). A Docker daemon must be running.
   - **Without Docker**: Python **3.12**, a virtual environment named `.venv`, `pip install -r requirements.txt`, then `uvicorn main:app` (smoke test, step 1). The smoke test calls the environment's interpreter by its path rather than activating it, because PowerShell blocks `Activate.ps1` by default.
3. **Open <http://localhost:8000>** and log in through `/dev/login` as any seeded user.

On the first start against an empty database, the application creates the tables and inserts a **demonstration data set** (see `core/seed.py`): 25 users, four surveys with their submissions and answers, and one prompt, but no summaries. Among the users, there is at least one user per role holding **that role only**, to sign in as through `/dev/login`: `arnaud.jousset@epf.fr` (`admin`), `bob.leponge@epfedu.fr` (student, no role), `facilitator.mdai5@epf.fr` (`facilitator:MDAI5`), `program.manager.mdai5@epf.fr` (`program_manager:MDAI5`) and `campus.manager.montpellier@epf.fr` (`campus_manager:Montpellier`). Their scopes match seeded surveys, so each sees data straight away. The programs from `import/Program_list.csv`, the default LLM provider and the known model prices are synchronised on every start.

> [!NOTE]
> On **Windows on ARM64**, use a **64-bit (x64) Python 3.12**, not the ARM64 build: `cryptography`, pulled in by `msal`, has no ARM64 wheel for Windows and would have to be compiled. See the smoke test's prerequisites.

### Without an LLM key

The application starts and works normally with `LLM_API_KEY` empty; only the summaries are unavailable. A summary requested in that state is marked as a configuration error, and no call is made to the provider (smoke test, step 4).

### The summaries daemon

Summaries are generated by `summaries_generator_daemon.py`, a separate process that loops, writes to the database and calls the external LLM service, one job at a time. Start it only when you need it, in either of two ways:

- set `RUN_SUMMARIES_DAEMON=1` (also `true`, `yes`, `on`) in `.env`: Uvicorn then starts the daemon as a separate process at startup and stops it on shutdown. This is the way to use with Docker;
- or run `python summaries_generator_daemon.py` yourself.

### Docker details

`docker-compose.yaml` builds the image from the `Dockerfile`, passes `.env` to the container through `env_file` (the `.env` is never copied into the image), publishes port 8000, and restarts the container automatically (`restart: always`). It mounts two host folders:

- `${LOCAL_DATABASE_DIR:-./database}` on `/app/database`, where the SQLite file lives;
- `./import` on `/app/import`, the seed's CSV files.

The image copies the source code in at build time and runs Uvicorn **without** `--reload`: after changing the code, rebuild (`docker compose up --build`).

> [!WARNING]
> With Docker Compose, leave `LOCAL_DATABASE_DIR` empty in `.env`. Compose uses it for the host side of the mount, but `env_file` also passes it into the container, where the application then writes the database to that path *inside* the container, outside the mounted volume: the data is lost with the container.

### `launch.sh`

`launch.sh` is the production launcher without Docker, on the school's server: it runs the application (`python main.py`) and the summaries daemon in two separate `screen` sessions. It is written for that machine only: it `cd`s into a hard-coded path (`/home/mde-admin/OceENS`) and uses a virtual environment named `venv`.

---

## Configuration

Every setting is an environment variable, read from `.env` at startup (`load_dotenv()` in `main.py`, `core/auth.py` and the daemon). **[`.env.example`](.env.example) is the reference**: copy it, and read its comments. Variables the code reads:

| Variable | Default | Role |
|---|---|---|
| `AUTH_MODE` | `entra` | `entra` or `dev`, case- and space-insensitive. Any other value stops the application at startup (exit code 1). `.env.example` ships `dev`. See [Development login](#development-login). |
| `DEV_LOGIN_KEY` | empty | `dev` only. If set, every development login must provide it. Ignored, with a warning, in `entra`. |
| `ALLOWED_DOMAINS` | `epf.fr,epfedu.fr` | E-mail domains allowed to log in, comma-separated. Applies in both modes. |
| `SECRET_KEY` | empty | Signs the session cookies. **Required with `AUTH_MODE=entra`**: missing or empty, the application logs a critical error and exits with code 1. Optional in `dev` (see below). |
| `ENTRA_CLIENT_ID`, `ENTRA_CLIENT_SECRET`, `ENTRA_TENANT_ID` | — | Microsoft Entra ID application. **Required with `AUTH_MODE=entra`** (exit code 1 if one is missing); unused in `dev`. |
| `REDIRECT_URI` | — | Entra callback URL, e.g. `https://<host>/auth/callback`. `entra` only. |
| `LOCAL_DATABASE_DIR` | `database/` at the project root | Folder of the SQLite file `db_oceens.db`; a relative path is taken from the project root. With Docker Compose, see the warning above. |
| `LLM_API_KEY` | empty | Key of the default LLM provider (Ollama EPF). Empty: the application runs, summaries are unavailable. |
| `RUN_SUMMARIES_DAEMON` | empty | `1`/`true`/`yes`/`on`: Uvicorn starts the summaries daemon alongside itself. |

LLM providers you add yourself read their key from a variable you name (see below); that name must match `LLM_*` or `*_API_KEY`.

Generate a `SECRET_KEY` with `python -c "import secrets; print(secrets.token_urlsafe(32))"`. Anyone who knows it can forge an admin session.

> [!CAUTION]
> Never commit `.env`. It is listed in `.gitignore`, like the `*.db` files (`database/db_oceens.db`, `cache_llm.db`).

---

## Logging

Application logs use Python's standard `logging` module and the `uvicorn` logger, so that messages from the application, `auth.py` and `seed.py` share the format, colours and handlers the server has already set up.

Levels are used by severity:

| Level | Use |
|---|---|
| `DEBUG` | Detailed information for development and seeding. |
| `INFO` | Startup, shutdown and normal operations. |
| `WARNING` | An expected resource is missing, or a non-blocking situation. |
| `ERROR` / `EXCEPTION` | An operation failed; `logger.exception()` keeps the traceback. |
| `CRITICAL` | Required configuration is missing and prevents startup. |

Example:

```python
import logging

logger = logging.getLogger("uvicorn")

logger.info("Operation completed")

try:
    risky_operation()
except Exception:
    logger.exception("Operation failed")
```

New diagnostics should use the appropriate logger rather than `print()`. The application level is currently set to `DEBUG` in `core/dependencies.py`. Application logs go through the Uvicorn handler, usually to `stderr`; to capture them separately, redirect it, for example `2> error.log`.

---

## LLM providers

Summaries of free-text answers are generated by an LLM. The provider is **configurable from the interface** (`/backend/providers`, admin only), without touching the code. The default provider is **Ollama EPF** (`https://locallm.mde.epf.fr/ollama`, model `gemma4:26b`, key in `LLM_API_KEY`), created automatically at startup.

### Supported API types

| `api_type` | Covers |
|---|---|
| `ollama` | Ollama servers (local, EPF, third-party) |
| `openai` | OpenAI **and any OpenAI-compatible endpoint**: vLLM, Groq, Mistral, LM Studio… |
| `anthropic` | Claude API (Anthropic) |

### Security principle: no key in the database

The SQLite database is not encrypted and goes into backups. **No API key is stored in it.** The `llm_providers` table holds only the *name* of the environment variable (`api_key_env`, e.g. `OPENAI_API_KEY`); the value stays in `.env` and is resolved only at call time. That name is checked against an allow-list (`LLM_*` or `*_API_KEY`) so that it cannot point at a system secret (`SECRET_KEY`, `ENTRA_CLIENT_SECRET`…).

### Adding a provider

1. **Add the key to `.env`** under a conforming name (`LLM_*` or `*_API_KEY`), e.g. `OPENAI_API_KEY=sk-...`.
2. **Restart the summaries daemon**: it reads `.env` only at startup.
3. **Create the provider** in `/backend/providers` → *+ Nouveau fournisseur*: name, API type, base URL, the environment variable's name (`OPENAI_API_KEY`), and a default model. The **key present / absent** indicator confirms the variable is loaded. The **Tester** button checks that the URL and key answer, then sends a one-token generation to confirm the account can actually generate (see below).
4. **Link a prompt** to the provider: in `/backend/prompts`, a `<select>` chooses a prompt's provider. A prompt with no provider (`provider_id` NULL) falls back to Ollama EPF.

> [!NOTE]
> A provider referenced by at least one prompt cannot be deleted, so as not to break those prompts.

### Exhausted credit and other provider errors

Each provider reports its failures in its own format: exhausted credit is a `429 insufficient_quota` at OpenAI, but a `400 "Your credit balance is too low"` at Anthropic. `services/llm_client.py` normalises these responses into categories (`quota`, `rate_limit`, `auth`, `model`, `server`) and derives a readable message from them, in French, for example: *« ⚠️ Crédit ou quota épuisé chez le fournisseur… (fournisseur OpenAI, modèle gpt-4o-mini, HTTP 429) »*.

That message is written to `Summary.metadata_text` instead of the raw JSON, so it is visible from the interface when a summary fails. The provider's raw response stays in the daemon's logs for diagnosis.

> [!IMPORTANT]
> The **Tester** button does not stop at listing the models: at OpenAI as at Anthropic, `GET /v1/models` still answers perfectly with a zero balance. A one-token generation (negligible cost) is sent next: it is the only way to spot exhausted credit **before** launching a round of summaries.

---

## Cost of summaries

The cost of each summary is **measured, not estimated**. At generation time, the daemon records the token counts returned by the provider (`Summary.input_tokens`, `output_tokens`, `model_used`): it is the only chance to capture them, since no API lets you ask for them afterwards. The amount is then obtained by crossing those counts with the price list.

### Price list — `/backend/llm/prices`

Prices live in the database (table `llm_model_prices`), **in euros**, and are editable from the administration: no release is needed to follow a price change, or to cover a provider added locally. Providers publish in dollars per million tokens; a price entered in dollars is converted once, at the dollar → euro rate stored in the `settings` table (default `0.92`, editable), then stored in euros. Changing the rate later does not rewrite existing prices.

Pre-filled at startup (`seed_model_prices`, idempotent: a price corrected by hand is never overwritten):

| Model | Pricing |
|---|---|
| `claude-opus-5` | $5.00 in / $25.00 out per million tokens, converted to euros |
| `claude-sonnet-5` | $3.00 in / $15.00 out per million tokens, converted to euros |
| `claude-haiku-4-5` | $1.00 in / $5.00 out per million tokens, converted to euros |
| `gemma4:26b` (Ollama EPF, self-hosted) | A flat €0.02 to €0.05 per summary, all included (GPU, electricity, depreciation), no per-token price |

Other providers' prices (OpenAI, Mistral, Groq…) are **to be entered**: they are not guessed. A price specific to one provider wins over a generic price for the same model name.

### Where to see it

| Where | What |
|---|---|
| `/backend/llm/costs` | Overall cost, per survey and per model (admin) |
| 💰 button on a survey row | Cost of that survey's summaries |

### What is not priced

A summary cannot be priced when its counts are missing (generated before this feature, or a provider that does not expose them) or when its model has no recorded price. It is then **counted separately**, never estimated nor set to zero: an invented amount would do more harm than a missing one, since it would be displayed with the authority of a real amount. The screens say explicitly when a total is partial.

> [!IMPORTANT]
> Tracking starts when the feature went live: summaries generated before it have no counts in the database and cannot be priced retroactively.

---

## Project structure

```
OceENS/
├── main.py                       # FastAPI factory, middlewares, router assembly
├── sondage_loader.py             # Loads a complete survey for export
├── survey_loader_from_xlsx.py    # Imports surveys from an Excel file
├── summaries_generator_daemon.py # Asynchronous LLM summary processing (separate process)
├── launch.sh                     # Production launcher on the school's server, without Docker
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Application image
├── docker-compose.yaml           # Local run with Docker
├── .env.example                  # Configuration reference, copied to .env
├── .env                          # Local configuration (⚠️ never committed)
├── CONTEXT.md                    # Domain language
├── AGENTS.md, CLAUDE.md          # Instructions for coding agents
│
├── core/                         # Low-level access and security
│   ├── auth.py                   #   Entra ID authentication (login, logout, callback) and development login
│   ├── database.py               #   SQLite engine and SessionDep dependency
│   ├── security.py               #   Roles, scopes, access control
│   ├── dependencies.py           #   Shared Jinja templates and logger
│   └── seed.py                   #   Initial data and program synchronisation
│
├── models/                       # SQLModel schema, one file per table
│   ├── __init__.py               #   Re-exports every class (see its docstring)
│   └── User.py, Survey.py, ...
│
├── routers/                      # Routes, split by business domain
│   ├── pages.py                  #   Home page and per-role dashboards
│   ├── surveys.py                #   Surveys: CRUD, status, export, visualisation
│   ├── students.py               #   Enrolling students in a survey
│   ├── users.py                  #   User role management
│   ├── summaries.py              #   Triggering LLM summaries
│   ├── prompts.py                #   Prompt administration
│   ├── survey_templates.py       #   Survey template administration
│   ├── sections_questions.py     #   Section and question administration
│   └── llm/                      #   LLM administration
│       ├── _access.py            #     Shared access control of the LLM screens
│       ├── providers.py          #     LLM providers (CRUD + connection test)
│       ├── prices.py             #     Price list per model
│       └── costs.py              #     Overall and per-survey cost
│
├── services/                     # Business logic
│   ├── helpers.py                #   Navigation, statistics, filters, sorting
│   ├── visualisation_data.py     #   Aggregations and visualisation context
│   ├── llm_client.py             #   Multi-provider LLM client (ollama/openai/anthropic)
│   ├── llm_costs.py              #   Summary cost (measured tokens × price list)
│   ├── settings_store.py         #   Application settings (dollar → euro rate)
│   └── export_csv.py             #   CSV export of the answers
│
├── import/                       # Seed data: Program_list.csv, seed_answers*.csv
├── database/                     # SQLite database, created at startup (ignored by Git)
│   └── db_oceens.db
│
├── docs/
│   ├── smoke-test.md             # Manual smoke test: how to run and check the project
│   ├── adr/                      # Architecture Decision Records
│   └── agents/                   # Issue tracker, triage labels, domain docs for agents
│
├── llm-utils/                    # LLM tooling outside the application
│   └── README.md                 # (cost tracking moved into the app, see above)
│
├── templates/                    # Jinja2 HTML templates
│   ├── index.html                #   Home / login page
│   ├── dashboard/                #   Per-role dashboards, survey, survey creation, visualisation, teacher analytics
│   ├── backend/                  #   Administration pages (admin only): prompts, llm/ (providers, prices, costs)
│   └── template_parts/           #   Fragments shared between dashboards
│
├── static/                       # css/, js/, img/
│
└── .venv/                        # Python virtual environment (not committed)
```

---

## Authentication (OAuth 2.0)

With `AUTH_MODE=entra`, authentication relies on **Microsoft Entra ID** through the MSAL library:

```
1. The user clicks "Se connecter"
   → FastAPI generates a random state (UUID, CSRF protection)
   → Redirect to Microsoft's login page

2. The user authenticates with Microsoft
   → Microsoft redirects to /auth/callback with a code + state

3. The server exchanges the code for an access token
   → User details fetched through Microsoft Graph
   → The database gives the user's role(s) and their scope
   → Session created: {name, email, roles}
   → Redirect to the matching dashboard

4. On logout (/logout)
   → Session and cookies removed
   → Logout on Microsoft's side
   → Back to the home page
```

Authentication alone authorises no business action: every route then checks the role and scope (program or campus) through `require_roles()` and its helpers.

---

## Development login

To work on a fork without an Azure application, the **development login** (*connexion de développement*) lets you log in as any user, with no proof of identity. It must **never** be used in production.

| Variable | Role |
|---|---|
| `AUTH_MODE` | `entra` (default) or `dev`, case- and space-insensitive. Any other value stops the application at startup. In `dev`, the `ENTRA_*` variables are not needed. |
| `DEV_LOGIN_KEY` | Optional, `dev` only. If set, every login must provide it (field `key`), otherwise `401`. If not set, login is open. Ignored, with a warning, in `entra`. |
| `SECRET_KEY` | Optional in `dev`: if missing, a random key is drawn at every start (with a warning) and sessions are lost on restart. Required in `entra`. |
| `ALLOWED_DOMAINS` | Also applies in `dev` (`403` for another domain); defaults to `epf.fr,epfedu.fr`. |

In `dev` mode, the session cookie is no longer restricted to HTTPS (`http://localhost` works), `/login` redirects to `/dev/login`, `/auth/callback` does not exist, and `/logout` clears the session and sends you back to `/`. A warning is logged at startup. A red banner, which cannot be closed, is shown at the top of every page that includes the shared header: it shows the logged-in address, offers « Changer d'utilisateur » (`/dev/login`), and says « accès ouvert à tous » when `DEV_LOGIN_KEY` is not set.

`POST /dev/login` expects a form with `email`, `name` (optional) and `key` (if `DEV_LOGIN_KEY` is set). The user is fetched or created as on return from Entra: an unknown e-mail becomes a new student. Without `name`, the displayed name is built from the e-mail (`bob.leponge@epfedu.fr` → "Bob Leponge"). A new login replaces the session: that is how you switch users.

In a browser, `GET /dev/login` lists the database's users, grouped by role name without scope (a user with no role appears under `student`, a user with several roles under each of them). A click logs in as that user; a free field lets you use another address, with an optional name. If `DEV_LOGIN_KEY` is set, a single key field is shown and used for every login on the page; the key is never stored in the session. Come back to this page to switch users.

```bash
AUTH_MODE=dev DEV_LOGIN_KEY=my-key uvicorn main:app

# Log in as the seed's admin; -c saves the session cookie
curl -i -c cookies.txt \
  -d email=antoine.gademer@epf.fr -d key=my-key \
  http://localhost:8000/dev/login

# Reuse the cookie (-b) for the next requests
curl -b cookies.txt -c cookies.txt -L http://localhost:8000/
```

> [!WARNING]
> `dev` mode does not require `SECRET_KEY`. Without it, the key is random and unknown; but if a known `SECRET_KEY` is set (shared, copied from an example…), anyone who knows it can forge a session cookie and bypass `DEV_LOGIN_KEY`: `dev` mode accepts it, since it is only meant for local use.

---

## Notable features

### Teacher analytics

The route `/dashboard/teachers/analytics` (`campus_manager`, `program_manager`) aggregates the satisfaction score per `(teacher, survey)` from the `QCU_Satisfaction` answers that carry an `Answer.teacher` (ME sections). Teachers are sorted with `teacher_sort_key()`, ignoring case and accents, and the list can be filtered by school year, semester, program and teacher.

### Teacher filter in the visualisation

A client-side selector filters the visualisation without reloading: only the chosen teacher's modules remain, and the Campus and Formation sections are hidden. The page reads `?teacher=<name>` on load to pre-filter itself; links from the analytics page pass that parameter, so a click on a teacher's score opens their view directly.

### Surveys imported from Excel

Surveys loaded by `survey_loader_from_xlsx.py` have no `QCU_Attendance` question: `services/visualisation_data.py` then uses `satisfaction_responses_count` as the fallback denominator for the teacher score. Teacher names are normalised with `.title()` on import and on aggregation, to merge case variants (`"GADEMER Antoine"` and `"Gademer Antoine"` are one entry). Questions are sorted by `question_id` in the template, which puts the charts before the free-text answers (*verbatims*) whatever the insertion order.

### Campus manager scope

The `campus_manager` dashboard shows only closed surveys with at least one respondent. The questionnaire link and QR code are hidden there (`can_view_survey_link=False`): this role reads results without distributing surveys. The guard `{% if can_view_survey_link | default(true) %}` leaves the other dashboards unchanged.

### Removing orphan students

When a survey is deleted, students no longer attached to **any other** survey are deleted too, so that unused accounts do not pile up (`services/helpers.py`, `_delete_orphan_students`). A safeguard protects users with a privileged role (`admin`, `program_manager`, `facilitator`, `campus_manager`): a teacher or manager who answered a survey is never deleted.

### Adding a user by e-mail

The « Utilisateurs » tab of the administrator dashboard has a **« + Ajouter un utilisateur »** button: an e-mail is enough to create the account, with the `student` role by default (`POST /api/users`, admin only). The e-mail is validated (format and allowed domain) and duplicates are refused.

---

## Deployment checklist

- [ ] `.env` created with the real Azure credentials and a dedicated `SECRET_KEY` (required outside `AUTH_MODE=dev`, otherwise the application refuses to start)
- [ ] `AUTH_MODE` unset or `entra`
- [ ] Valid SSL certificate (Let's Encrypt or equivalent)
- [ ] `https_only=True` on the SessionMiddleware (automatic outside `AUTH_MODE=dev`)
- [ ] Database present (`database/db_oceens.db`) or Docker volume mounted
- [ ] Environment variables secured, including `LLM_API_KEY`
- [ ] **Docker Compose**: `.env` loaded through `env_file`, never copied into the image; `LOCAL_DATABASE_DIR` left empty (see [Docker details](#docker-details))
- [ ] `summaries_generator_daemon.py` running if LLM summaries are used

---

## Before contributing

The repository has no automated test suite and no CI yet. Before proposing a change that touches startup, configuration, dependencies or the container, run **[`docs/smoke-test.md`](docs/smoke-test.md)**: its static checks, then the steps your change concerns. Then test the affected routes by hand on a throwaway SQLite database (never a copy of production), with the relevant roles and survey statuses.

---

## Resources

- [FastAPI](https://fastapi.tiangolo.com/)
- [FastAPI and Uvicorn logging guide](https://apitally.io/blog/fastapi-logging-guide)
- [MSAL Python](https://github.com/AzureAD/microsoft-authentication-library-for-python)
- [Microsoft Graph](https://learn.microsoft.com/en-us/graph/)
- [Jinja2](https://jinja.palletsprojects.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [SQLModel](https://sqlmodel.tiangolo.com/)
- [Pandas](https://pandas.pydata.org/)

---

**OcéEns team** — EPF
