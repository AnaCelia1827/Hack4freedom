# Bluejet API foundation

Run from this directory with a Python environment containing `requirements.txt`:

```bash
pip install -r requirements.txt
PYTHONPATH=. flask --app wsgi run
```

The readiness endpoint remains conservative until PostgreSQL is configured.
## Configuração local

Copie `.env.example` para o ambiente da API e defina `BLUEJET_ADMIN_PUBKEYS`
com os pubkeys Nostr autorizados para publicar tarefas e revisar entregas.
Sem essa configuração, as rotas administrativas respondem `403` por padrão.
