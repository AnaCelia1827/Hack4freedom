# Bluejet API foundation

Run from this directory with a Python environment containing `requirements.txt`:

```bash
pip install -r requirements.txt
PYTHONPATH=. flask --app wsgi run
```

Without `DATABASE_URL`, readiness reports `database=not-configured` for the
legacy in-memory development mode. With `DATABASE_URL`, `/health/ready` checks
PostgreSQL and returns `503` when the connection is unavailable. Payment
obligation reads and payout-attempt creation also use PostgreSQL when it is
configured; the invoice is validated at the HTTP boundary and is not persisted
by this foundation slice.

Apply migrations from the repository root:

```bash
PYTHONPATH=apps/api DATABASE_URL=postgresql+psycopg://... \
  python -m alembic -c apps/api/alembic.ini upgrade head
```

PostgreSQL integration tests require an isolated database:

```bash
PYTHONPATH=apps/api \
  TEST_MIGRATION_DATABASE_URL=postgresql+psycopg://migration-owner/... \
  TEST_DATABASE_URL=postgresql+psycopg://runtime-login/... \
  python -m pytest apps/api/tests
```

Migrations são aplicadas pelo owner. A API usa um login separado que herda
`bluejet_runtime`, sem ownership, DDL, DELETE ou TRUNCATE. O tempo máximo de
espera do lock idempotente é configurável por `DATABASE_LOCK_TIMEOUT_MS` e usa
1000 ms por padrão.
## Configuração local

Copie `.env.example` para o ambiente da API e defina `BLUEJET_ADMIN_PUBKEYS`
com os pubkeys Nostr autorizados para publicar tarefas e revisar entregas.
Sem essa configuração, as rotas administrativas respondem `403` por padrão.
