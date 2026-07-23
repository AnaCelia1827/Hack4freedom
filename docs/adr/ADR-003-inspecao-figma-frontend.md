# ADR-003 — Inspeção Figma obrigatória para o frontend

## Status

Aprovado

## Decisão

A Fase 9 deve utilizar o plugin/app da Figma conectado ao Codex e o arquivo
canônico [Bluejet no Figma](https://www.figma.com/design/TyhhDZgTJ4jqqKfnq1jdNZ/hack4frredom?node-id=0-1).
Antes de qualquer implementação visual, o Codex deve inspecionar pelo plugin
frames, componentes, estilos, tokens, dimensões, grids, tipografia e assets.

Screenshots são somente evidência de validação visual posterior. O Figma define
apresentação e interação visual; `docs/requisitos.md`, ADRs e OpenAPI definem
comportamento, estados e regras de negócio. Em conflito, os requisitos
prevalecem e a divergência deve ser registrada.

Assets devem ser exportados pelo plugin ou recriados em código apenas quando
forem elementos simples. Nenhuma tela pode ser implementada por aproximação
antes da auditoria do Figma.

## Consequências

O Figma Inspection Gate é obrigatório para iniciar e concluir a Fase 9. O
relatório deve registrar os IDs e propriedades dos elementos inspecionados.
Esta decisão é documental e não autoriza alterações de código nesta etapa.
