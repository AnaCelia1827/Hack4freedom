---
sidebar_position: 2
sidebar_label: Arquitetura da Solução
---

# Arquitetura da solução

## Introdução

A arquitetura é apresentada com o **Modelo C4**, que organiza a solução em níveis de abstração:

- **C1 — Contexto:** sistema, usuários e dependências externas;
- **C2 — Contêineres:** aplicações e armazenamentos;
- **C3 — Componentes:** responsabilidades internas;
- **C4 — Código:** implementação detalhada no repositório.

Esta documentação cobre os três primeiros níveis. Entidades, estados e regras são apresentados de forma resumida nesta página e detalhados junto à implementação.

## Princípios

- experiência mobile-first;
- complexidade de Nostr e Lightning oculta da participante;
- dados privados fora de redes públicas;
- separação entre tarefa, matching, liquidez e bônus;
- pagamentos idempotentes e falhas recuperáveis;
- integrações identificadas como `REAL`, `SANDBOX` ou `MOCK`.

## Nível 1: contexto do sistema

O nível C1 mostra quem utiliza a plataforma e de quais sistemas externos ela depende.

```text
Participante ───────┐
ONG / Revisor ──────┤
Empresa parceira ───┼──> Plataforma ──> Nostr
Patrocinador ───────┤         │
Administrador ──────┘         ├───────> Bitcoin / Lightning
                              └───────> Hodle / Pix
```

*Fonte: produzido pelos autores (2026).*

### Atores

| Ator | Responsabilidade |
|---|---|
| Participante | Aprender, executar tarefas, receber e controlar a publicação de badges |
| Organização parceira | Convidar, orientar e acompanhar participantes |
| Revisor | Avaliar entregas e registrar decisão justificada |
| Empresa parceira | Fornecer e financiar tarefas reais |
| Patrocinador | Financiar impacto ou liquidez e acompanhar resultados |
| Administrador | Configurar conteúdo, recursos, integrações e conciliação |

### Sistemas externos

| Sistema | Uso |
|---|---|
| Signer e relays Nostr | Autenticação e publicação consentida de badges |
| Breez SDK Spark | Carteira controlada pela participante |
| Core Lightning/CLNRest | Tesouraria e pagamentos Lightning |
| Rede Bitcoin/Lightning | Liquidação e roteamento |
| Hodle/Pix | Conversão opcional entre Bitcoin e reais |

A plataforma mantém regras, estados e dados privados. Sistemas externos confirmam operações específicas, mas não são a única fonte de verdade do processo.

## Nível 2: contêineres

No C4, “contêiner” significa uma aplicação executável ou armazenamento, não necessariamente Docker.

```text
┌──────────────── PWA React ────────────────┐
│ participante │ revisão │ administração   │
└───────────────┬───────────┬───────────────┘
                │ HTTPS     │ signer/carteira
                v           v
┌──────────────── Backend Flask ────────────┐
│ identidade │ cursos │ tarefas │ financeiro│
│ revisão    │ badges │ ledger  │ painéis   │
└──────────┬──────────────┬─────────────────┘
           v              v
       SQLite          Gateways
                    Nostr │ Lightning │ Pix
```

*Fonte: produzido pelos autores (2026).*

| Contêiner | Tecnologia | Responsabilidade |
|---|---|---|
| PWA | React e Vite | Interface mobile, formulários, signer e carteira |
| Backend | Python e Flask | APIs, autorização e regras de negócio |
| Banco | SQLite e SQLAlchemy | Dados operacionais, estados e ledger |
| Jobs | Processamento assíncrono simples | Retry, webhooks e conciliação |
| Carteira | Breez SDK Spark | Recebimento e controle dos satoshis |
| Tesouraria | Core Lightning | Pagamento de cobranças e métricas |
| Relays | Nostr | Distribuição de eventos públicos |
| Gateway fiat | Hodle/Pix | Cotação e conversão opcional |

### Decisão do MVP

O backend é um **monólito modular**. Essa escolha reduz a complexidade de implantação e permite transações consistentes entre reserva, obrigação e ledger. Microsserviços só devem ser considerados quando escala ou autonomia de equipes justificarem o custo adicional.

SQLite atende ao cenário controlado do MVP. Produção pode evoluir para PostgreSQL, armazenamento de objetos e fila durável sem alterar os limites de domínio.

## Nível 3: componentes

### PWA

| Componente | Função |
|---|---|
| Aprendizagem | Trilhas, avaliações e progresso |
| Marketplace | Tarefas elegíveis, reserva e submissão |
| Carteira e recibos | Cobrança, pagamento e opção Pix |
| Revisão | Critérios, aprovação e correção |
| Painéis | Impacto, financiamento e administração |
| Adaptadores | Comunicação com API, Nostr e Breez |

### Backend

| Componente | Função |
|---|---|
| Identidade | Desafio Nostr, validação e sessão |
| Aprendizagem | Tentativas, conclusão e desbloqueio |
| Trabalho e revisão | Tarefas, reservas, entregas e decisões |
| Financiamento e ledger | Fontes, reservas, lançamentos e recibos |
| Orquestrador de pagamento | Validação, idempotência, liquidação e retry |
| Publicador de badges | Consentimento, assinatura e publicação em relays |
| Relatórios e auditoria | Indicadores, conciliação e histórico |

As integrações são acessadas por gateways internos:

```text
NostrGateway      → autenticação e badges
LightningGateway  → validação e pagamento
FiatGateway       → cotação e saída Pix
```

Cada gateway pode ter implementação real, sandbox ou simulada sem alterar as regras centrais.

## Fluxos críticos

### Autenticação

```text
PWA solicita desafio
    → signer assina evento
    → backend verifica nonce, assinatura e expiração
    → sessão é criada
```

A chave privada permanece no signer. Mais detalhes estão em [Identidade e Reputação](identidade.md).

### Tarefa e pagamento

```text
tarefa financiada → reserva → entrega → revisão
                  → obrigação → pagamento → ledger → recibo
```

A aprovação cria uma obrigação. Invoice expirada ou falha temporária não elimina o valor devido, e novas tentativas utilizam idempotência.

### Badge

```text
conclusão → concessão interna → consentimento
          → publicação NIP-58 → confirmação dos relays
```

Falha de publicação não bloqueia tarefa ou pagamento.

## Segurança e privacidade

| Risco | Controle |
|---|---|
| Vazamento de chave | Chave privada nunca chega ao backend |
| Replay de login | Nonce de uso único e expiração |
| Pagamento duplicado | Idempotência e unicidade |
| Webhook falso | Verificação e reprocessamento seguro |
| Exposição em relay | Campos permitidos e consentimento |
| Mistura de recursos | Fontes tipadas e ledger append-only |
| Falha externa | Timeout, retry e estado recuperável |
| Simulação ambígua | Identificação obrigatória do modo |

Dados pessoais, situação de vulnerabilidade, localização e conteúdo da entrega permanecem fora do Nostr.

## Escopo do MVP

| Elemento | Modo |
|---|---|
| Capacitação, tarefa e revisão | `REAL` |
| Assinatura Nostr e badge | `REAL`, com fallback identificado |
| Pagamento Lightning | `REAL` ou `SANDBOX` |
| Conversão Pix | Condicional |
| Histórico de canais e roteamento | `MOCK` |
| Projeção de bônus | `MOCK` até existir receita conciliada |

O nível C4 é representado pelo código, pelos requisitos e pela documentação específica de frontend, backend, Bitcoin e segurança.
