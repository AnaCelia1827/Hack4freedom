---
sidebar_position: 1
sidebar_label: Arquitetura Técnica
---

# Arquitetura técnica

## Estado documentado

Esta página descreve a implementação encontrada na branch
[`bluejet-development`](https://github.com/AnaCelia1827/Hack4freedom/tree/bluejet-development),
no commit `9d08c4c`, analisado em 24 de julho de 2026. O código da aplicação ainda
não está integrado à branch principal da documentação.

Para evitar que uma demonstração seja confundida com operação em produção, os
componentes são classificados assim:

| Estado | Significado |
|---|---|
| **Implementado** | Existe código executável e verificável no repositório |
| **Parcial** | O fluxo existe, mas depende de memória, validação simplificada ou integração pendente |
| **Mock** | Simula comportamento sem movimentar dinheiro ou publicar em rede externa |
| **Planejado** | Está definido na arquitetura, mas não há implementação funcional |

## Visão geral

A solução é um monólito modular composto por uma SPA React e uma API Flask. A
API concentra regras de capacitação, tarefas, revisão e pagamentos. PostgreSQL
já protege parte do núcleo financeiro; os demais domínios ainda usam memória do
processo.

```text
Navegador
  └─ SPA React/Vite
       ├─ signer NIP-07 ──────────────── Parcial
       └─ HTTP + cookie de sessão
            └─ API Flask
                 ├─ autenticação e onboarding ─ Memória
                 ├─ capacitação ────────────── Memória
                 ├─ tarefas e revisão ──────── Memória
                 ├─ comunidade ─────────────── Memória
                 └─ núcleo financeiro
                      ├─ obrigações e tentativas ─ PostgreSQL
                      ├─ ledger e outbox ───────── PostgreSQL
                      └─ pagamento Lightning ───── Mock
```

## Componentes e maturidade

| Componente | Tecnologia | Estado atual |
|---|---|---|
| Cliente web | React, TypeScript e Vite | **Implementado** como SPA responsiva |
| API | Python 3.12 e Flask 3 | **Implementado** |
| Contrato HTTP | OpenAPI 3.1 | **Parcial**: não cobre todas as rotas existentes |
| Sessão | Cookie `HttpOnly` e armazenamento em memória | **Parcial** |
| Assinatura Nostr | Extensão NIP-07 no navegador | **Parcial**: backend ainda não verifica a assinatura criptograficamente |
| Domínios de aprendizagem e trabalho | Serviços Python em memória | **Parcial** |
| Persistência financeira | PostgreSQL 16, SQLAlchemy e Alembic | **Implementado** para obrigações, tentativas, ledger e outbox |
| Upload privado | Registro de metadados | **Mock**: arquivo não é armazenado |
| Lightning | Invoice informada pela participante | **Mock**: sem Breez, CLN ou liquidação real |
| Badges e comunidade Nostr | Objetos e eventos locais | **Mock**: sem publicação em relay |
| Conversão Pix | Hodle | **Planejado** |

## Estrutura do código

```text
apps/
├─ api/
│  ├─ bluejet_api/
│  │  ├─ app.py          # rotas e composição da aplicação
│  │  ├─ auth.py         # desafios e sessões Nostr
│  │  ├─ learning.py     # cursos, quiz e evidências
│  │  ├─ work.py         # tarefas, reservas e entregas
│  │  ├─ finance.py      # revisão e finanças em memória
│  │  ├─ community.py    # feed e oportunidades
│  │  └─ database.py     # persistência financeira PostgreSQL
│  └─ tests/
└─ web/
   ├─ src/main.tsx       # SPA, rotas e telas
   ├─ src/*.css          # tokens, layout e responsividade
   └─ public/_redirects  # suporte a deep links
migrations/              # migrações Alembic
openapi/openapi.yaml     # contrato HTTP
docs/adr/                # decisões arquiteturais
```

## Fluxo principal do MVP

```text
login NIP-07
  → capacitação e quiz
  → evidência de habilidade
  → tarefa financiada e publicada
  → reserva exclusiva por 60 minutos
  → entrega privada
  → revisão administrativa
  → obrigação de pagamento
  → tentativa idempotente
  → outbox de despacho
  → liquidação e recibo
```

O fluxo funciona de ponta a ponta apenas em memória e modo `MOCK`. Quando
`DATABASE_URL` está configurada, a obrigação, a tentativa e o evento de outbox
são persistidos, mas o worker de despacho e a reconciliação PostgreSQL ainda não
foram implementados.

## Decisões técnicas relevantes

- **Monólito modular:** reduz o custo operacional do MVP e mantém as regras
  transacionais próximas.
- **PostgreSQL no núcleo financeiro:** permite locks, restrições e testes reais
  de concorrência. A referência anterior a SQLite representa uma decisão
  superada pela implementação atual.
- **Outbox transacional:** a tentativa de pagamento e a solicitação de despacho
  são gravadas na mesma transação.
- **Ledger de partidas dobradas:** débitos e créditos precisam fechar e as
  transações são imutáveis após a criação.
- **Modos explícitos:** toda operação financeira deve informar `MOCK`,
  `SANDBOX` ou `REAL`.
- **Reserva separada de funding:** a expiração da vaga não devolve nem altera
  silenciosamente os recursos reservados para a tarefa.

## Execução local

Pré-requisitos: Node.js 20+, Python 3.12+ e PostgreSQL 16 para testar
persistência.

```powershell
# API em modo de memória
Set-Location apps/api
python -m pip install -r requirements.txt
$env:PYTHONPATH = "."
python -m flask --app wsgi run

# Cliente web, em outro terminal
Set-Location apps/web
npm ci
npm run dev
```

Por padrão, o frontend chama `http://localhost:5000`. O endereço pode ser
alterado com `VITE_API_URL`. A configuração Vite atual não possui o proxy
`/api` mencionado no README da aplicação.

As instruções de banco, testes e variáveis estão em
[Backend e API](backend.md). Rotas e estado do cliente estão em
[Frontend](frontend.md).

## Qualidade e entrega

O workflow `Qualidade` executa três jobs em pushes e pull requests:

1. build do Docusaurus;
2. migrações e testes da API contra PostgreSQL 16, com usuários distintos de
   migração e runtime;
3. compilação TypeScript e build Vite.

O pipeline configura a verificação, mas o resultado de uma execução específica
deve ser consultado no
[GitHub Actions](https://github.com/AnaCelia1827/Hack4freedom/actions).

## Limites antes de produção

O MVP ainda não deve operar recursos reais. Os principais bloqueios são:

- verificação criptográfica Nostr ausente;
- autorização incompleta em algumas rotas financeiras e administrativas;
- domínios e sessões voláteis;
- ausência de armazenamento privado de arquivos;
- ausência de worker, gateway Lightning e reconciliação persistente;
- invoice sem validação BOLT11;
- ausência de testes automatizados do frontend e de testes ponta a ponta.

O detalhamento e a ordem de correção estão em [Segurança](seguranca.md).
