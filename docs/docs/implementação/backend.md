---
sidebar_position: 3
sidebar_label: Backend e API
---

# Backend e API

## Escopo implementado

O backend é uma API Flask organizada como monólito modular. A fábrica
`create_app` instancia os serviços, configura o acesso ao PostgreSQL quando
disponível e registra as rotas HTTP.

| Domínio | Capacidades existentes | Persistência |
|---|---|---|
| Identidade | desafio, sessão, consulta da pessoa autenticada e logout | Memória |
| Onboarding | rascunho, atualização e conclusão | Memória |
| Capacitação | cursos, aulas, atividades, notas, quiz e evidência | Memória |
| Trabalho | empresas, tarefas, funding, reserva, candidatura e entrega | Memória |
| Revisão | fila, aprovação, correção e rejeição | Memória |
| Financeiro | obrigação, tentativa, ledger e outbox | PostgreSQL quando configurado |
| Comunidade | feed, posts, comentários, reações e denúncias | Memória |
| Impacto e carteira | agregados demonstrativos | Mock em memória |

O contrato disponível em
[`openapi/openapi.yaml`](https://github.com/AnaCelia1827/Hack4freedom/blob/bluejet-development/openapi/openapi.yaml)
documenta os fluxos principais, mas algumas rotas adicionadas ao código ainda
não aparecem nele. Antes de publicar uma API estável, código e contrato devem
ser reconciliados.

## Organização interna

| Módulo | Responsabilidade |
|---|---|
| `app.py` | composição da aplicação, autenticação de rotas e respostas HTTP |
| `auth.py` | desafios de uso único e sessões |
| `learning.py` | curso, matrícula, avaliação e evidência de habilidade |
| `work.py` | tarefas, funding, reservas, candidaturas e submissões |
| `finance.py` | revisão, pagamentos e recibos do modo em memória |
| `community.py` | comunidade e oportunidades externas |
| `database.py` | modelos SQLAlchemy e operações financeiras transacionais |

Essa divisão já cria limites de domínio, embora as rotas e a injeção de
dependências ainda estejam concentradas em `app.py`.

## Autenticação e perfis

O cliente solicita um desafio, assina um evento com uma extensão NIP-07 e envia
`challenge`, `pubkey`, `signature` e `event`. O servidor impede reutilização e
expiração do desafio e cria o cookie `bluejet_session`.

O cookie é `HttpOnly`, `SameSite=Lax` e recebe `Secure` em produção. A sessão
dura 12 horas no serviço em memória. O fluxo é apenas **parcial**, pois
`auth.py` compara o envelope recebido, mas ainda não valida o ID nem a assinatura
Schnorr do evento Nostr.

Existem dois níveis de acesso:

- **participante:** qualquer sessão válida;
- **administrador:** pubkey presente em `BLUEJET_ADMIN_PUBKEYS`.

Sem uma lista de administradores configurada, as rotas protegidas de
administração retornam `403`, comportamento seguro por padrão.

## Regras de trabalho

Uma tarefa só pode ser publicada quando `funded_sats` for igual a
`reward_sats`. A participante precisa possuir evidência de capacitação para
reservá-la.

A reserva da vaga:

- pertence a uma única participante;
- dura 60 minutos;
- bloqueia outra reserva ativa para a mesma tarefa;
- expira sem modificar o funding da tarefa.

O conteúdo de uma submissão é usado apenas para calcular um SHA-256. O backend
não persiste os bytes do arquivo; portanto, o upload atual deve ser tratado como
metadado de demonstração, não como armazenamento privado.

## Núcleo financeiro persistente

Com `DATABASE_URL`, cinco estruturas sustentam a base financeira:

| Estrutura | Função |
|---|---|
| `payment_obligations` | valor devido por uma atribuição aprovada |
| `payout_attempts` | histórico das tentativas de pagamento |
| `ledger_transactions` | cabeçalho imutável do lançamento |
| `ledger_entries` | débitos e créditos em satoshis |
| `outbox_events` | efeitos externos a despachar |

### Estados

```text
PaymentObligation: OPEN → CLEARING → SETTLED

PayoutAttempt:
CREATED → VALIDATED → PROCESSING → SETTLED
                            ├────→ FAILED
                            ├────→ EXPIRED
                            └────→ AMBIGUOUS
```

O código persistente cria a tentativa diretamente em `VALIDATED`, muda a
obrigação para `CLEARING` e grava `PayoutDispatchRequested` na mesma transação.
Não existe worker que consuma esse evento atualmente.

### Invariantes aplicadas

- valor em satoshis deve ser inteiro e positivo;
- uma atribuição gera no máximo uma obrigação;
- uma obrigação tem no máximo uma tentativa ativa;
- a chave de idempotência é única globalmente;
- a mesma chave devolve a tentativa já criada;
- locks advisory e `SELECT FOR UPDATE` protegem concorrência;
- timeout de lock é limitado por `DATABASE_LOCK_TIMEOUT_MS`;
- débitos e créditos do ledger precisam ter o mesmo total;
- ledger e auditoria rejeitam update, delete, truncate e entradas tardias;
- migrações são progressivas: correções financeiras devem usar nova migração,
  não downgrade destrutivo.

O usuário de runtime herda o papel `bluejet_runtime`, sem ownership, DDL,
`DELETE` ou `TRUNCATE`. O usuário de migração permanece separado.

## Configuração

| Variável | Uso | Padrão |
|---|---|---|
| `BLUEJET_ENV` | ambiente; ativa cookie `Secure` em `production` | `development` |
| `DATABASE_URL` | conexão SQLAlchemy com PostgreSQL | modo em memória |
| `DATABASE_LOCK_TIMEOUT_MS` | espera máxima do lock idempotente | `1000` |
| `CORS_ORIGINS` | origens permitidas pretendidas | `http://localhost:3000` |
| `BLUEJET_ADMIN_PUBKEYS` | pubkeys administrativas separadas por vírgula | nenhuma |

`DATABASE_URL` é obrigatória quando `BLUEJET_ENV=production`. A variável
`CORS_ORIGINS` é lida, mas ainda não está ligada a um middleware CORS.

## Banco e migrações

No PowerShell, a partir da raiz da branch de desenvolvimento:

```powershell
$env:PYTHONPATH = "apps/api"
$env:DATABASE_URL = "postgresql+psycopg://usuario:senha@localhost:5432/bluejet"
python -m alembic -c apps/api/alembic.ini upgrade head
```

A aplicação deve usar uma credencial de runtime diferente da credencial que
executa a migração.

## Execução e testes

```powershell
Set-Location apps/api
python -m pip install -r requirements.txt
$env:PYTHONPATH = "."
python -m flask --app wsgi run
```

Health checks:

- `GET /health/live`: processo Flask ativo;
- `GET /health/ready`: PostgreSQL pronto ou `database=not-configured` em
  desenvolvimento.

Testes unitários podem ser executados com:

```powershell
$env:PYTHONPATH = "."
python -m pytest tests -q
```

Os testes PostgreSQL exigem `TEST_MIGRATION_DATABASE_URL` e
`TEST_DATABASE_URL`. Eles verificam reinício, privilégios mínimos, concorrência,
idempotência, atomicidade do outbox e imutabilidade do ledger.

## Pendências conhecidas

- persistir sessões, onboarding, aprendizagem, trabalho e comunidade;
- dividir `app.py` em blueprints e serviços injetáveis;
- verificar eventos Nostr criptograficamente;
- completar autorização por propriedade dos recursos;
- validar BOLT11, despachar o pagamento e reconciliar o resultado;
- armazenar e inspecionar arquivos reais em serviço privado;
- padronizar erros e validar payloads por schema;
- implementar CORS, limitação de requisições e proteção CSRF;
- manter OpenAPI sincronizado com todas as rotas.
