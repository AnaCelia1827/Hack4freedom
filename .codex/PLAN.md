# 1. Resumo executivo

- Produto: Bluejet, plataforma que conecta capacitação, trabalho real, reputação profissional e pagamento Lightning para mulheres.
- Objetivo do MVP: demonstrar o caminho aprender → comprovar → trabalhar → receber → construir reputação, sem expor chaves privadas e sem misturar impacto real com simulação.
- Caminho crítico: login Nostr, quiz com nota mínima de 80%, `SkillEvidence`, `PaidTask` financiada, reserva exclusiva, entrega privada, revisão humana, obrigação imutável, invoice BOLT11 exata, pagamento real, reconciliação e recibo.
- Escopo Must have adicional: perfil Doador descrito nos requisitos atuais, painel de oportunidades com dois tipos e comunidade Nostr mínima.
- Estratégia: API REST contract-first, monólito modular Flask, PostgreSQL, ledger de partidas dobradas, outbox/inbox transacional, worker assíncrono e integrações por ports and adapters.
- Resultado esperado: cenário reproduzível, verificável e executável em mobile, com no máximo um payout ativo por obrigação.

# 2. Diagnóstico do repositório

- Raiz Git: `/home/lorena/Hack4freedom`; branch `main` sincronizada com `origin/main` no início desta correção.
- Estado: `.codex/` não rastreado; nenhum código de produto existente.
- Stack encontrada: Docusaurus 3.9.1, React 19, JavaScript, CSS, npm e Node ≥20.
- CI existente: build e deploy do site de documentação no GitHub Pages.
- Reutilizável: documentação em `docs/`, narrativa financeira/Lightning, assets, CSS do site e invariantes em `.codex/AGENTS.md`.
- Ausente: backend, aplicação web do produto, OpenAPI, banco, migrações, worker, ledger, storage privado, Docker, testes de produto, E2E e observabilidade.
- Build documental atual: `npm run docs:build` depende de instalação; a auditoria anterior encontrou `docusaurus: command not found`.
- Figma: telas desktop parciais, um mobile incompleto, ausência de variables/styles compartilhados e mistura de RESILIENCE, EmpowerHer, PT/EN, score, “Z”, sats, BRL e USD.
- Riscos: prazo curto, escopo atual de Doador amplo, integração CLN real, experiência Breez no browser, conteúdo público no Nostr e concorrência financeira.

# 3. Decisões congeladas

| Decisão | Escolha | Justificativa | Registro |
|---|---|---|---|
| Marca | Bluejet | Elimina RESILIENCE/EmpowerHer | PLAN/Fase 0 |
| Idioma | Português do Brasil | Remove mistura PT/EN | PLAN/Fase 0 |
| Backend | Python 3.12, Flask modular, SQLAlchemy 2 | Baseline arquitetural | Fase 1 |
| Banco | PostgreSQL | Locks, índices parciais, ledger e outbox | Fase 1 |
| Frontend | React, Vite e TypeScript | Não existe app de produto | Fase 9 |
| Estilo | CSS Modules e tokens CSS | Tailwind não existe no projeto | Fase 9 |
| Fonte visual canônica | Plugin/app Figma conectado ao Codex | ADR-003; screenshots são somente validação | Fase 9 |
| Moeda contratual | Sats inteiros | BOLT11 e obrigação exatas | RN-009 |
| BRL | Centavos inteiros, referência temporal | Evita float e promessa de conversão | RN-010 |
| Score | Não bloqueia tarefa e não representa dinheiro | Fórmula não validada | Fase 0 |
| Evidência de aprendizagem | `SkillEvidence` interna | Fonte de verdade independente | RF-079 |
| Badge | Opt-in por badge | Privacidade por padrão | RF-080/RN-044 |
| Criação da tarefa | Admin em nome da empresa | Não exige portal empresarial completo | Fase 4 |
| Vagas | Uma por PaidTask | Regra do MVP | RN-043 |
| Assignment reservation | 60 minutos | Exclusividade temporária | ADR-001 |
| Task funding reservation | Persiste após expiração | Garante obrigação futura | ADR-001 |
| Pagamento concorrente | Um attempt ativo por obrigação | Evita dois `xpay` | ADR-002 |
| Timeout incerto | Estado `AMBIGUOUS` | Obriga reconciliação | ADR-002 |
| Oportunidades | `PaidTask` ≠ `OpportunityListing` | Somente tarefa paga cria workflow financeiro | RF-069–071 |
| Comunidade | Feed/publicação/denúncia/moderação no P0 | Must have atual | RF-072–076 |
| Pix | Fora do caminho crítico, feature flag | Falha não desfaz Lightning | RN-016 |

# 4. Escopo

| P0 obrigatório | P1 após P0 | P2 visão futura | Fora do MVP |
|---|---|---|---|
| Golden path 1–17; Doador RF-017–047; recibo/impacto; oportunidades mínimas; comunidade mínima; mobile | Notificações, Breez refinado, mais filtros, feed paginado avançado | Pix real, resgate de liquidez, canais reais, múltiplas trilhas/tarefas | Localização, conexão segura, premium, mensagens privadas, recomendação algorítmica, IA decisora, Cashu, relay próprio |

Comunidade e oportunidades são P0. Elas podem ser implementadas depois do núcleo financeiro, mas são dependência obrigatória do hardening e do release candidate.

# 5. Arquitetura final

```text
apps/web — React/Vite/TypeScript
  ├─ NIP-07 signer
  ├─ ParticipantWallet: Breez Spark | BOLT11 externa
  └─ REST /api/v1
          |
apps/api — Flask modular
  ├─ identity / profiles / organizations
  ├─ learning / reputation
  ├─ opportunities / community / moderation
  ├─ work / payments / impact
  ├─ administration / notifications / platform
  └─ ports
      ├─ NostrGateway / NostrSigner
      ├─ ParticipantWallet / LightningGateway
      ├─ FiatGateway / ExchangeRateGateway
      └─ ObjectStorage
          |
PostgreSQL — domínio, ledger, audit, outbox e inbox
          |
worker — expiração, outbox, badge e reconciliação
          |
CLNRest privado / Core Lightning / relays / object storage
```

- Diretórios prováveis: `apps/api/src/bluejet/`, `apps/web/src/`, `openapi/bluejet-v1.yaml`, `migrations/versions/` e `docs/adr/`.
- O domínio não importa adapters de provider.
- Efeitos externos só partem de eventos de outbox confirmados na mesma transação do estado de domínio.
- CLNRest e runes ficam em rede privada; nenhuma credencial Lightning chega ao frontend.
- Administração possui autenticação, cookie, audience e autorização separados.
- Uploads ficam privados, em quarentena, e usam URLs temporárias.

# 6. Modelo de domínio

## Fontes de verdade

- Aprendizado: `SkillEvidence`, não badge.
- Trabalho: `PaidTask`, `Assignment`, `Submission` e `Review`.
- Funding: `TaskFundingReservation`, não `AssignmentReservation`.
- Obrigação: `PaymentObligation`, criada somente pela aprovação humana.
- Efeito externo: `ProviderPayment`, reconciliado pelo backend.
- Financeiro: `LedgerTransaction` e `LedgerEntry` append-only.
- Impacto realizado: pagamentos `SETTLED` e ledger real.
- Simulação: read models separados com `mode=MOCK`.

## Relacionamentos essenciais

- `User` possui sessões, quiz attempts, SkillEvidence, assignments e reports.
- `PaidTask` pertence a `Company`, possui uma vaga e uma ou mais funding reservations.
- `Assignment` possui uma AssignmentReservation, até duas submissions e reviews.
- `Assignment` possui no máximo uma PaymentObligation.
- `PaymentObligation` possui attempts históricos, mas no máximo um ativo.
- `OpportunityListing` não referencia entidades financeiras.
- `CommunityPostReference` referencia evento Nostr público; denúncia/moderação permanecem locais.

## Invariantes financeiras

- Valores em sats/msats ou centavos inteiros; float é proibido.
- `PaymentObligation.assignment_id` é único.
- `PayoutAttempt.idempotency_key` é único.
- `ProviderPayment.payment_hash` é único.
- `(provider, provider_event_id)` é único.
- Índice único parcial impede mais de um attempt em `CREATED`, `VALIDATED`, `PROCESSING` ou `AMBIGUOUS` por obrigação.
- Aprovação: `TASK_RESERVED → PARTICIPANT_PAYABLE`.
- Dispatch: `PARTICIPANT_PAYABLE → LIGHTNING_CLEARING`.
- Settlement: `LIGHTNING_CLEARING → SETTLED`.
- Falha definitiva usa lançamento compensatório; `AMBIGUOUS` permanece em clearing.

## Estados canônicos

```text
PaidTask: DRAFT → FUNDED → PUBLISHED → CLOSED

Assignment: RESERVED → IN_PROGRESS → SUBMITTED → UNDER_REVIEW
            → CHANGES_REQUESTED → RESUBMITTED → UNDER_REVIEW
            → APPROVED → PAYMENT_PENDING → PAYMENT_PROCESSING → PAID
            RESERVED/IN_PROGRESS → EXPIRED
            UNDER_REVIEW/RESUBMITTED → REJECTED

PaymentObligation: OPEN → CLEARING → SETTLED

PayoutAttempt: CREATED → VALIDATED → PROCESSING
               → AMBIGUOUS → SETTLED | FAILED
               → SETTLED | FAILED | EXPIRED

Badge: PUBLISH_PENDING → PUBLISHED | PUBLISH_FAILED
```

`AMBIGUOUS` não permite retry, não volta para `CREATED`, gera alerta e exige reconciliação para `SETTLED` ou `FAILED`.

## Eventos

- Domínio: `SkillEvidenceCreated`, `TaskFunded`, `PaidTaskPublished`, `AssignmentReserved`, `AssignmentExpired`, `SubmissionCreated`, `ChangesRequested`, `SubmissionApproved`, `PaymentObligationCreated`, `PayoutDispatchRequested`, `PaymentAmbiguous`, `PaymentSettled`, `ReceiptIssued`, `CommunityReportCreated`.
- Externos: relay ack/reject, resultado `xpay`, resultado `listpays`, webhook Fiat/Breez.
- Read models: `ParticipantJourney`, `EligibleTasks`, `OpportunitiesCatalog`, `CommunityFeed`, `ReviewerQueue`, `PaymentStatus`, `ReceiptView`, `DonorDashboard`, `ImpactRealized`, `SimulationScenario`.

# 7. Golden path obrigatório

1. Participante entra com Nostr.
2. Backend cria sessão sem receber chave privada.
3. Participante acessa uma trilha curta.
4. Participante conclui quiz com nota mínima de 80%.
5. Uma `SkillEvidence` é criada.
6. Uma `PaidTask` compatível é desbloqueada.
7. A tarefa já está previamente financiada.
8. Participante cria `AssignmentReservation` por 60 minutos.
9. Participante envia entrega privada.
10. Revisor humano aprova ou solicita uma correção.
11. Aprovação cria `PaymentObligation` imutável.
12. Participante fornece invoice BOLT11 pelo valor exato.
13. Tesouraria realiza pagamento Lightning real.
14. Backend reconcilia o pagamento.
15. Participante visualiza recibo.
16. Impacto realizado aparece separado da simulação.
17. Badge NIP-58 pode ser publicado com opt-in sem bloquear tarefa ou pagamento.

# 8. Rastreabilidade

| Requisitos atuais | Fase | PR | Módulo | Teste/evidência |
|---|---:|---|---|---|
| RF-001–003, CA-001 | 2 | PR-02 | identity | assinatura, replay, sessão, logout |
| RF-004–011, RF-079–080, CA-002 | 3 | PR-03 | learning/reputation | 79/80%, SkillEvidence, consentimento, relay |
| RF-012–016, CA-003, CA-011 | 4 | PR-09 | work/payments | funding, concorrência, expiração sem devolução |
| RF-017–024, CA-008 | 7 | PR-05 | donor/payments | aporte dividido e saldos separados |
| RF-025–031 | 7 | PR-06 | donor/impact | campanha financiada, consumo e encerramento |
| RF-032–041, CA-009 | 7 | PR-07 | donor/impact | principal separado, receita líquida, MOCK |
| RF-042–047, CA-010 | 7 | PR-08 | learning/payments | recompensa pré-financiada e única |
| RF-048–049 | 4 | PR-09 | work/platform | entrega autorizada, hash e storage privado |
| RF-050–053, CA-004 | 5 | PR-10 | work/payments | uma correção, justificativa e obrigação única |
| RF-054–061, RF-077–078, CA-005–006, CA-012–013 | 6 | PR-11 | payments | BOLT11, attempt concorrente, ambiguous e retry |
| RF-062–068, CA-007 | 7 | PR-12 | payments/impact/platform | recibo, real vs mock, seed/reset |
| RF-069–071, CA-014 | 8 | PR-13 | opportunities | tipos distintos e ausência de financeiro |
| RF-072–076, CA-015 | 8 | PR-13 | community/moderation | aviso público, feed, denúncia e ocultação |
| RN-001–020 | 3–7 | PR-03/09/10/11/12 | learning/work/payments | invariantes do golden path |
| RN-021–034 | 7 | PR-05/06/07/08/12 | donor/impact | modalidades e métricas separadas |
| RN-035–037, RN-043 | 4 | PR-09 | work/payments | reservations distintas e uma vaga |
| RN-038–040 | 6 | PR-11 | payments | attempt ativo, reconciliação e alerta |
| RN-041–042 | 8 | PR-13 | opportunities/community | sem payout e conteúdo público seguro |
| RN-044 | 3 | PR-03 | reputation | badge independente |
| RNF-001–011 | 1–10 | PR-01/04/11/16 | platform/payments | secrets, transações, inbox, recovery |
| RNF-012–016 | 9 | PR-14/15 | web | mobile, labels, teclado e mensagens |
| RNF-017–020 | 1/10 | PR-01/16 | platform | performance, demo e fallback honesto |

## Fase 0 — Requisitos, UX e ADRs

### Objetivo

Congelar contratos, escopo, marca, estados financeiros e referência visual antes da implementação.

### Critérios de entrada

Repositório inventariado; requisitos atuais e review disponíveis.

### Dependências

Nenhuma implementação.

### Checklist de implementação

- Manter RF-001–068 e acrescentar RF-069–080 sem reutilizar significado.
- Acrescentar RN-035–044 e CA-011–015.
- Formalizar ADR-001 e ADR-002.
- Corrigir marca, idioma, moedas, score, badge, oportunidades e comunidade no Figma.
- Remover conflito de um dia/devolução automática.
- Registrar `AMBIGUOUS` em requisitos, banco, backend, frontend, OpenAPI, testes e observabilidade.

### Entidades e estados afetados

Todas as entidades canônicas; principalmente reservations, payment obligation, payout attempt, opportunity e community.

### Endpoints e contratos afetados

Catálogo inicial de `/api/v1`; nenhum endpoint implementado nesta fase.

### Migrações

Nenhuma.

### Eventos de domínio

Catálogo e envelopes versionados.

### Integrações

Matriz REAL/SANDBOX/MOCK para Nostr, Lightning, Fiat, wallet, storage e câmbio.

### Testes unitários

Validação documental de IDs, links e estados.

### Testes de integração

Build Docusaurus após setup autorizado.

### Testes E2E

Storyboard desktop/mobile dos 17 passos, oportunidade e comunidade.

### Testes de falha

Revisão cruzada de todos os conflitos listados.

### Checklist de segurança

Threat model, classificação de segredos e dados proibidos no Nostr.

### Checklist de privacidade

Consentimento do badge e aviso de publicação comunitária pública.

### Checklist UX/Figma

Criar telas faltantes, estados loading/error/success/ambiguous e mobile.

### Checklist de revisão

Product, Architecture, Security, Payment e UX Gates.

### Critérios de saída

IDs válidos, ADRs aprovados, contratos sem conflito e Figma P0 aprovado.

### Fallback e rollback

Reverter somente mudanças documentais; código não pode começar com contrato conflitante.

### Riscos

Escopo amplo e divergência do protótipo.

### Estimativa relativa: M

### O que pode ser paralelizado

ADRs, rastreabilidade e revisão Figma.

### O que não pode ser iniciado antes desta fase

OpenAPI público, schema e UI final.

## Fase 1 — Fundação técnica

### Objetivo

Criar estrutura modular, configuração, PostgreSQL, OpenAPI, CI, testes e observabilidade.

### Critérios de entrada

Fase 0 aprovada.

### Dependências

Python 3.12, Node 20, PostgreSQL e object storage local.

### Checklist de implementação

- Criar `apps/api`, `apps/web`, `openapi` e `migrations`.
- Configurar Flask factory, SQLAlchemy 2 e Alembic.
- Definir OpenAPI 3.1, erros problem details, cursor e `Idempotency-Key`.
- Implementar outbox/inbox e worker com `FOR UPDATE SKIP LOCKED`.
- Config fail-closed e logs JSON com redaction.
- CI para docs, API, web, migrações e testes.
- Seed/reset restritos por ambiente.

### Entidades e estados afetados

`OutboxEvent`, `InboxEvent`, `AuditEvent` e tabelas base.

### Endpoints e contratos afetados

`GET /health/live`, `GET /health/ready` e erro comum.

### Migrações

Schemas, extensions, roles e tabelas platform.

### Eventos de domínio

Envelope `{event_id,type,version,aggregate_id,occurred_at,payload}`.

### Integrações

Adapters fake para todos os ports.

### Testes unitários

Config, serialização, redaction e transições.

### Testes de integração

PostgreSQL real, Alembic e outbox concorrente.

### Testes E2E

Health API/web.

### Testes de falha

Config ausente, banco fora e evento duplicado.

### Checklist de segurança

CORS allowlist, CSRF, headers, dependency e secret scan.

### Checklist de privacidade

Inventário de dados, retenção e redaction central.

### Checklist UX/Figma

Tokens CSS aprovados; nenhum Tailwind.

### Checklist de revisão

Architecture e Security Gates.

### Critérios de saída

CI verde, ambiente reproduzível e RNF-001–011/RNF-017–020 cobertos.

### Fallback e rollback

Migrações reversíveis e adapters fake sem efeito externo.

### Riscos

Bootstrap amplo e diferenças Node local/CI.

### Estimativa relativa: L

### O que pode ser paralelizado

API base, web shell, CI e infraestrutura.

### O que não pode ser iniciado antes desta fase

Persistência de domínio e integração real.

## Fase 2 — Identidade Nostr

### Objetivo

Autenticar participante por assinatura sem receber chave privada.

### Critérios de entrada

API, banco, cookies e OpenAPI disponíveis.

### Dependências

NIP-07 no cliente e verificador no backend.

### Checklist de implementação

- Challenge aleatório, uso único e TTL de cinco minutos.
- Evento assinado vinculado a URL, método, payload e challenge.
- Validar assinatura, pubkey, timestamp, nonce e replay.
- Sessão HttpOnly/Secure/SameSite=Lax com rotação.
- Logout revoga sessão.
- Fallback pré-autenticado mantém banner DEMO.

### Entidades e estados afetados

`AuthChallenge: ISSUED→USED|EXPIRED`; `Session: ACTIVE→REVOKED`.

### Endpoints e contratos afetados

`POST /auth/nostr/challenges`, `POST /auth/nostr/sessions`, `GET /me`, `DELETE /sessions/current`.

### Migrações

Users, challenges, sessions e índices de nonce/pubkey.

### Eventos de domínio

`UserAuthenticated`, `SessionRevoked`.

### Integrações

Signer Nostr somente no browser.

### Testes unitários

Assinatura, TTL, replay e clock skew.

### Testes de integração

Cookie, CSRF e revogação.

### Testes E2E

CA-001 ao vivo e fallback rotulado.

### Testes de falha

Signer negado, assinatura inválida e challenge repetido.

### Checklist de segurança

Nunca aceitar nsec; rate limit e cookie distinto do admin.

### Checklist de privacidade

Persistir somente pubkey e perfil mínimo.

### Checklist UX/Figma

Login, permissão negada, timeout e modo demo mobile.

### Checklist de revisão

Security Gate.

### Critérios de saída

RF-001–003 e CA-001 verdes; nenhum segredo em resposta/log.

### Fallback e rollback

Flag desabilita login ao vivo e preserva modo DEMO identificado.

### Riscos

Extensão indisponível no celular.

### Estimativa relativa: M

### O que pode ser paralelizado

UI de login e verificador.

### O que não pode ser iniciado antes desta fase

Jornada autenticada.

## Fase 3 — Capacitação, SkillEvidence e badge

### Objetivo

Concluir uma trilha curta, avaliar nota mínima, criar SkillEvidence e publicar badge opcional.

### Critérios de entrada

Participante autenticada.

### Dependências

Outbox e NostrSigner fake.

### Checklist de implementação

- Uma Course, Module, conteúdo e Quiz versionados.
- Attempts append-only e cálculo determinístico.
- Criar SkillEvidence única com nota ≥80%.
- Desbloquear tarefa pela evidence, nunca por score/badge.
- Registrar consentimento por badge e publicar via outbox.
- Não publicar dados pessoais ou evidência privada.

### Entidades e estados afetados

Enrollment, QuizAttempt, SkillEvidence, BadgeDefinition e BadgeAward.

### Endpoints e contratos afetados

`GET /courses`, `GET /courses/{id}`, `POST /courses/{id}/enrollments`, `POST /modules/{id}/quiz-attempts`, `GET /skill-evidence`, `PUT /skill-evidence/{id}/badge-consent`.

### Migrações

Learning/reputation e unicidades de evidence/award.

### Eventos de domínio

`QuizPassed`, `SkillEvidenceCreated`, `BadgePublicationRequested`.

### Integrações

NostrSigner e relays configuráveis.

### Testes unitários

79%, 80%, 100%, retry, unicidade e opt-in.

### Testes de integração

Outbox, relay ack e deduplicação.

### Testes E2E

CA-002: curso → quiz → SkillEvidence → tarefa; badge consentido separadamente.

### Testes de falha

Relay indisponível ou badge rejeitado sem bloquear tarefa/pagamento.

### Checklist de segurança

Signer isolado e nenhuma chave no banco/log.

### Checklist de privacidade

Preview público e opt-in por badge.

### Checklist UX/Figma

Curso único, quiz, resultado, evidence, consentimento e status do badge.

### Checklist de revisão

Product, Security, Privacy e UX Gates.

### Critérios de saída

RF-004–011, RF-079–080, RN-044 e CA-002 verdes.

### Fallback e rollback

Desabilitar publicação externa preservando SkillEvidence.

### Riscos

Propagação inconsistente entre relays.

### Estimativa relativa: M

### O que pode ser paralelizado

Learning, reputation e telas.

### O que não pode ser iniciado antes desta fase

Reserva da tarefa pela participante.

## Fase 4 — Tarefa e trabalho

### Objetivo

Cadastrar, financiar, publicar, reservar e receber entrega privada.

### Critérios de entrada

Ledger base, SkillEvidence e storage disponíveis.

### Dependências

Company administrada, ObjectStorage e worker de expiração.

### Checklist de implementação

- Admin cria Company e PaidTask de uma vaga.
- TaskFundingReservation debita fontes e credita `TASK_RESERVED`.
- Publicação exige funding integral; elegibilidade exige SkillEvidence.
- Lock de linha e índice parcial impedem duas assignments ativas.
- AssignmentReservation expira em 60 minutos e libera somente a vaga.
- TaskFundingReservation permanece vinculada; outra participante pode reservar.
- Upload fica em quarentena; PNG/JPEG/PDF/MP4, até 10 MB.
- Submission guarda versão, hash e referências privadas.

### Entidades e estados afetados

Company, PaidTask, TaskFundingReservation, Assignment, AssignmentReservation, Submission e StoredObject.

### Endpoints e contratos afetados

`POST /admin/companies`, `POST /admin/paid-tasks`, `POST /admin/paid-tasks/{id}/funding-reservations`, `POST /admin/paid-tasks/{id}/publish`, `GET /paid-tasks?eligible=true`, `POST /paid-tasks/{id}/assignment-reservations`, `POST /uploads`, `POST /assignments/{id}/submissions`.

### Migrações

Work, storage, funding lines, uma vaga e índices parciais.

### Eventos de domínio

`TaskFunded`, `PaidTaskPublished`, `AssignmentReserved`, `AssignmentExpired`, `SubmissionCreated`.

### Integrações

ObjectStorage privado e scanner.

### Testes unitários

Funding, elegibilidade, TTL, MIME e hash.

### Testes de integração

Duas reservas concorrentes; expiração preserva funding.

### Testes E2E

CA-003/011: tarefa desbloqueada → reserva → expiração ou entrega.

### Testes de falha

Tarefa sem funding, upload inválido, usuária não atribuída e worker duplicado.

### Checklist de segurança

RBAC, locks, URL temporária e download autorizado.

### Checklist de privacidade

Entrega privada e nada publicado no Nostr.

### Checklist UX/Figma

Tarefa paga identificada, reserva, cronômetro, upload e expiração.

### Checklist de revisão

Product, Payment e Security Gates.

### Critérios de saída

RF-012–016, RF-048–049, RN-035–037, RN-043 e CA-003/011 verdes.

### Fallback e rollback

Fechar tarefa; funding só muda por operação contábil explícita.

### Riscos

Race conditions e arquivos maliciosos.

### Estimativa relativa: L

### O que pode ser paralelizado

Storage, admin task e participant task.

### O que não pode ser iniciado antes desta fase

Revisão ou obrigação financeira.

## Fase 5 — Revisão e obrigação financeira

### Objetivo

Executar revisão humana, uma correção e aprovação imutável.

### Critérios de entrada

Submission válida e autenticação administrativa separada.

### Dependências

Ledger transacional e audit log.

### Checklist de implementação

- Fila administrativa minimiza dados pessoais.
- Decisões: `APPROVE`, `REQUEST_CHANGES`, `REJECT`.
- Correção/rejeição exigem justificativa.
- Somente uma correção; reenvio cria Submission v2.
- Aprovação, ledger e PaymentObligation ocorrem na mesma transação.
- Aprovação duplicada retorna a obrigação original.
- Obrigação e audit log rejeitam UPDATE/DELETE.

### Entidades e estados afetados

Review, PaymentObligation, Assignment e AuditEvent.

### Endpoints e contratos afetados

`GET /admin/review-queue`, `GET /admin/submissions/{id}`, `POST /admin/submissions/{id}/reviews`, `GET /assignments/{id}/payment-obligation`.

### Migrações

Reviews, obligations, constraints e triggers append-only.

### Eventos de domínio

`ChangesRequested`, `SubmissionRejected`, `SubmissionApproved`, `PaymentObligationCreated`.

### Integrações

Nenhuma externa na transação de aprovação.

### Testes unitários

Uma correção, justificativa e transições proibidas.

### Testes de integração[text](../apps/api/bluejet_api/config.py)

Aprovação duplicada e rollback atômico.

### Testes E2E

CA-004 com correção e posterior aprovação.

### Testes de falha

Duplo clique, reviewer sem permissão e erro do ledger.

### Checklist de segurança

Admin Argon2id+TOTP, RBAC e CSRF.

### Checklist de privacidade

Revisor vê somente dados necessários.

### Checklist UX/Figma

Fila, detalhe, correção, rejeição e aprovação confirmada.

### Checklist de revisão

Product, Payment e Security Gates.

### Critérios de saída

RF-050–053, RN-006–008, RN-019–020 e CA-004 verdes.

### Fallback e rollback

Desabilitar novas reviews; obrigações existentes continuam válidas.

### Riscos

Aprovação sem saldo ou tentativa de reversão.

### Estimativa relativa: M

### O que pode ser paralelizado

UI de revisão e serviço de obrigação.

### O que não pode ser iniciado antes desta fase

Solicitação de invoice.

## Fase 6 — Ledger e Lightning

### Objetivo

Validar BOLT11, garantir attempt exclusivo, pagar por `xpay` e reconciliar por `listpays`.

### Critérios de entrada

PaymentObligation `OPEN` e funding contabilizado.

### Dependências

CLNRest privado, rune mínima, worker e chave de criptografia.

### Checklist de implementação

- Validar rede, valor, expiração e payment hash da BOLT11.
- Cifrar invoice e persistir somente metadados necessários em claro.
- Obter lock pessimista ou compare-and-swap na obrigação.
- Exigir `OPEN`, mudar atomicamente para `CLEARING` e criar attempt/outbox na mesma transação.
- Índice único parcial para `CREATED`, `VALIDATED`, `PROCESSING`, `AMBIGUOUS`.
- Mesma idempotency key retorna o original; key diferente com attempt ativo retorna 409 ou o attempt ativo.
- Worker emite somente um `xpay` para o outbox despachável.
- Timeout incerto gera `AMBIGUOUS`, alerta e bloqueio de retry.
- Reconciliar payment hash com `listpays`.
- `AMBIGUOUS → SETTLED|FAILED`; nunca `CREATED`.
- Retry somente após `FAILED`, `EXPIRED` ou reconciliação conclusiva.
- Attempts terminais permanecem no histórico.

### Entidades e estados afetados

LedgerAccount, LedgerTransaction, LedgerEntry, PaymentObligation, PayoutAttempt, ProviderPayment e ProviderEvent.

### Endpoints e contratos afetados

`POST /payment-obligations/{id}/payout-attempts`, `GET /payout-attempts/{id}`, `POST /admin/payout-attempts/{id}/reconcile`.

### Migrações

Ledger, attempts, providers, uniques e índice parcial de attempt ativo.

### Eventos de domínio

`PayoutInvoiceAccepted`, `PayoutDispatchRequested`, `PaymentAmbiguous`, `PaymentFailed`, `PaymentSettled`.

### Integrações

LightningGateway CLN REAL, SANDBOX e MOCK com modo visível.

### Testes unitários

Invoice errada/expirada, idempotency key, payment hash e transições `AMBIGUOUS`.

### Testes de integração

PostgreSQL real, CLN fake fiel, ledger e outbox transacionais.

### Testes E2E

CA-005/006/013: invoice → xpay → listpays → PAID.

### Testes de falha

CA-012: duas requisições simultâneas com invoices e keys diferentes; somente um attempt, outbox e xpay.

### Checklist de segurança

Rune fora do frontend, allowlist, limite de valor/fee e redaction.

### Checklist de privacidade

Invoice cifrada e mascarada; preimage não é pública.

### Checklist UX/Figma

Invoice, processando, ambíguo, falho, reconciliando e pago.

### Checklist de revisão

Payment Gate por especialista Lightning.

### Critérios de saída

RF-054–061, RF-064, RF-077–078, RN-038–040 e CA-005/006/012/013 verdes.

### Fallback e rollback

Interromper dispatch real, reconciliar pendentes e nunca reverter obrigação para evitar pagamento.

### Riscos

Liquidez, rede incorreta, timeout ambíguo e corrida de requests.

### Estimativa relativa: L

### O que pode ser paralelizado

Adapter CLN, ledger, reconciliador e UI de estados.

### O que não pode ser iniciado antes desta fase

Recibo final e impacto realizado.

## Fase 7 — Doador, recibo, carteira e impacto

### Objetivo

Cumprir RF-017–047, emitir recibos e separar impacto real de simulação.

### Critérios de entrada

Ledger e pagamento liquidado disponíveis.

### Dependências

ExchangeRateGateway, read models e wallet adapters.

### Checklist de implementação

- Perfil único de Doador com saldos contábeis separados.
- Aporte dividido soma 100% e exige aceite específico.
- Campanha reserva o valor máximo antes da publicação.
- Capital de liquidez nunca paga tarefa diretamente.
- Posição, canais, routing e custos são `MOCK` quando não reais.
- Somente receita líquida positiva reconciliada alimenta BonusPool.
- Recompensa de trilha cria obrigação distinta e única.
- Receipt é imutável e derivado do ledger.
- BRL guarda centavos, fonte e timestamp.
- BOLT11 externo é fallback obrigatório; Breez é adapter.
- Impacto realizado lê somente settlements reais.

### Entidades e estados afetados

DonorProfile, Contribution, ContributionAllocation, ImpactCampaign, LiquidityPosition, RoutingPeriod, BonusPool, Receipt e ExchangeRateSnapshot.

### Endpoints e contratos afetados

`POST /donor/contributions`, `GET /donor/contributions`, `POST /donor/campaigns`, `GET /donor/dashboard`, `GET /receipts/{id}`, `GET /me/payments`, `GET /impact/realized`, `GET /impact/simulations`.

### Migrações

Donor, campaigns, liquidity, rewards, receipts e simulation schema separado.

### Eventos de domínio

`ContributionAllocated`, `CampaignFunded`, `RoutingPeriodReconciled`, `BonusCredited`, `CourseRewardObligationCreated`, `ReceiptIssued`, `ImpactRealized`.

### Integrações

ParticipantWallet, ExchangeRateGateway e FiatGateway desabilitado por padrão.

### Testes unitários

Composição 100%, saldos, receita líquida, reward único, receipt e mode.

### Testes de integração

CA-008/009/010 e receipt reconstruído do ledger.

### Testes E2E

Doador → alocação → campanha; participante → recompensa/recibo; painel real/mock.

### Testes de falha

Cotação indisponível, receita negativa, Breez indisponível e Pix falho.

### Checklist de segurança

Autorização doador/admin e recibo autorizado.

### Checklist de privacidade

Painel usa agregados; não expõe entregas ou dados sensíveis.

### Checklist UX/Figma

Sats primários, BRL secundário, principal/receita/custos/impacto separados e mode visível.

### Checklist de revisão

Product, Payment, Privacy e UX Gates.

### Critérios de saída

RF-017–047, RF-062–068 e CA-007–010 verdes.

### Fallback e rollback

Omitir BRL se cotação falhar; desligar adapter Pix/Breez sem afetar Lightning externo.

### Riscos

Escopo Doador e interpretação incorreta de capital/receita.

### Estimativa relativa: L

### O que pode ser paralelizado

Contributions, receipt, wallet e dashboard após ledger.

### O que não pode ser iniciado antes desta fase

Métricas públicas de impacto ou bônus sem reconciliação.

## Fase 8 — Comunidade e oportunidades mínimas P0

### Objetivo

Entregar RF-069–076 sem introduzir pagamentos indevidos ou dados sensíveis.

### Critérios de entrada

Identity, RBAC, NostrGateway e catálogo de PaidTask disponíveis.

### Dependências

Relays Nostr e moderação local.

### Checklist de implementação

- Painel lista PaidTask e OpportunityListing em seções distintas.
- Payload usa `PAID_TASK` ou `EXTERNAL_OPPORTUNITY`.
- OpportunityListing nunca cria funding, assignment, review, obligation ou payout.
- Feed permite aprendizado, dúvida e conquista.
- Participante assina no cliente após aviso público.
- Denúncia e ocultação/restauração são locais e auditadas.
- Excluir localização, conexão segura, premium, mensagens privadas, feed avançado e recomendação.

### Entidades e estados afetados

OpportunityListing, CommunityPostReference, ContentReport e ModerationDecision.

### Endpoints e contratos afetados

`GET /opportunities`, `POST /admin/opportunities`, `GET /community/feed`, `POST /community/reports`, `POST /admin/moderation-decisions`.

### Migrações

Listings, reports e moderation.

### Eventos de domínio

`OpportunityPublished`, `CommunityReportCreated`, `ContentHidden`, `ContentRestored`.

### Integrações

NostrGateway e relays públicos.

### Testes unitários

Discriminador de tipos, ausência de workflow financeiro e moderação.

### Testes de integração

Relay read/write e deduplicação.

### Testes E2E

CA-014/015: navegar tipos, publicar com aviso, denunciar e ocultar.

### Testes de falha

Relay indisponível, evento duplicado, link externo inválido e usuário não autorizado.

### Checklist de segurança

Sanitização, rate limit, links seguros e nenhum dado financeiro no evento.

### Checklist de privacidade

Aviso público, preview e proibição de dados sensíveis.

### Checklist UX/Figma

Rótulos claros “Tarefa remunerada” e “Oportunidade externa”; estados relay/moderação.

### Checklist de revisão

Product, Security, Privacy e UX Gates.

### Critérios de saída

RF-069–076, RN-041–042 e CA-014/015 verdes; comunidade e oportunidades permanecem P0.

### Fallback e rollback

Relay indisponível mostra estado offline; catálogo local continua; a feature não é omitida do release.

### Riscos

Conteúdo público indevido e confusão entre oportunidade e tarefa.

### Estimativa relativa: M

### O que pode ser paralelizado

Opportunity catalog e community/moderation.

### O que não pode ser iniciado antes desta fase

Hardening/release; mensagens privadas ou localização.

## Fase 9 — Cliente, Figma e mobile

### Objetivo

Implementar o golden path, Doador, oportunidades e comunidade com fidelidade visual, responsividade e acessibilidade.

### Critérios de entrada

Figma corrigido/aprovado, contratos OpenAPI estáveis e Figma Inspection Gate
aprovado conforme ADR-003.

### Figma Inspection Gate (obrigatório)

- Usar o plugin/app da Figma conectado ao Codex no arquivo canônico:
  `https://www.figma.com/design/TyhhDZgTJ4jqqKfnq1jdNZ/hack4frredom?node-id=0-1`.
- Inspecionar diretamente frames, componentes, estilos, tokens, dimensões,
  grids, tipografia e assets antes de implementar qualquer tela.
- Registrar no relatório de inspeção os IDs e propriedades utilizadas.
- Tratar o Figma como fonte de apresentação e interação visual; usar
  `docs/requisitos.md`, ADRs e OpenAPI como fonte de comportamento, estados e
  regras de negócio.
- Registrar toda divergência em que requisitos prevaleçam sobre o Figma.
- Exportar assets pelo plugin; recriar em código somente elementos simples.
- Reprovar a fase se qualquer tela tiver sido criada por aproximação antes da
  auditoria.
- Screenshots entram somente como evidência de validação visual posterior.

### Dependências

React/Vite/TypeScript, API, wallet adapters e assets exportados.

### Checklist de implementação

- Executar e anexar evidência do Figma Inspection Gate antes do primeiro PR de UI.
- App shell e rotas participant/admin/donor.
- Tokens CSS baseados no Figma aprovado; sem Tailwind.
- Login, curso, quiz, evidence, badge, tarefa, reserva, entrega, review, invoice, pagamento, recibo, impacto, Doador, oportunidades e comunidade.
- Estados loading, empty, error, success, expired, offline, `AMBIGUOUS` e `MOCK`.
- Desktop/mobile, foco visível, labels, teclado e reduced motion.
- Assets Figma baixados e versionados.
- Cliente nunca implementa regra financeira; somente renderiza estados da API.

### Entidades e estados afetados

View models de todos os contratos P0.

### Endpoints e contratos afetados

Todos os endpoints P0; cliente tipado a partir do OpenAPI.

### Migrações

Nenhuma.

### Eventos de domínio

Consumir polling de até cinco segundos; sem efeitos financeiros no cliente.

### Integrações

NIP-07, Breez Spark e BOLT11 externa.

### Testes unitários

Reducers, forms, estados, adapters e discriminação de oportunidades.

### Testes de integração

Mock Service Worker validado contra OpenAPI.

### Testes E2E

Golden path desktop/mobile, comunidade e Doador.

### Testes de falha

Offline, sessão expirada, relay/CLN/storage indisponíveis e `AMBIGUOUS`.

### Checklist de segurança

Sem secrets no bundle; CSP, XSS, CSRF e dependências revisados.

### Checklist de privacidade

Preview de publicação e downloads temporários.

### Checklist UX/Figma

Comparar conceito e screenshot; PT-BR consistente; tarefa e oportunidade não se confundem.

### Checklist de revisão

Figma Inspection Gate, UX Gate com fidelity ledger e QA Gate.

### Critérios de saída

RNF-012–016, Figma Inspection Gate aprovado e todos os fluxos P0 executáveis
em mobile.

### Fallback e rollback

Deploy do build anterior; API permanece compatível.

### Riscos

Volume de telas, acessibilidade tardia e dependência Breez/browser.

### Estimativa relativa: L

### O que pode ser paralelizado

Participant, admin/donor e visual QA após contratos.

### O que não pode ser iniciado antes desta fase

Release candidate.

## Fase 10 — Hardening e Demo Day

### Objetivo

Provar confiabilidade, segurança, recuperação e apresentação.

### Critérios de entrada

Todo P0 integrado em release candidate.

### Dependências

CLN real, wallet, relays, seeds e dados de demonstração.

### Checklist de implementação

- E2E completo, concorrência, chaos e scans.
- Seed idempotente e reset exclusivo de DEMO.
- Alertas para outbox parada, clearing antigo e `AMBIGUOUS`.
- Runbook de reconciliação e rotação de credenciais.
- Ensaiar cinco minutos com checkpoints e fallback.
- Congelar release candidate e gravar demonstração.

### Entidades e estados afetados

Todas; nenhuma regra nova.

### Endpoints e contratos afetados

Admin reset/reconcile restritos e auditados.

### Migrações

Somente aditivas no release candidate.

### Eventos de domínio

Auditar a cadeia completa de cada assignment e payout.

### Integrações

Nostr, CLN, wallet, storage e relays reais.

### Testes unitários

Invariantes e transições canônicas.

### Testes de integração

PostgreSQL, storage, outbox, inbox e CLN adapter.

### Testes E2E

Golden path móvel e CA-001–015.

### Testes de falha

Incluem reservas concorrentes, payout concorrente, `AMBIGUOUS`, badge/relay, Pix falho, MOCK isolado, secrets e teclado.

### Checklist de segurança

Threat model fechado, RBAC, secrets, uploads, webhook e response plan.

### Checklist de privacidade

Consentimentos, limpeza pós-demo e ausência de dados sensíveis públicos.

### Checklist UX/Figma

Contraste, foco, mobile, estados e modos visíveis.

### Checklist de revisão

Todos os gates formais.

### Critérios de saída

CA-001–015 e RNF-001–020 verdes; pagamento real reconciliado; comunidade/oportunidades no release.

### Fallback e rollback

Conta DEMO rotulada, BOLT11 externo, relay alternativo, vídeo gravado e rollback de aplicação; nunca falsificar pagamento.

### Riscos

Dependências externas, liquidez e prazo.

### Estimativa relativa: L

### O que pode ser paralelizado

Ensaios, scans, observabilidade e documentação.

### O que não pode ser iniciado antes desta fase

Apresentação como release aprovado.

# 9. Sequência de PRs

| PR | Objetivo | Requisitos atuais | CAs | Testes obrigatórios | Dependência/rollback/evidência |
|---|---|---|---|---|---|
| PR-00 | Convergência documental, ADRs e Figma | RF-069–080, RN-035–044 | CA-011–015 | IDs/estados/links | Nenhuma; reverter docs; ADRs aprovados |
| PR-01 | Fundação API/OpenAPI/PostgreSQL/outbox | RNF-001–011, RNF-017–020 | — | config, DB, migration, outbox | PR-00; migrations reversíveis; CI |
| PR-02 | Identidade Nostr | RF-001–003 | CA-001 | assinatura, replay, sessão | PR-01; flag DEMO; login observado |
| PR-03 | Learning, SkillEvidence e badge | RF-004–011, RF-079–080, RN-044 | CA-002 | quiz, evidence, consentimento | PR-02; badge desligável |
| PR-04 | Ledger e funding base | RF-013, RF-064 | — | partidas dobradas e transação | PR-01; saldo zero |
| PR-05 | Doador e alocações | RF-017–024 | CA-008 | 100%, aceites, saldo separado | PR-04; sem mistura |
| PR-06 | Campanhas de impacto | RF-025–031 | — | reserva/consumo/limite | PR-05; campanha encerrável |
| PR-07 | Liquidez, routing e bônus | RF-032–041, RN-021–027 | CA-009 | líquido positivo e MOCK | PR-06; mock isolado |
| PR-08 | Recompensa de trilha | RF-042–047, RN-028–031 | CA-010 | obrigação única | PR-06; desabilitar campanha |
| PR-09 | PaidTask, reservas e entrega | RF-012–016, RF-048–049, RN-035–037, RN-043 | CA-003/011 | race, expiração e upload | PR-03/04; funding preservado |
| PR-10 | Review e obligation | RF-050–053, RN-006–008 | CA-004 | correção/aprovação | PR-09; sem reversão |
| PR-11 | Lightning e reconciliação | RF-054–061, RF-077–078, RN-038–040 | CA-005/006/012/013 | attempt concorrente, xpay/listpays | PR-10; reconciliar antes de retry |
| PR-12 | Recibo, carteira e impacto | RF-062–068 | CA-007 | receipt e REAL/MOCK | PR-11; fallback BOLT11 |
| PR-13 | Comunidade e oportunidades P0 | RF-069–076, RN-041–042 | CA-014/015 | separação, feed, moderação | PR-03/09; relay offline |
| PR-14 | Cliente participante | RNF-012–016 | CA-001–006/011/013 | mobile/keyboard/E2E | PR-02–13; rollback build |
| PR-15 | Cliente admin/donor | RF-017–053 | CA-004/008–010 | RBAC/review/dashboard | PR-05–12; rollback build |
| PR-16 | Hardening e RC | Todos | CA-001–015 | regressão, chaos, scans, demo | PR-13–15; rollback release |

# 10. Gates de revisão

## Product Gate

- RF/RN/CA atual citado em cada PR.
- P0 inclui Doador, comunidade e oportunidades.
- Nenhum score, badge ou oportunidade externa vira gate financeiro.

## Architecture Gate

- Domínio não importa provider.
- OpenAPI, banco, frontend, testes e observabilidade compartilham estados canônicos.
- Outbox só é criado na mesma transação da mudança de estado.

## Security Gate

- Threat model, autorização, uploads, logs, segredos, Nostr e webhooks revisados.

## Payment Gate

- Funding, obligation, ledger, partial unique index, lock, `AMBIGUOUS`, reconciliação e retry verificados.

## UX Gate

- Golden path, P0 community/opportunities, mobile, acessibilidade e REAL/SANDBOX/MOCK.

## QA Gate

- Unitário, integração, E2E, concorrência, falhas e regressão verdes.

## Release Gate

- Seed/reset, observabilidade, fallback, demo gravada e rollback ensaiados.

# 11. Plano de testes

- Tarefa não financiada não publica.
- Duas reservas concorrentes: uma assignment ativa.
- Reserva expira em 60 minutos, libera vaga e preserva funding.
- Entrega por usuária não atribuída é rejeitada.
- Aprovação duplicada cria uma obrigação.
- Uma correção; segunda correção bloqueada.
- Invoice com valor errado ou expirada.
- Payment hash repetido e idempotency key repetida.
- Duas requests simultâneas com keys/invoices diferentes: um attempt ativo, um outbox, um `xpay`.
- Timeout após pagamento produz `AMBIGUOUS`, alerta e nenhum retry.
- `listpays` reconcilia para `SETTLED` ou `FAILED`.
- Retry somente após falha definitiva/reconciliação.
- Badge falho não bloqueia pagamento.
- Relay indisponível não bloqueia trabalho.
- Pix falho não desfaz Lightning.
- MOCK nunca entra no impacto realizado.
- Rune, invoice, token e identificador pessoal ausentes dos logs.
- OpportunityListing não cria payment workflow.
- Feed público exige aviso, denúncia e moderação mínima.
- Happy path mobile e navegação por teclado.

# 12. Plano de segurança

- Trust boundaries: browser/API, API/PostgreSQL, worker/CLNRest, API/storage e worker/relays.
- Autenticação: Nostr para participante; Argon2id+TOTP para administração.
- Autorização: PARTICIPANT, REVIEWER, ADMIN, DONOR e SPONSOR_VIEWER com ownership.
- Arquivos: storage privado, quarentena, MIME sniffing, hash, limite e URL temporária.
- Nostr: nenhum dado pessoal, entrega, invoice ou pagamento; badge opt-in.
- Lightning: rune mínima, limite de valor/fee, invoice cifrada, locks e reconciliação.
- Webhooks/inbox: autenticação, timestamp, replay window e deduplicação.
- Observabilidade: alertas de outbox parada, clearing antigo e `AMBIGUOUS`.
- Response plan: pausar dispatch, preservar ledger, revogar rune/sessões, reconciliar e rotacionar segredos.

# 13. Plano de demonstração

- Dados: uma participante, um admin/reviewer, um doador, uma empresa, uma trilha e uma PaidTask de usabilidade.
- Valor: 1.000 sats; empresa e matching previamente reservados; bônus somente se realizado.
- Sequência: tarefa financiada → login → quiz 80% → SkillEvidence → badge opt-in → reserva 60m → entrega → review → obligation → BOLT11 → xpay → listpays → receipt → impacto → oportunidade/comunidade.
- Duração: até cinco minutos, com checkpoints de login, evidence, aprovação, pagamento e recibo.
- Real: assinatura Nostr, pagamento Lightning, reconciliação e badge se consentido.
- Mock: cenário de capital/canais/routing, sempre marcado.
- Fallback: sessão DEMO rotulada, BOLT11 externo, relay alternativo e vídeo gravado.
- Reset: somente ambiente DEMO, admin+TOTP, auditado e sem produção.

# 14. Riscos e mitigação

| Risco | Probabilidade | Impacto | Sinal | Mitigação | Dono |
|---|---|---|---|---|---|
| Prazo curto | Alta | Crítico | P0 não integrado | slices verticais e congelar P2 | Tech Lead |
| CLN sem rota | Média | Crítico | xpay falha | valores baixos, ensaio e BOLT11 externo | Payment Lead |
| Timeout ambíguo | Média | Crítico | clearing antigo | alerta, listpays e sem retry cego | Payment Lead |
| Corrida de payout | Média | Crítico | dois attempts | lock + partial unique + CA-012 | Backend |
| Figma incompleto | Alta | Alto | tela sem estado | Fase 0 e fidelity ledger | UX |
| Relay indisponível | Alta | Médio | sem ACK | retry e relay alternativo | Nostr Lead |
| Dados públicos indevidos | Média | Alto | report sensível | aviso, sanitização, moderação | Privacy |
| Upload malicioso | Média | Alto | MIME divergente | quarentena e scan | Security |
| Escopo Doador | Alta | Alto | PR P0 crescente | contratos pequenos e feature flags | Product |

# 15. Definition of Done

- PLAN começa na seção 1 e contém Fases 0–10.
- Requisitos RF-001–080, RN-001–044, RNF-001–020 e CA-001–015 citados existem no documento atual.
- Golden path 1–17 executável.
- AssignmentReservation e TaskFundingReservation permanecem distintas.
- Uma obrigação possui um único attempt ativo, `AMBIGUOUS` é canônico e retry exige reconciliação.
- Comunidade e oportunidades P0 passam CA-014/015.
- Ledger balanceado, approval imutável e pagamento Lightning real reconciliado.
- Nenhum segredo aparece em código/logs/respostas.
- Mobile, teclado, estados de erro e modo REAL/SANDBOX/MOCK validados.
- Seed, reset, fallback, rollback e ensaio de cinco minutos aprovados.

# 16. Comandos de verificação

## Comandos existentes no repositório

- `npm ci` — setup usado pelo CI.
- `npm install` — setup documentado no README.
- `npm run docs:start` — servidor Docusaurus.
- `npm run docs:build` — build Docusaurus.
- `npm run docs:serve` — serve do build.
- `npm run clear` — limpeza de cache.

## Comandos ausentes a serem criados em PR-01

Lint, type check, testes backend/frontend, migrações, API, worker, E2E, segurança, build do produto e execução integrada continuam `MISSING` até serem adicionados e validados.

# 17. Questões restantes

Nenhuma questão bloqueante para a consistência documental. O próximo passo é executar PR-00 documental; nenhuma funcionalidade de aplicação pode ser implementada antes dos gates da Fase 0.
