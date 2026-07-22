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
- ledger e painel mínimo do patrocinador - painel da pessoa que cria a task;
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
- onboarding completo de patrocinadores;
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
| 3. Patrocinador | Visualizar impacto real e cenário simulado |

| Opcional - Administrador | Cadastrar conteúdo, financiar tarefa, configurar demo e consultar ledger |


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

**RF-012 — Cadastrar:** informar título, empresa, instruções, evidência, critérios, prazo, vagas e remuneração.  
**RF-031 — Compor valor:** registrar parcelas de empresa, matching e bônus realizado.  
**RF-032 — Validar financiamento:** publicar somente se reservas cobrirem todas as vagas.  
**RF-033 — Listar elegíveis:** mostrar apenas tarefas cujos pré-requisitos foram cumpridos.  
**RF-034 — Reservar:** criar atribuição exclusiva por 60 minutos.  
**RF-035 — Evitar concorrência:** impedir duas participantes na mesma vaga.  
**RF-036 — Liberar expirada:** devolver vaga e recursos após expiração.

### Entrega e revisão

**RF-040 — Enviar:** receber campos obrigatórios e confirmação da submissão.  
**RF-041 — Preservar evidência:** guardar conteúdo, horário e hash.  
**RF-042 — Fila de revisão:** exibir pendências sem dados pessoais desnecessários.  
**RF-043 — Aprovar:** registrar decisão e criar obrigação de pagamento.  
**RF-044 — Solicitar correção:** exigir justificativa.  
**RF-045 — Reenviar:** permitir uma correção no MVP.  
**RF-046 — Auditar:** registrar ator, horário, estado anterior, novo estado e motivo.

### Pagamento Lightning

**RF-050 — Gerar invoice:** Breez gera BOLT11 pelo valor aprovado.  
**RF-051 — Validar invoice:** verificar rede, valor, expiração e associação com obrigação aberta.  
**RF-052 — Iniciar pagamento:** enviar invoice à implementação de `LightningGateway`.  
**RF-053 — Idempotência:** criar chave única por obrigação.  
**RF-054 — Confirmar:** registrar status, identificador e prova disponível.  
**RF-055 — Recuperar falha:** manter obrigação aberta e permitir retry idempotente.  
**RF-056 — Impedir duplicidade:** bloquear novo pagamento se a atribuição estiver `PAID`.  
**RF-057 — Invoice expirada:** permitir substituição sem perder aprovação.

### Recibo e ledger

**RF-060 — Recibo:** mostrar tarefa, total, composição, horário, status e identificador.  
**RF-061 — Referência BRL:** informar cotação e horário utilizados.  
**RF-062 — Ledger append-only:** correções financeiras geram lançamentos compensatórios.  
**RF-063 — Rastreabilidade:** cada parcela aponta para sua fonte.

### Painel e demonstração

**RF-070 — Impacto real:** exibir tarefas pagas, sats, matching e badges a partir do ledger.  
**RF-071 — Cenário simulado:** marcar canais, roteamento, custos e bônus não reais como “Simulação”.  
**RF-072 — Separação:** não somar métricas reais e simuladas.  
**RF-080 — Seed:** carregar trilha, tarefa, empresa e fontes iniciais.  
**RF-081 — Reset:** restaurar cenário sem afetar dados de produção.  
**RF-082 — Modo da integração:** indicar `REAL`, `SANDBOX` ou `MOCK` na administração.

## 5. Regras de negócio

**RN-001** — Tarefa não financiada não pode ser publicada.  
**RN-002** — Trilha concluída é pré-requisito da reserva.  
**RN-003** — Nota mínima é 80%.  
**RN-004** — Uma participante só pode ter uma reserva ativa da mesma tarefa.  
**RN-005** — Reserva expira em 60 minutos.  
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

## 6. Requisitos não funcionais

### Segurança e privacidade

**RNF-001** — Chaves privadas não aparecem em banco, logs ou respostas.  
**RNF-002** — Credenciais Lightning, Hodle e do emissor ficam no servidor.  
**RNF-003** — Administração exige autenticação separada.  
**RNF-004** — Credencial Lightning possui privilégio mínimo.  
**RNF-005** — Dados pessoais e entregas são privados por padrão.  
**RNF-006** — Logs mascaram tokens, invoices e informações pessoais quando possível.

### Confiabilidade financeira

**RNF-010** — Pagamentos são idempotentes.  
**RNF-011** — Mudanças financeiras usam transação de banco.  
**RNF-012** — O ledger reconstrói o saldo de cada fonte.  
**RNF-013** — Webhooks verificam autenticidade e aceitam reentrega.  
**RNF-014** — Integrações externas possuem timeout e estado recuperável.

### Usabilidade e acessibilidade

**RNF-020** — Happy path funciona em tela móvel.  
**RNF-021** — Usuária não precisa conhecer canais ou roteamento.  
**RNF-022** — Valores aparecem em sats e, quando útil, em BRL.  
**RNF-023** — Erro e sucesso usam texto, não apenas cor.  
**RNF-024** — Formulários possuem rótulos e navegação por teclado.

### Desempenho e demo

**RNF-030** — Páginas respondem em até três segundos no cenário controlado.  
**RNF-031** — Aprovação aparece em até cinco segundos por polling ou tempo real.  
**RNF-032** — O modo demonstração é reproduzível.  
**RNF-033** — Fallback externo não simula falsamente transação real.

## 7. Entidades mínimas

| Entidade | Campos essenciais |
|---|---|
| User | id, nostr_pubkey, display_name, created_at |
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
    def get_quote(self, sats): ...
    def create_pix_withdrawal(self, request): ...
    def get_transaction_status(self, reference): ...
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
Dado o painel do patrocinador
Quando dados do nó não forem reais
Então aparecem em bloco marcado como Simulação
E não integram os totais realizados
```

## 11. Definition of Done

O MVP está pronto quando:

- requisitos Must have e CA-001 a CA-007 passaram;
- existe um pagamento Lightning real registrado;
- existe badge NIP-58 consultável em pelo menos um relay;
- repetir o pagamento não envia sats novamente;
- o cenário pode ser resetado;
- nenhum segredo aparece no repositório ou logs;
- toda simulação está marcada;
- o roteiro cabe em cinco minutos;
- uma pessoa externa à equipe ensaiou o fluxo.

## 12. Rastreabilidade

| Objetivo | Requisitos | Evidência |
|---|---|---|
| Identidade portátil | RF-001 a RF-004 | Login Nostr |
| Capacitação | RF-010 a RF-014 | Quiz e desbloqueio |
| Reputação | RF-020 a RF-023 | Badge publicado |
| Trabalho real | RF-030 a RF-046 | Entrega e aprovação |
| Renda imediata | RF-050 a RF-057 | Sats na Breez |
| Transparência | RF-060 a RF-072 | Recibo e painel |
| Confiabilidade | RF-080 a RF-082, RNF-010 a RNF-014 | Reset, retry e idempotência |
