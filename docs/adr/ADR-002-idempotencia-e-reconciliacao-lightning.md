# ADR-002 — Idempotência e reconciliação de pagamentos Lightning

- Status: aprovado
- Data: 2026-07-22

## Contexto

Uma idempotency key evita repetição da mesma requisição, mas não impede duas requisições concorrentes com keys e invoices diferentes para a mesma obrigação. Um timeout após `xpay` também pode ocultar um pagamento já liquidado.

## Decisão

Uma `PaymentObligation` possui no máximo um `PayoutAttempt` ativo por vez.

O fluxo de criação deve:

1. validar a invoice BOLT11 antes da transação financeira;
2. iniciar transação de banco;
3. obter lock pessimista `SELECT ... FOR UPDATE` na obrigação ou aplicar compare-and-swap por versão;
4. exigir que a obrigação esteja `OPEN`;
5. criar o attempt;
6. transicionar a obrigação para `CLEARING`;
7. criar `PayoutDispatchRequested` no outbox;
8. confirmar attempt, obrigação e outbox na mesma transação.

O banco deve aplicar unicidade parcial equivalente a:

```sql
UNIQUE (payment_obligation_id)
WHERE status IN ('CREATED', 'VALIDATED', 'PROCESSING', 'AMBIGUOUS')
```

Regras adicionais:

- mesma idempotency key retorna o attempt original;
- key diferente enquanto houver attempt ativo retorna conflito ou o attempt ativo;
- attempts terminais são preservados no histórico;
- retry só ocorre após `FAILED`, `EXPIRED` ou reconciliação explícita;
- timeout após possível envio produz `AMBIGUOUS`;
- `AMBIGUOUS` bloqueia retry, mantém a obrigação em `CLEARING` e gera alerta;
- reconciliação por `listpays` conclui como `SETTLED` ou `FAILED`;
- somente após `FAILED` reconciliado a obrigação pode voltar a `OPEN`, com lançamento compensatório quando necessário;
- um attempt nunca volta diretamente de `AMBIGUOUS` para `CREATED`.

## Consequências

- Idempotência existe nos níveis de requisição, obrigação, payment hash, provider event e efeito externo.
- O worker só chama `xpay` para um outbox despachável e ainda não processado.
- O teste concorrente deve comprovar uma única transação, um único outbox e uma única chamada `xpay`.

