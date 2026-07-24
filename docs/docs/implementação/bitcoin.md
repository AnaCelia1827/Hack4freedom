---
sidebar_position: 2
sidebar_label: Bitcoin, Lightning e Nostr
---

# Bitcoin, Lightning e Nostr

## Estado das integrações

A implementação atual prepara os limites de integração, mas não movimenta
Bitcoin nem publica eventos em relays. O modo financeiro efetivo do MVP é
`MOCK`.

| Capacidade | Estado | Evidência atual |
|---|---|---|
| Assinatura pelo navegador | **Parcial** | chamada NIP-07 a `getPublicKey` e `signEvent` |
| Verificação Nostr no servidor | **Parcial** | desafio e envelope são validados, assinatura criptográfica não |
| Badge NIP-58 | **Mock** | evidência recebe estado local `PUBLISH_PENDING` |
| Comunidade Nostr | **Mock** | IDs locais simulam eventos; não há publicação em relay |
| Invoice Lightning | **Mock** | API aceita uma string não vazia, sem decodificação BOLT11 |
| Pagamento Lightning | **Planejado** | não há Breez SDK, Core Lightning ou CLNRest no código |
| Conciliação | **Parcial** | existe modelo de estados; não há consulta a provedor real |
| Saída em reais | **Planejado** | nenhuma integração Hodle/Pix implementada |

## Identidade Nostr

### Fluxo atual

```text
SPA → POST /auth/nostr/challenges
API → challenge aleatório com validade de 5 minutos
SPA → extensão NIP-07 assina evento kind 22242
SPA → POST /auth/nostr/sessions
API → confere desafio, pubkey, conteúdo e assinatura recebida
API → cookie de sessão válido por 12 horas
```

O desafio é de uso único e não aceita material prefixado por `nsec`. Entretanto,
o backend ainda não recalcula o ID do evento nem verifica a assinatura Schnorr.
Assim, a autenticação demonstra o contrato NIP-07, mas não estabelece prova
criptográfica de posse da chave.

### Implementação necessária

Um adaptador `NostrVerifier` deve:

1. validar o formato do evento e a pubkey;
2. recalcular o ID conforme NIP-01;
3. verificar a assinatura;
4. exigir kind, timestamp, challenge e domínio esperados;
5. rejeitar eventos antigos, futuros ou reutilizados;
6. registrar somente metadados de auditoria, nunca a chave privada.

Referência: [repositório oficial de NIPs](https://github.com/nostr-protocol/nips).

## Badges e comunidade

A aprovação no quiz cria uma evidência interna de habilidade. A publicação de
badge exige consentimento, mas atualmente só muda o estado local para
`PUBLISH_PENDING`. A comunidade também permanece em memória e usa identificador
UUID no lugar de um evento Nostr real.

Para publicar em relays, o sistema precisa de um `BadgePublisher` que:

- produza o evento NIP-58 com o mínimo de informação;
- obtenha assinatura da autoridade emissora;
- envie a múltiplos relays com timeout;
- registre confirmações e falhas por relay;
- permita retry idempotente sem duplicar o badge.

Dados pessoais, localização, vulnerabilidade, entregas e valores individuais
não devem ser publicados em Nostr.

## Pagamento Lightning

### Modelo já implementado

A aprovação de uma entrega cria uma `PaymentObligation`. A participante informa
uma invoice e solicita um `PayoutAttempt` com `Idempotency-Key`.

No caminho PostgreSQL, a transação:

1. bloqueia a obrigação;
2. impede outra tentativa ativa;
3. cria a tentativa em `VALIDATED`;
4. muda a obrigação para `CLEARING`;
5. cria `PayoutDispatchRequested` no outbox;
6. confirma os três efeitos atomicamente.

Isso protege o banco contra duplicidade, mas ainda não dispara pagamento
externo.

### Estados operacionais

| Estado | Interpretação |
|---|---|
| `OPEN` | valor devido, sem tentativa ativa |
| `CLEARING` | tentativa em processamento ou aguardando conciliação |
| `SETTLED` | obrigação liquidada |
| `AMBIGUOUS` | houve timeout após possível envio; retry está bloqueado |
| `FAILED` / `EXPIRED` | tentativa terminal sem liquidação |

Uma resposta ambígua nunca deve produzir retry automático. O worker precisa
consultar o provedor pelo `payment_hash` antes de liberar nova tentativa.

## Arquitetura-alvo da integração

```text
API
 ├─ grava obrigação + attempt + outbox
 └─ responde sem chamar serviço externo

Worker de pagamentos
 ├─ reserva evento de outbox
 ├─ LightningGateway.validate(invoice)
 ├─ LightningGateway.pay(invoice, idempotency_key)
 ├─ persiste payment_hash e resultado
 └─ gera ledger + recibo ou marca AMBIGUOUS

Worker de reconciliação
 ├─ consulta LightningGateway.get_status(payment_hash)
 └─ conclui SETTLED/FAILED sem duplicar efeitos
```

O `LightningGateway` deve esconder o provedor concreto. Adaptadores possíveis
incluem [Core Lightning/CLNRest](https://docs.corelightning.org/docs/rest) para
tesouraria e [Breez SDK Spark](https://sdk-doc-spark.breez.technology/) para uma
experiência de carteira no cliente. A escolha final exige avaliação de custódia,
liquidez, disponibilidade regional, taxas e responsabilidades regulatórias.

## Ledger e reservas

O ledger usa partidas dobradas em satoshis. Cada transação precisa ter pelo
menos um débito e um crédito com totais iguais.

Exemplo de obrigação reconhecida:

| Conta | Direção | Valor |
|---|---|---:|
| `TASK_RESERVED` | débito | 10.000 sats |
| `PARTICIPANT_PAYABLE` | crédito | 10.000 sats |

A reserva financeira da tarefa é diferente da reserva temporária da vaga. Se a
vaga expira após 60 minutos, o funding continua reservado e pode sustentar uma
nova atribuição. Qualquer devolução exige lançamento compensatório explícito.

## Critérios para habilitar `SANDBOX`

- decodificação e validação real de BOLT11;
- adaptador de provedor com timeout e chave idempotente;
- worker durável para outbox;
- persistência de `payment_hash`, erros e respostas do provedor;
- reconciliação após reinício;
- autorização por propriedade da obrigação;
- testes concorrentes incluindo a chamada externa simulada;
- telemetria para fila parada, saldo e tentativas `AMBIGUOUS`.

## Critérios para habilitar `REAL`

Além dos itens de sandbox:

- revisão de segurança independente;
- segregação de tesouraria, limites por transação e por período;
- gestão de secrets fora do repositório;
- reserva de liquidez e alertas operacionais;
- procedimento de resposta a pagamento ambíguo;
- conciliação entre provedor, obrigações, ledger e recibos;
- aprovação jurídica, contábil e regulatória aplicável;
- identificação visível do modo real em API, interface e relatórios.

Até que esses critérios sejam atendidos, valores exibidos pela carteira e
impacto financeiro devem permanecer marcados como simulação.
