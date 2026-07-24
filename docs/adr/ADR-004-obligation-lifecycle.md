# ADR-004 — Ciclo de vida auditado da obrigação financeira

- Status: aprovado para implementação local/SANDBOX
- Data: 2026-07-24

## Contexto

Uma `PaymentObligation` precisa preservar para sempre a identidade da
atribuição, o valor, o modo e a data de criação, mas seu estado operacional
precisa avançar durante clearing e liquidação. Tratar toda a linha como
append-only impediria o fluxo aprovado no ADR-002; permitir updates livres
quebraria a auditabilidade financeira.

## Decisão

Os campos `assignment_id`, `amount_sats`, `mode` e `created_at` são imutáveis e
a obrigação não pode ser apagada ou truncada.

As únicas transições ordinárias são:

```text
OPEN → CLEARING → SETTLED
```

`SETTLED` é terminal. Uma obrigação em `CLEARING` pode voltar para `OPEN`
somente quando o attempt correspondente terminar em `FAILED` após resultado
conclusivo ou reconciliação. Esse retorno exige, na mesma transação:

- attempt terminal `FAILED`;
- evento de auditoria com motivo;
- lançamento compensatório de `LIGHTNING_CLEARING` para
  `PARTICIPANT_PAYABLE`.

Um attempt `AMBIGUOUS` mantém a obrigação em `CLEARING`, bloqueia novos
attempts e só pode transicionar para `SETTLED` ou `FAILED` por reconciliação.

O dispatch move contabilmente `PARTICIPANT_PAYABLE` para
`LIGHTNING_CLEARING`. A liquidação move `LIGHTNING_CLEARING` para `SETTLED`.
Nenhuma chamada de provider ocorre dentro da transação que mantém o lock da
obrigação.

## Consequências

- O histórico econômico continua imutável e reconstruível.
- Falhas são corrigidas por compensação, nunca pela edição de lançamentos.
- Triggers rejeitam transições impossíveis e updates de campos econômicos.
- Evidência SANDBOX não satisfaz critérios que exigem Lightning REAL.
