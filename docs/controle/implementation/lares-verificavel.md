# Implementation Handoff: LARES Verificável Git-native

## Selected Design And Constraints

A opção selecionada mantém o Git como registro inicial, usa JSON versionado e
um CLI sem dependências externas. Ela não tenta fornecer imutabilidade forte de
um serviço WORM; S3 continuará exigindo evidência externa e aprovação da
plataforma.

## Source Revision And Drift Check

- Base observada: `8163f80d3d6a00e29702f6d4c034c5dfd3e77b51`.
- O workspace já estava sujo e a `origin/main` estava à frente.
- Esta implementação permanece `EM_VERIFICACAO_LOCAL` até existir commit
  candidato e CI em checkout limpo.

## Affected Components

- `AGENTS.md`;
- `docs/controle/`;
- `tools/lares/`;
- `.github/workflows/lares.yml`;
- `.github/PULL_REQUEST_TEMPLATE/lares.md`;
- `.gitignore`.

## Implemented Control Surface

- registro de fontes/claims com SHA-256 e detecção de drift;
- baseline completo dos 159 IDs atuais e golden path 1–17;
- risco mínimo derivado, com path desconhecido em fail-closed S3;
- envelopes de autorização vinculados a commit, paths e operações;
- Work Items, Runs, Evidence, Challenges, GateDecisions, Divergences,
  Incidents e Supersessions;
- schemas e templates versionados;
- scanner preventivo de nsec, BOLT11, credenciais e chaves privadas;
- impedimento de MOCK para claims REAL;
- separação entre executor, verificador e aprovadores S3;
- JourneyGate que exige cobertura das claims, mesmo commit e revalidação quando
  o HEAD diverge;
- status determinístico, meta-testes, testes unitários, CI e template de PR.

O primeiro registro de execução é `RUN-20260722-LARES-001`. Por ter sido
produzido em workspace preexistente sujo, ele resulta em
`PASS_WITH_LIMITATIONS` e não gera `GateDecision ACCEPT`.

## Ordered Work Packages

1. Registry e baseline.
2. Risk policy e autorização.
3. Work Items, Runs, Evidence e Gates.
4. Validator, status projection e meta-tests.
5. AGENTS/system prompt.
6. CI e template de PR.
7. Validação em commit limpo.

## Compatibility And Migration

O protocolo não altera código do produto. PLAN, requisitos, ADRs, OpenAPI e
Figma continuam em seus locais. O status histórico manual não é importado como
aceite; ele entra como claim ou divergência até receber evidência reproduzível.

## Tactical Protections During Migration

- nenhum Work Item começa como aceito;
- golden path começa não pronto;
- divergências conhecidas bloqueiam release;
- evidência local suja é marcada `LOCAL_ONLY`;
- S2/S3 exige separação de funções.

## Tests And Security Validation

- parser e referências JSON;
- fingerprints de fontes;
- IDs atuais de requisitos;
- risco mínimo por path/operação;
- MOCK rejeitado para claim REAL;
- scanner de evidência sensível;
- status determinístico;
- workspace sujo não produz ACCEPT;
- meta-testes do próprio protocolo.

Comandos canônicos e resultados da execução inicial estão no RunManifest. O
hash do workspace exclui `runs/`, `evidence/` e `status.md` para eliminar ciclo
autorreferente; o escopo exato do hash permanece registrado na run.

## Performance And Resource Benchmarks

O custo esperado é linear no número de manifestos e no tamanho das fontes
fingerprinted. O CI deve medir o tempo total; a meta inicial é permanecer abaixo
de cinco segundos sem dependências de rede.

## Rollout And Rollback

Rollout incremental: primeiro Git/status, depois CI, depois enforcement em PR e,
por fim, evidência externa para S3. Rollback técnico remove o workflow e o CLI,
sem alterar fontes canônicas ou dados de produto.

## Acceptance Criteria

- validator e unit tests passam;
- status check passa;
- CI usa checkout limpo;
- system prompt aponta para todas as fontes;
- JOURNEY-GP-001 permanece não pronto sem evidência;
- nenhuma claim local é promovida indevidamente a aceite reproduzível.

## Open Decisions

- mecanismo de assinatura de GateDecision S3;
- storage privado/WORM para evidências financeiras;
- identidade de CODEOWNERS para produto, segurança e pagamentos;
- integração futura do status ao Docusaurus após resolver a estrutura de docs.
