# Bluejet / Hack4Freedom

Este repositório contém a API Flask, o cliente React/Vite, as migrations
PostgreSQL e a documentação do projeto.

## Aplicação local integrada

Requisitos: Python 3.12, Node.js 20 e PostgreSQL 16. A partir da raiz:

```bash
python -m pip install -r apps/api/requirements.txt pytest
npm ci --prefix apps/web
```

Prepare um banco vazio e aplique as migrations com a credencial de owner:

```bash
PYTHONPATH=apps/api \
DATABASE_URL=postgresql+psycopg://migration-owner:senha@127.0.0.1:5432/bluejet \
python -m alembic -c apps/api/alembic.ini upgrade head
```

Inicie a API com a credencial de runtime, sem privilégios de DDL, no primeiro
terminal:

```bash
PYTHONPATH=apps/api \
DATABASE_URL=postgresql+psycopg://runtime-login:senha@127.0.0.1:5432/bluejet \
CORS_ORIGINS=http://localhost:5173 \
flask --app apps/api/wsgi.py run --host 127.0.0.1 --port 5000
```

Inicie o cliente no segundo terminal:

```bash
npm run dev --prefix apps/web
```

Acesse `http://localhost:5173`. O navegador chama `/api`; o proxy local do
Vite encaminha a chamada para `http://127.0.0.1:5000`. Verifique a API em
`http://127.0.0.1:5000/health/ready`.

Em produção, use HTTPS, configure `CORS_ORIGINS` com a origem exata do cliente
e mantenha `/api` no mesmo site por proxy reverso. Não use `*` com cookies.

## Documentação Hack4Freedom

Site de documentação em Docusaurus, organizado a partir dos documentos Markdown do projeto.

## Desenvolvimento local

Requisitos: Node.js 20 ou superior.

```bash
npm install
npm run docs:start
```

O servidor local abre a documentação em `http://localhost:3000/Hack4freedom/`.

## Validação de produção

```bash
npm run docs:build
npm run docs:serve
```

O build estático é gerado em `build/`.

## Publicação

O workflow `deploy-docs.yml` publica automaticamente no GitHub Pages quando houver um push na branch `main`. No GitHub, configure **Settings → Pages → Source** como **GitHub Actions**.

Endereço esperado: `https://anacelia1827.github.io/Hack4freedom/`.

## Estrutura

- `contexto.md`: visão geral;
- `docs/`: conteúdo da documentação;
- `sidebars.js`: ordem e categorias do menu lateral;
- `docusaurus.config.js`: domínio, navegação, rodapé e tema;
- `src/css/custom.css`: identidade visual;
- `static/img/`: logo, favicon e cartão social.
