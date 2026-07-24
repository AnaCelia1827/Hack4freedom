# Migrações do banco

As migrações Alembic da API modular ficam neste diretório. A revisão
`0001_platform` cria outbox, inbox de providers e auditoria.
`0002_financial_foundation` adiciona obrigação, attempt exclusivo, ledger e
triggers append-only. `0003_financial_invariants` acrescenta constraint triggers
diferidos que rejeitam transações de ledger vazias ou desbalanceadas no commit.
`0004_ledger_closure` permite entries somente na mesma transação de banco que
criou a LedgerTransaction, impedindo anexos retroativos.
`0005_runtime_role_hardening` cria o papel NOLOGIN `bluejet_runtime`, concede
somente operações necessárias e protege ledger/audit contra `TRUNCATE`. O login
da aplicação deve herdar esse papel e não pode ser owner do schema. Migrações
financeiras são forward-only: correções usam uma nova revisão, nunca downgrade
destrutivo.
`0006_identity_persistence` adiciona usuários, challenges e sessões da
participante. Apenas hashes SHA-256 do challenge e do token são persistidos; o
papel runtime não recebe `DELETE`, `TRUNCATE` ou DDL nessas tabelas.
`0007_platform_runtime` persiste o draft de onboarding e adiciona lease ao
outbox. Consumidores reservam eventos com `FOR UPDATE SKIP LOCKED`; conclusão do
onboarding, evento de domínio e auditoria são gravados atomicamente.

Este é o primeiro slice do `WI-DB-001`; os demais agregados in-memory ainda
precisam ser migrados antes de considerar o Work Item concluído.
