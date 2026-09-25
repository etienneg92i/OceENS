FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && rm -rf /var/lib/apt/lists/*

# uv installe les dépendances depuis uv.lock, avec l'interpréteur de l'image
RUN pip install --no-cache-dir uv==0.11.7
ENV UV_PYTHON_DOWNLOADS=never UV_LINK_MODE=copy

# Dépendances d'abord (couche mise en cache tant que le lockfile ne change pas)
COPY pyproject.toml uv.lock .python-version README.md ./
RUN uv sync --locked --no-dev --no-install-project

# Puis le paquet oceens lui-même (src/oceens/ : code, templates, static, import)
COPY src ./src
RUN uv sync --locked --no-dev

ENV PATH="/app/.venv/bin:$PATH"

# La base SQLite vit hors du paquet : monter /app/database comme volume pour la
# persister entre les redémarrages.
ENV LOCAL_DATABASE_DIR=/app/database

# Le fichier .env ne doit PAS être copié dans l'image : fournir les secrets via
# --env-file .env au lancement (docker run) ou via env_file (docker compose).

CMD ["uvicorn", "oceens.main:app", "--host", "0.0.0.0", "--port", "8000"]
