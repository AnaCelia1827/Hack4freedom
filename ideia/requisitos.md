# Requisitos do Produto — MVP

Este documento converte a visão e os [fluxos fechados](fluxos.md) em requisitos verificáveis para o Demo Day de 25 de julho de 2026.

## 1. Objetivo e métrica principal

Demonstrar que uma participante consegue entrar com Nostr, concluir uma capacitação, receber um badge, executar uma tarefa financiada, obter aprovação humana e receber um pagamento Lightning real.

> No cenário controlado do Demo Day, a participante deve sair do login ao pagamento confirmado em até dez minutos, sem precisar compreender canais, invoices ou chaves privadas.

## 2. Escopo MoSCoW

### Must have

- login Nostr por assinatura;
- trilha curta com ganho de pontuação;
- badge NIP-58 real - comprovar que fez a trilha;
- tarefa previamente financiada - tarefa que a empresa vai colocar;
- reserva, entrega e revisão humana - pessoa/empresa que subiu a tarefa;
- pagamento Lightning real para a carteira da pessoa que concluiu a task;
- ledger e painel mínimo do doador, separado da área da empresa que cria a task;
- perfil único de doador com duas modalidades: fundo de impacto e capital de liquidez;
- Painel de oportunidades - divisão em 2 partes (1. tarefas - empresas/pessoa parceira adiciona uma tarefa remunerada; 2. Oportunidades gerais da comunidade);
- Tela de comunidade - tipo um linkedin/twiter, onde pode

### Should have

- carteira Breez integrada;
- badge visível no perfil;
- valor de referência em BRL;

### Could have

- Lightning Address;
- off-ramp real via Hodle;
- login NIP-46;
- triagem por IA;
- notificações;
- mais trilhas e tarefas;
- painel detalhado de canais.

### Won't have no MVP

- portal completo para empresas;
- onboarding financeiro e compliance completos de doadores;
- lucratividade real comprovada do nó;
- resgate de capital de liquidez;
- multisig com BDK;
- relay próprio;
- Cashu/eCash;
- marketplace aberto;
- aprovação autônoma por IA;
- promessa de Pix instantâneo.

## 3. Perfis

| Perfil | Permissões |
|---|---|
| 1. Participante | Consumir trilha, reservar tarefa, entregar, gerar invoice e ver recibo |
| 2. Empresa/Pessoa parceira que sobe a task | Avaliar, aprovar, pedir correção e justificar |
| 3. Doador | Aportar, escolher a modalidade, acompanhar saldos, impacto e liquidez |
| Opcional - Administrador | Cadastrar conteúdo, configurar demo, reconciliar aportes e consultar ledger |


## 4. Requisitos funcionais

### Identidade

**RF-001 — Assinatura Nostr:** verificar assinatura e associar a chave pública a uma sessão.
**RF-002 — Chave privada:** nunca solicitar, transmitir ou persistir a chave privada.  
**RF-003 — Logout:** permitir encerramento da sessão no dispositivo.

### Capacitação

**RF-004 — Exibir trilha:** mostrar título, objetivo, duração e conteúdo.  
**RF-005 — Registrar progresso e a pontuação:** persistir início, tentativas e conclusão.
**RF-006 — Avaliar:** aplicar quiz e calcular resultado.
**RF-007 — Desbloquear:** liberar tarefa com nota mínima de 80%.
**RF-008 — Nova tentativa:** permitir nova tentativa sem apagar histórico.

### Badge - perfil

**RF-009 — Definir badge:** a plataforma cria o modelo do certificado, contendo nome, descrição e identificador. Essa definição é assinada pela chave Nostr oficial do projeto.
**RF-010 — Conceder badge:** Conceder badge: depois da aprovação, a plataforma publica um evento associando o badge à chave pública (npub) da participante.
**RF-011 — Registrar publicação:** o backend guarda o ID do evento, os relays utilizados e quais deles confirmaram o recebimento.

### Tarefa e financiamento

**RF-012 — Cadastrar tarefa:** informar título, empresa, instruções, critérios, prazo, vagas e remuneração.  
**RF-013 — Compor valor:** registrar parcelas de empresa, matching e bônus realizado.   
**RF-014 — Listar elegíveis:** mostrar apenas tarefas cujos pré-requisitos foram cumpridos.  
**RF-015 — Evitar concorrência:** impedir duas participantes na mesma task. Para isso, a participante pode se inscrever para realziar umas task, e essa task ficará aguardando conclusão por essa pessoa, pelo tempo pré definido.
**RF-016 — Liberar expirada:** devolver vaga e recursos após expiração.

### Perfil Doador e modalidades de aporte

Uma única conta de doador pode utilizar duas modalidades financeiras. Elas compartilham login, cadastro, histórico e painel, mas permanecem separadas no ledger:

```text
Perfil Doador
   |
   +-- FUNDO_IMPACTO
   |      recurso consumível para matching e incentivos
   |
   +-- CAPITAL_LIQUIDEZ
          capital denominado em BTC para canais Lightning
```

| Modalidade | Natureza | Uso | MVP |
|---|---|---|---|
| `FUNDO_IMPACTO` | Doação consumível | Matching e recompensas reservadas | Real ou seed controlado |
| `CAPITAL_LIQUIDEZ` | Capital alocado, não doação consumível | Canais e possível receita líquida | Simulado e identificado |

**RF-017 — Perfil único:** permitir que a mesma identidade acesse as duas modalidades sem criar contas distintas.  
**RF-018 — Explicar modalidades:** antes do aporte, mostrar finalidade, consumo, riscos, resgate e efeito esperado de cada modalidade. 
**RF-019 — Escolher alocação:** permitir selecionar somente impacto, somente liquidez ou dividir o valor entre ambas.  
**RF-020 — Validar composição:** exigir que a soma das parcelas corresponda a 100% do aporte.  
**RF-021 — Confirmar conscientemente:** apresentar um resumo final e coletar aceite específico para cada modalidade antes de confirmar.  
**RF-022 — Registrar aporte:** criar identificador, valor, moeda de entrada, cotação, parcelas, modo da integração e status.  
**RF-023 — Emitir comprovante:** mostrar quanto foi destinado a impacto e quanto foi convertido ou referenciado em BTC para liquidez.  
**RF-024 — Histórico unificado:** listar todos os aportes na mesma conta, com filtros por modalidade e status.

#### Fundo de impacto

**RF-025 — Creditar fundo:** após confirmação financeira, creditar a parcela de impacto como saldo consumível.  
**RF-026 — Criar campanha:** permitir destinar saldo a matching de tasks ou recompensa de conclusão de trilha.  
**RF-027 — Definir limites:** registrar valor unitário, público elegível, quantidade máxima, início e término.  
**RF-028 — Reservar campanha:** reservar o valor máximo da campanha antes de anunciá-la às participantes.  
**RF-029 — Consumir saldo:** baixar a reserva somente após o evento elegível e o pagamento Lightning confirmado.  
**RF-030 — Encerrar campanha:** impedir novas recompensas quando o saldo ou prazo terminar.  
**RF-031 — Exibir impacto:** mostrar sats reservados, distribuídos, saldo restante, pessoas beneficiadas e tarefas/trilhas associadas.

#### Capital de liquidez

**RF-032 — Registrar capital:** registrar a parcela denominada em BTC separadamente do fundo consumível.  
**RF-033 — Informar custódia:** mostrar quem controla as chaves, prazo de alocação, regras de resgate, custos e riscos.  
**RF-034 — Associar ao nó:** relacionar o capital ao nó e, quando aplicável, aos canais financiados.  
**RF-035 — Exibir posição:** mostrar principal em BTC, valor de referência em BRL, valor alocado, reserva on-chain e status dos canais.  
**RF-036 — Registrar receitas e custos:** importar ou registrar routing fees, rebalanceamentos, taxas on-chain e operação.  
**RF-037 — Fechar período:** calcular receita líquida somente depois que receitas e custos do período forem reconciliados.  
**RF-038 — Creditar bônus:** transferir somente receita líquida positiva e realizada para a pool de incentivos.  
**RF-039 — Impedir uso do principal:** bloquear o capital de liquidez como fonte direta de pagamento de tasks ou trilhas.  
**RF-040 — Identificar simulação:** marcar posição, canais, taxas e rendimentos como `MOCK` enquanto não vierem de um nó real.  
**RF-041 — Solicitar resgate:** em versão futura, permitir pedido de resgate conforme prazo, custos e saldo disponível após fechamento de canais. - BEM INTERESSANTE

#### Recompensa por conclusão de trilha

**RF-042 — Criar recompensa:** permitir campanha com valor fixo em sats por trilha concluída.  
**RF-043 — Pré-financiar recompensa:** publicar a recompensa somente quando seu valor máximo estiver reservado no fundo de impacto ou na pool de bônus realizado.  
**RF-044 — Validar elegibilidade:** exigir nota mínima, conclusão registrada e limite de uma recompensa por participante e trilha.  
**RF-045 — Acionar pagamento:** após elegibilidade, criar obrigação Lightning distinta do pagamento de task.  
**RF-046 — Informar origem:** identificar no recibo se a recompensa veio de doação de impacto ou receita líquida do nó.  
**RF-047 — Não prometer receita futura:** ocultar ou encerrar a campanha quando não houver saldo previamente reservado.

### Entrega e revisão da task

**RF-048 — Enviar:** receber campos obrigatórios e confirmação da submissão.  
**RF-049 — Preservar evidência:** guardar conteúdo, horário e hash.
**RF-050 — Aprovar:** registrar decisão e criar obrigação de pagamento.  
**RF-051 — Solicitar correção:** a pessoa que subiu a task pode exigir justificativa.  
**RF-052 — Reenviar:** permitir uma correção no MVP.
**RF-053 — Auditar:** registrar ator, horário, estado anterior, novo estado e motivo.

### Pagamento Lightning

depois que uma tarefa é aprovada, a carteira Breez da participante cria uma cobrança Lightning no valor correspondente.

**RF-054 — Gerar invoice:** Breez gera BOLT11 pelo valor aprovado.
**RF-055 — Validar invoice:** verificar rede, valor, expiração e associação com obrigação aberta.
**RF-056 — Iniciar pagamento:** enviar invoice à implementação de `LightningGateway`.
**RF-057 — Idempotência:** criar chave única por obrigação.
**RF-058 — Confirmar:** registrar status, identificador e prova disponível.
**RF-059 — Recuperar falha:** manter obrigação aberta e permitir retry idempotente. 
**RF-060 — Impedir duplicidade:** bloquear novo pagamento se a atribuição estiver `PAID`.  
**RF-061 — Invoice expirada:** permitir substituição sem perder aprovação.

### Recibo e ledger

**RF-062 — Recibo:** mostrar tarefa, total, composição, horário, status e identificador.  
**RF-063 — Referência BRL:** informar cotação e horário utilizados.  
**RF-064 — Ledger append-only:** correções financeiras geram lançamentos compensatórios.  

### Painel e demonstração — Painel do Doador

**RF-065 — Impacto real:** exibir tarefas pagas, sats, matching e badges a partir do ledger.
**RF-066 — Seed:** carregar trilha, tarefa, empresa e fontes iniciais.  
**RF-067 — Reset:** restaurar cenário sem afetar dados de produção.  
**RF-068 — Modo da integração:** indicar `REAL`, `SANDBOX` ou `MOCK` na administração.

## 5. Regras de negócio

**RN-001** — Tarefa não financiada não pode ser publicada. 
**RN-002** — Trilha concluída é pré-requisito da reserva. 
**RN-003** — Nota mínima é 80%.  
**RN-004** — Uma participante só pode ter uma reserva ativa da mesma tarefa.  
**RN-005** — Reserva expira em 1 dia.  
**RN-006** — Apenas entrega aprovada gera obrigação de pagamento.  
**RN-007** — Aprovação não pode ser revertida para evitar pagamento.  
**RN-008** — IA não aprova nem rejeita definitivamente.  
**RN-009** — Valor aprovado é fixado em sats.  
**RN-010** — Valor em BRL é referência temporal.  
**RN-011** — Cada atribuição é paga uma única vez.  
**RN-012** — Receita futura de roteamento não financia obrigação atual.  
**RN-013** — Só bônus líquido realizado pode compor reserva.  
**RN-014** — Capital de liquidez não é pagamento de tarefa.  
**RN-015** — Falha de badge não bloqueia tarefa ou pagamento.  
**RN-016** — Falha de Pix não desfaz pagamento Lightning.  
**RN-017** — Dados sensíveis não são publicados no Nostr.  
**RN-018** — Toda simulação é identificada visualmente.  
**RN-019** — Correção ou rejeição exige justificativa.  
**RN-020** — Uma correção é permitida no MVP.

### Regras do perfil Doador

**RN-021** — Uma conta de doador pode manter aportes nas duas modalidades.  
**RN-022** — Unificação de perfil não autoriza mistura contábil dos saldos.  
**RN-023** — `FUNDO_IMPACTO` é consumível e não possui promessa de resgate.  
**RN-024** — `CAPITAL_LIQUIDEZ` é denominado em BTC e não possui preservação garantida em BRL.  
**RN-025** — Capital de liquidez não pode pagar diretamente task, matching ou trilha.  
**RN-026** — Somente receita líquida positiva, reconciliada e realizada pode alimentar a pool de bônus.  
**RN-027** — Receita negativa de um período não pode gerar crédito de bônus.  
**RN-028** — Toda campanha precisa ter o valor máximo reservado antes de ser publicada.  
**RN-029** — Cada conclusão elegível recebe no máximo uma recompensa por campanha.  
**RN-030** — Recompensa de trilha e pagamento de task são obrigações financeiras diferentes.  
**RN-031** — Dados simulados não podem alterar saldos reais nem gerar pagamentos reais.  
**RN-032** — Resgate do capital depende de prazo, saldo dos canais, custos e regras aceitas.  
**RN-033** — Alterar a modalidade depois da confirmação exige operação contábil explícita; não se edita o aporte original.  
**RN-034** — O painel deve apresentar principal, receita bruta, custos, receita líquida e impacto em métricas separadas.

## 6. Requisitos não funcionais

### Segurança e privacidade

**RNF-001** — Chaves privadas não aparecem em banco, logs ou respostas.  
**RNF-002** — Credenciais Lightning, Hodle e do emissor ficam no servidor.  
**RNF-003** — Administração exige autenticação separada.  
**RNF-004** — Credencial Lightning possui privilégio mínimo.  
**RNF-005** — Dados pessoais e entregas são privados por padrão.  
**RNF-006** — Logs mascaram tokens, invoices e informações pessoais quando possível.

### Confiabilidade financeira

**RNF-007** — Pagamentos são idempotentes.  
**RNF-008** — Mudanças financeiras usam transação de banco.  
**RNF-009** — O ledger reconstrói o saldo de cada fonte.  
**RNF-010** — Webhooks verificam autenticidade e aceitam reentrega.  
**RNF-011** — Integrações externas possuem timeout e estado recuperável.

### Usabilidade e acessibilidade

**RNF-012** — Happy path funciona em tela móvel.  
**RNF-013** — Usuária não precisa conhecer canais ou roteamento.  
**RNF-014** — Valores aparecem em sats e, quando útil, em BRL.  
**RNF-015** — Erro e sucesso usam texto, não apenas cor.  
**RNF-016** — Formulários possuem rótulos e navegação por teclado.

### Desempenho e demo

**RNF-017** — Páginas respondem em até três segundos no cenário controlado.  
**RNF-018** — Aprovação aparece em até cinco segundos por polling ou tempo real.  
**RNF-019** — O modo demonstração é reproduzível.  
**RNF-020** — Fallback externo não simula falsamente transação real.

## 7. Entidades mínimas

| Entidade | Campos essenciais |
|---|---|
| User | id, nostr_pubkey, display_name, created_at |
| DonorProfile | id, user_id, display_name, terms_version, created_at |
| Contribution | id, donor_id, input_amount, input_currency, quote_id, status, integration_mode |
| ContributionAllocation | id, contribution_id, type, amount_sats, percentage, status |
| ImpactCampaign | id, donor_id, type, reward_sats, max_beneficiaries, reserved_sats, status |
| LiquidityPosition | id, donor_id, principal_sats, allocated_sats, reserve_sats, custody_model, status |
| RoutingPeriod | id, position_id, gross_fees_sats, costs_sats, net_sats, status |
| BonusPool | id, source_type, available_sats, reserved_sats, distributed_sats |
| Course | id, title, objective, status |
| Module | id, course_id, content, passing_score |
| Completion | user_id, module_id, score, status, completed_at |
| BadgeAward | user_id, definition_id, event_id, publish_status |
| Company | id, name, description |
| Task | id, company_id, title, instructions, reward_sats, slots, status |
| Assignment | id, task_id, user_id, status, reserved_until |
| Submission | id, assignment_id, content, evidence_hash, submitted_at |
| Review | id, submission_id, reviewer_id, decision, reason, created_at |
| FundingSource | id, type, name, available_sats, mode |
| Reservation | id, assignment_id, source_id, amount_sats, status |
| Payment | id, assignment_id, idempotency_key, invoice, status, payment_ref |
| LedgerEntry | id, event_type, source_id, amount_sats, reference_id, created_at |

## 8. Estados canônicos

```text
Task:
DRAFT, FUNDED, PUBLISHED, CLOSED

Assignment:
RESERVED, IN_PROGRESS, SUBMITTED, UNDER_REVIEW,
CHANGES_REQUESTED, RESUBMITTED, APPROVED,
PAYMENT_PENDING, PAYMENT_PROCESSING, PAYMENT_FAILED, PAID, EXPIRED

Badge:
PUBLISH_PENDING, PUBLISHED, PUBLISH_FAILED

Payment:
CREATED, VALIDATED, PROCESSING, SETTLED, FAILED, EXPIRED

Contribution:
DRAFT, QUOTED, PENDING_PAYMENT, CONFIRMED, ALLOCATED, FAILED, CANCELLED

ImpactCampaign:
DRAFT, FUNDED, ACTIVE, EXHAUSTED, CLOSED

LiquidityPosition:
PENDING, AVAILABLE, CHANNEL_ALLOCATED, REDEEM_REQUESTED, REDEEMED

RoutingPeriod:
OPEN, RECONCILED, APPROVED, BONUS_CREDITED
```

Esses nomes devem ser iguais no backend, frontend, banco e documentação.

## 9. Interfaces externas

```python
class NostrGateway:
    def verify_auth(self, event): ...
    def publish_badge(self, award): ...

class LightningGateway:
    def validate_invoice(self, invoice, expected_sats): ...
    def pay(self, invoice, idempotency_key): ...
    def get_payment(self, payment_ref): ...

class FiatGateway:
    def create_deposit(self, amount, currency): ...
    def get_quote(self, sats): ...
    def get_contribution_status(self, reference): ...
    def create_pix_withdrawal(self, request): ...
    def get_transaction_status(self, reference): ...

class LightningNodeGateway:
    def get_channels(self): ...
    def get_routing_fees(self, period): ...
    def get_liquidity_position(self): ...
```

Cada interface pode ter implementação real, sandbox e mock, sempre visível ao administrador.

## 10. Critérios de aceite

### CA-001 — Login

```gherkin
Dado um desafio válido e não utilizado
Quando a participante o assina com Nostr
Então o backend valida a assinatura
E cria uma sessão sem armazenar a chave privada
```

### CA-002 — Trilha e badge

```gherkin
Dada uma participante autenticada
Quando ela alcança pelo menos 80% na avaliação
Então o módulo é concluído
E a tarefa é desbloqueada
E a concessão do badge é iniciada
```

### CA-003 — Reserva

```gherkin
Dada uma tarefa publicada, financiada e com vaga
Quando uma participante elegível a inicia
Então uma atribuição exclusiva é criada por 60 minutos
E outra participante não ocupa a mesma vaga
```

### CA-004 — Aprovação

```gherkin
Dada uma entrega submetida
Quando o revisor a aprova
Então a decisão é auditada
E uma obrigação de pagamento é criada
```

### CA-005 — Pagamento

```gherkin
Dada uma obrigação e uma invoice válida pelo valor exato
Quando a tesouraria confirma o pagamento
Então a atribuição muda para PAID
E o ledger realiza cada fonte
E a participante visualiza o recibo
```

### CA-006 — Idempotência

```gherkin
Dado um pagamento processado
Quando a solicitação se repete com a mesma chave
Então nenhum segundo pagamento é criado
E a resposta referencia o original
```

### CA-007 — Simulação

```gherkin
Dado o painel do doador
Quando dados do nó não forem reais
Então aparecem em bloco marcado como Simulação
E não integram os totais realizados
```

### CA-008 — Aporte dividido pelo Doador

```gherkin
Dado um doador autenticado e um aporte cotado
Quando ele destina 40% ao FUNDO_IMPACTO e 60% ao CAPITAL_LIQUIDEZ
Então o sistema exige aceite das condições de ambas as modalidades
E registra duas alocações ligadas ao mesmo aporte
E mantém os saldos separados no ledger
E apresenta um comprovante com a composição completa
```

### CA-009 — Receita do nó transformada em bônus

```gherkin
Dado um período de roteamento com receitas e custos reconciliados
Quando a receita líquida for positiva e aprovada
Então somente o valor líquido é creditado na pool de bônus
E o principal de liquidez permanece inalterado
E o painel preserva separadamente receita bruta, custos e bônus disponível
```

### CA-010 — Recompensa de trilha pré-financiada

```gherkin
Dada uma campanha ativa, financiada e com saldo reservado
Quando uma participante elegível conclui a trilha pela primeira vez
Então uma obrigação de recompensa é criada pelo valor definido
E o recibo informa a fonte da recompensa
E uma nova conclusão da mesma trilha não gera segundo pagamento
```

## 11. Definition of Done

O MVP está pronto quando:

- requisitos Must have e CA-001 a CA-010 passaram;
- existe um pagamento Lightning real registrado;
- existe badge NIP-58 consultável em pelo menos um relay;
- repetir o pagamento não envia sats novamente;
- o cenário pode ser resetado;
- nenhum segredo aparece no repositório ou logs;
- toda simulação está marcada;
- um doador consegue visualizar as duas modalidades na mesma conta sem mistura de saldos;
- o roteiro cabe em cinco minutos;
- uma pessoa externa à equipe ensaiou o fluxo.

## 12. Rastreabilidade

| Objetivo | Requisitos | Evidência |
|---|---|---|
| Identidade portátil | RF-001 a RF-003 | Login Nostr |
| Capacitação | RF-004 a RF-008 | Quiz e desbloqueio |
| Reputação | RF-009 a RF-011 | Badge publicado |
| Trabalho real | RF-012 a RF-016 e RF-048 a RF-053 | Tarefa, entrega e aprovação |
| Perfil único do doador | RF-017 a RF-024 | Um acesso e duas alocações separadas |
| Fundo de impacto | RF-025 a RF-031 | Matching e campanhas financiadas |
| Capital de liquidez | RF-032 a RF-041 | Posição, canais, receitas e custos |
| Recompensa de trilha | RF-042 a RF-047 | Bônus pré-financiado e não duplicado |
| Renda imediata | RF-054 a RF-061 | Sats na Breez |
| Transparência | RF-062 a RF-068 | Recibo e painel |
| Confiabilidade | RF-057, RF-059, RF-060 e RNF-007 a RNF-011 | Retry e idempotência |
