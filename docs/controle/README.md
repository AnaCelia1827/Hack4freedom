# LARES Verificável — control plane do Bluejet

O LARES conecta fontes canônicas, autorização, execução, evidência e status.
Ele não substitui requisitos, ADRs, OpenAPI, Figma, código ou testes. Sua função
é impedir que uma tarefa seja declarada concluída sem lastro reproduzível.

## Invariante central

```text
Quem define o escopo não pode controlar sozinho a execução, a prova e o veredito.
```

Para S2 e S3, executor e verificador devem ser pessoas ou agentes distintos. Uma
operação S3 também exige aprovação humana específica, limitada ao commit,
ambiente, efeito externo, valor e validade declarados.

## Arquitetura

```text
Scope Baseline + Source/Claim Registry
                  ↓
              Work Item
                  ↓
        Authorization Envelope
                  ↓
            Run Manifest
                  ↓
           Evidence Bundle
                  ↓
       Adversarial Challenge
                  ↓
          Gate Decision
                  ↓
        Status Projection
```

## Planos de controle

### Policy Plane

- `source-registry.json`: autoridade, vigência e fingerprint das fontes;
- `scope-baseline.json`: escopo imutável da release e golden path;
- `risk-policy.json`: risco mínimo e segregação de funções;
- `divergences/`: conflitos que nunca podem ser resolvidos silenciosamente;
- `gates/`: gates de jornada e release.
- `schemas/`: contratos serializados dos registros;
- `templates/`: modelos de novos registros, sem valor probatório próprio.
- `prompts/lares-system-prompt.md`: bootstrap completo para novos agentes.

### Authorization Plane

- `authorizations/`: escopo, paths, operações, ambiente, efeitos externos,
  validade e aprovador.

Uma autorização de conversa ou tarefa não autoriza automaticamente commit,
push, deploy, migration de produção, publicação Nostr ou pagamento real.

### Execution Plane

- `work-items/`: resultado esperado, requisitos, dependências, refutação e
  recuperação;
- `runs/`: commit, árvore, comandos, arquivos alterados e resultado observável.
- `challenges/`: tentativas estruturadas de refutar claims e controles.

Um workspace sujo pode produzir investigação e verificação local, mas não
aceite reproduzível.

### Evidence and Status Plane

- `evidence/`: metadados sanitizados, claims, ambiente e limitações;
- `gate-decisions/`: aceite ou rejeição assinada pelo papel competente;
- `supersessions/`: correções append-only de registros anteriores;
- `incidents/`: contenção e recuperação de falhas materializadas;
- `status.md`: projeção gerada e descartável.

O Git nunca deve conter invoice completa, nsec, token, rune, entrega privada,
URL assinada ou resposta bruta de provider. Evidência sensível deve permanecer
em storage privado; o repositório armazena apenas hash e referência opaca.

## Ciclo obrigatório

```text
LER → ENQUADRAR → LASTREAR → AUTORIZAR
→ EXECUTAR → FALSIFICAR → VERIFICAR → DECIDIR → PROJETAR STATUS
```

1. **Ler:** carregar `AGENTS.md` e as fontes apontadas neste diretório.
2. **Enquadrar:** declarar escopo, premissas, risco, ações permitidas e condições
   de parada.
3. **Lastrear:** criar ou atualizar o Work Item.
4. **Autorizar:** comprovar que o envelope cobre exatamente a execução.
5. **Executar:** trabalhar no commit e ambiente declarados.
6. **Falsificar:** procurar contraexemplos, concorrência, fronteiras e modos
   incorretos.
7. **Verificar:** produzir evidência por claim, com limitações.
8. **Decidir:** registrar GateDecision; `ACEITO` nunca é digitado no Work Item.
9. **Projetar status:** regenerar `status.md`.

## Classes de risco

| Classe | Exemplos | Controle mínimo |
| --- | --- | --- |
| S0 | leitura e documentação | fonte, objetivo e verificação |
| S1 | código local reversível | diff, testes e recovery |
| S2 | auth, dados privados, migration, ledger | verificador independente e teste de falha |
| S3 | produção, xpay, deploy, efeito irreversível | autorização específica, dupla revisão e evidência externa |

O risco é derivado por `risk-policy.json`. O executor pode elevá-lo, mas não
reduzi-lo unilateralmente.

## Estados

O Work Item usa estados de preparação e execução:

```text
CAPTURADO → LASTREADO → PRONTO → EM_EXECUCAO → EM_VERIFICACAO
```

Estados laterais: `EM_VERIFICACAO_LOCAL`, `EM_RISCO`, `BLOQUEADO`,
`CANCELADO`.

O estado `ACEITO_NO_COMMIT` só é projetado quando existe uma GateDecision
válida, com evidências para o mesmo commit e uma run reproduzível.

## Comandos

```bash
python tools/lares/lares.py doctor
python tools/lares/lares.py validate
python tools/lares/lares.py meta-test
python -m unittest discover -s tools/lares -p 'test_*.py'
python tools/lares/lares.py status --check
python tools/lares/lares.py workspace-fingerprint \
  --exclude docs/controle/runs \
  --exclude docs/controle/evidence \
  --exclude docs/controle/status.md
```

Depois de alterar registros:

```bash
python tools/lares/lares.py status --write
```

No CI, `doctor --strict` impede aceite baseado em workspace sujo.

## REAL, SANDBOX e MOCK

O modo é proveniência, não decoração. Deve estar presente em obligation,
attempt, provider event, provider payment, ledger, recibo, read model, run e
evidence bundle.

- `MOCK` nunca satisfaz requisito marcado como `REAL`;
- resposta de `xpay` não substitui reconciliação por `listpays`;
- screenshot não substitui ledger;
- teste in-memory não prova lock PostgreSQL;
- pagamento liquidado não possui rollback, somente reconciliação ou
  compensação append-only.

## Controle do enquadramento, não do pensamento privado

O protocolo não solicita chain-of-thought. Ele torna observáveis fontes,
premissas, desconhecidos, alternativas, condições de refutação, ações,
resultados e evidências. O objetivo é controlar a decisão e a execução
observáveis, não prometer acesso à cognição privada do agente.

Para operar o método em outra sessão, use
`prompts/lares-system-prompt.md` como prompt-base e mantenha o `AGENTS.md` na
raiz como bootstrap automático do repositório.
