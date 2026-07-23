# Migrações do banco

As migrações Alembic da API modular ficam neste diretório. A revisão
`0001_platform` cria as tabelas append-only de outbox, inbox de providers e
auditoria. O schema de domínio e o ledger PostgreSQL ainda pertencem ao
`WI-DB-001` e não devem ser considerados concluídos por esta migration inicial.
