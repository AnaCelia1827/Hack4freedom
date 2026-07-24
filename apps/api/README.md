# Bluejet API foundation

Run from this directory with a Python environment containing `requirements.txt`:

```bash
pip install -r requirements.txt
PYTHONPATH=. DATABASE_URL=postgresql+psycopg://runtime-login:senha@127.0.0.1:5432/bluejet \
  CORS_ORIGINS=http://localhost:5173 flask --app wsgi run --host 127.0.0.1 --port 5000
```

Without `DATABASE_URL`, readiness reports `database=not-configured` for the
legacy in-memory development mode. With `DATABASE_URL`, `/health/ready` checks
PostgreSQL and returns `503` when the connection is unavailable. Payment
obligation reads, payout attempts, provider state, reconciliation, receipts and
the donor core use PostgreSQL when it is configured. In local development,
`LIGHTNING_MODE=SANDBOX` accepts only the explicit non-BOLT11 token
`lnsbx:network:amount:expires:payment_hash`. The complete token is hashed at the
HTTP boundary and is never persisted or returned. This mode does not prove a
real Lightning payment.

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

Mantenha a connection string somente em `apps/api/.env.local`, que é ignorado
pelo Git, carregue-o no processo e use o driver Psycopg 3:

```bash
set -a
. apps/api/.env.local
set +a
```

```dotenv
DATABASE_URL='postgresql+psycopg://usuario:senha@host:5432/postgres?sslmode=require'
```

Com PostgreSQL, papéis administrativos são lidos de `user_roles` e vínculos de
organização de `company_memberships`. `BLUEJET_ADMIN_PUBKEYS` permanece apenas
como bootstrap do modo local sem banco e não substitui o RBAC persistido.

O seed de staging/local exige a conexão do migration owner e aceita somente
pubkeys públicas hexadecimais:

```bash
PYTHONPATH=apps/api DATABASE_URL='postgresql+psycopg://migration-owner/...' \
  python -m bluejet_api.seed_roles \
  --participant-pubkey '<PARTICIPANT_64_HEX>' \
  --organization-pubkey '<ORGANIZATION_64_HEX>' \
  --admin-reviewer-pubkey '<ADMIN_REVIEWER_64_HEX>' \
  --donor-pubkey '<DONOR_64_HEX>' \
  --company-id '<COMPANY_ID>'
```

`--donor-pubkey` is optional. `DONOR` remains separate from `ORGANIZATION`;
both are backend grants and cannot be selected by a client payload.

The local donor endpoints persist only `SANDBOX` contributions. They require
integer sats, explicit terms acceptance and allocation percentages in basis
points totaling exactly `10000`. Impact funds and liquidity principal are
credited to separate ledger accounts. No Lightning, Fiat, Pix, wallet or
exchange-rate provider is called by this slice.

Participante e administração usam desafios Nostr, audiences e cookies
separados. Configure `NOSTR_AUTH_AUDIENCE` e `ADMIN_NOSTR_AUTH_AUDIENCE` com
as URLs HTTPS exatas em produção. Uma sessão `bluejet_session` não autoriza
rotas administrativas; elas exigem `bluejet_admin_session` e papel `ADMIN` ou
`REVIEWER` persistido, conforme a rota. Clientes nunca podem enviar `role`,
`roles` ou `session_scope` durante o login.

`CORS_ORIGINS` aceita uma lista separada por vírgulas e reflete somente origens
exatas. Wildcard é recusado. Em produção, todas as origens precisam usar HTTPS;
o cookie de sessão é `HttpOnly`, `SameSite=Lax` e `Secure`.
