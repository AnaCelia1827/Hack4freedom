# Status verificável do Bluejet

> Este arquivo é gerado por `python tools/lares/lares.py status --write`.
> Não o edite manualmente.

- Baseline: `SCOPE-BLUEJET-MVP-2026-07`
- Data de corte do baseline: `2026-07-22`
- Release: `Bluejet MVP — Demo Day`
- Pronta para release: `NÃO`
- Cobertura lastreada: `23/159` requisitos obrigatórios
- Divergências bloqueantes abertas: `4`

## Work Items

| Work Item | Estado verificável | Risco | Requisitos |
| --- | --- | --- | --- |
| `WI-DB-001` — Tornar PostgreSQL a fonte persistente do domínio | EM_VERIFICACAO_LOCAL | S2 | RNF-007, RNF-008, RNF-009, RNF-010, RNF-011, CA-012, CA-013 |
| `WI-GIT-001` — Preservar a implementação local em commits revisáveis | ACEITO_NO_COMMIT a9dd9a989158 | S2 | RNF-019 |
| `WI-GIT-002` — Publicar a branch e integrar a main remota | EM_EXECUCAO | S2 | RNF-019 |
| `WI-ID-001` — Fechar identidade Nostr e onboarding persistente | LASTREADO | S2 | RF-001, RF-002, RF-003, RNF-001, CA-001 |
| `WI-JOURNEY-001` — Comprovar golden path integrado | LASTREADO | S3 | CA-001, CA-002, CA-003, CA-004, CA-005, CA-006, CA-007, CA-011, CA-012, CA-013, CA-014, CA-015 |
| `WI-LARES-001` — Implantar o LARES Verificável | EM_VERIFICACAO_LOCAL | S1 | RNF-019, RNF-020 |
| `WI-LARES-002` — Restaurar fingerprint canônico do prompt LARES | EM_VERIFICACAO_LOCAL | S1 | RNF-019, RNF-020 |

## Gates da release

| Gate | Estado | Evidências/etapas |
| --- | --- | --- |
| `JOURNEY-GP-001` | NAO_PRONTO | 0/17 |

## Divergências bloqueantes

- `DIV-DATABASE-001` — PostgreSQL canônico versus SQLite e serviços in-memory: Executar WI-DB-001 e atualizar documentos candidatos sem alterar retroativamente os requisitos.
- `DIV-GIT-001` — Branch publicada e CI reproduzível; main ainda não integrada: Emitir autorização separada para atualizar origin/main, analisar os commits exclusivos e realizar merge não destrutivo somente após registrar conflitos e recovery.
- `DIV-LIGHTNING-001` — Pagamento real exigido versus adapter MOCK: Conectar PostgreSQL, CLNRest privado, xpay e listpays sob autorização S3 específica.
- `DIV-OPENAPI-001` — OpenAPI não representa todo o runtime Flask: Criar comparação automática de rotas e contract tests bidirecionais.

## Requisitos ainda sem Work Item

`CA-008`, `CA-009`, `CA-010`, `RF-004`, `RF-005`, `RF-006`, `RF-007`, `RF-008`, `RF-009`, `RF-010`, `RF-011`, `RF-012`, `RF-013`, `RF-014`, `RF-015`, `RF-016`, `RF-017`, `RF-018`, `RF-019`, `RF-020`, `RF-021`, `RF-022`, `RF-023`, `RF-024`, `RF-025`, `RF-026`, `RF-027`, `RF-028`, `RF-029`, `RF-030`, `RF-031`, `RF-032`, `RF-033`, `RF-034`, `RF-035`, `RF-036`, `RF-037`, `RF-038`, `RF-039`, `RF-040`, `RF-041`, `RF-042`, `RF-043`, `RF-044`, `RF-045`, `RF-046`, `RF-047`, `RF-048`, `RF-049`, `RF-050`, `RF-051`, `RF-052`, `RF-053`, `RF-054`, `RF-055`, `RF-056`, `RF-057`, `RF-058`, `RF-059`, `RF-060`, `RF-061`, `RF-062`, `RF-063`, `RF-064`, `RF-065`, `RF-066`, `RF-067`, `RF-068`, `RF-069`, `RF-070`, `RF-071`, `RF-072`, `RF-073`, `RF-074`, `RF-075`, `RF-076`, `RF-077`, `RF-078`, `RF-079`, `RF-080`, `RN-001`, `RN-002`, `RN-003`, `RN-004`, `RN-005`, `RN-006`, `RN-007`, `RN-008`, `RN-009`, `RN-010`, `RN-011`, `RN-012`, `RN-013`, `RN-014`, `RN-015`, `RN-016`, `RN-017`, `RN-018`, `RN-019`, `RN-020`, `RN-021`, `RN-022`, `RN-023`, `RN-024`, `RN-025`, `RN-026`, `RN-027`, `RN-028`, `RN-029`, `RN-030`, `RN-031`, `RN-032`, `RN-033`, `RN-034`, `RN-035`, `RN-036`, `RN-037`, `RN-038`, `RN-039`, `RN-040`, `RN-041`, `RN-042`, `RN-043`, `RN-044`, `RNF-002`, `RNF-003`, `RNF-004`, `RNF-005`, `RNF-006`, `RNF-012`, `RNF-013`, `RNF-014`, `RNF-015`, `RNF-016`, `RNF-017`, `RNF-018`
