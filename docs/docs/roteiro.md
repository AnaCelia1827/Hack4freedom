---
sidebar_position: 9
sidebar_label: Roteiro de implementação
---

# Roteiro de implementação

## Premissas

Este roadmap parte do estado verificado em 24 de julho de 2026. Ele considera
uma equipe pequena, com três pessoas desenvolvedoras e apoio parcial de produto,
design, segurança e jurídico. Com uma ou duas pessoas técnicas, os prazos devem
ser ampliados.

O plano prioriza primeiro identidade, autorização e persistência; depois
integrações sandbox; e somente então um piloto controlado. Hodle/Pix, capital de
liquidez real e expansão do marketplace não estão no caminho crítico do MVP.

## Linha do tempo

| Fase | Período | Resultado esperado |
|---|---|---|
| 0. Demo responsável | 24–25 jul. 2026 | jornada estável e claramente marcada como `MOCK` |
| 1. Consolidação e segurança crítica | 27 jul.–14 ago. | base única, autenticação verificável e rotas protegidas |
| 2. Persistência do produto | 17 ago.–11 set. | jornada sobrevive a reinícios e arquivos são privados |
| 3. Integrações em sandbox | 14 set.–9 out. | Nostr e Lightning funcionam ponta a ponta sem dinheiro real |
| 4. Preparação do piloto | 12–30 out. | operação, privacidade e segurança validadas |
| 5. Piloto controlado | 2–27 nov. | uso acompanhado e decisão documentada sobre modo real |
| 6. Evolução pós-piloto | a partir de 30 nov. | escala, doadores, liquidez e conversão opcional |

As datas são metas de planejamento, não compromissos de liberação. Uma fase só
termina quando seus critérios de saída forem atendidos.

## Fase 0 — Demo responsável

**Período:** 24 a 25 de julho de 2026.

Objetivo: apresentar o que existe com estabilidade e sem confundir simulação
com operação real.

### Entregas

- congelar mudanças funcionais de alto risco;
- integrar ou empacotar uma versão reproduzível da `bluejet-development`;
- executar os três jobs do pipeline de qualidade;
- preparar dados fictícios e um roteiro de demonstração;
- exibir `MOCK` em pagamento, carteira, impacto e liquidez;
- demonstrar o caminho de falha e recuperação, além do caminho feliz;
- registrar limitações conhecidas na apresentação.

### Critério de saída

A jornada completa é executada duas vezes em ambiente limpo, sem dado pessoal,
dinheiro real ou afirmação de integração inexistente.

## Fase 1 — Consolidação e segurança crítica

**Período:** 27 de julho a 14 de agosto de 2026.

Objetivo: transformar o protótipo em uma base única e eliminar vulnerabilidades
que impedem qualquer teste externo.

### Entregas

- definir branch de integração e política de revisão;
- reconciliar documentação, OpenAPI e rotas implementadas;
- verificar ID e assinatura dos eventos Nostr com biblioteca auditada;
- validar kind, domínio, timestamp, challenge e proteção contra replay;
- aplicar autenticação, papel e ownership a todas as rotas privadas;
- proteger rotas administrativas hoje expostas;
- remover senha do cadastro e limpar o `localStorage`;
- habilitar CORS restritivo, CSRF e rate limiting básico;
- dividir `app.py` em blueprints sem alterar as regras de domínio;
- criar testes de autorização por perfil e propriedade.

### Critério de saída

- todos os achados P0 da documentação de segurança estão fechados;
- OpenAPI representa as rotas públicas da versão;
- CI é obrigatório para merge;
- nenhuma operação financeira é criada por usuário não autorizado.

## Fase 2 — Persistência do produto

**Período:** 17 de agosto a 11 de setembro de 2026.

Objetivo: remover a dependência de memória e preservar a jornada depois de
reinícios ou múltiplas instâncias.

### Entregas

- modelar e migrar participantes, sessões e onboarding;
- persistir cursos, matrículas, tentativas e evidências;
- persistir empresas, tarefas, funding, reservas, entregas e revisões;
- persistir comunidade apenas quando necessária ao piloto;
- implementar expiração da reserva de vaga por job idempotente;
- integrar armazenamento de objetos privado;
- validar conteúdo, tamanho e MIME real de uploads;
- adicionar URLs temporárias, retenção e análise antimalware;
- ligar aprovação, obrigação e ledger na mesma fronteira transacional;
- ampliar testes de repositório, integração e recuperação após reinício.

### Critério de saída

Uma jornada iniciada antes de reiniciar API, worker e banco pode ser retomada
sem perda, duplicidade ou acesso cruzado entre participantes.

## Fase 3 — Nostr e Lightning em sandbox

**Período:** 14 de setembro a 9 de outubro de 2026.

Objetivo: substituir os mocks por adaptadores testáveis, ainda sem recursos
reais.

### Trilha Nostr

- implementar `NostrVerifier` e `BadgePublisher`;
- publicar badge NIP-58 somente após consentimento;
- registrar evento, relays consultados e confirmações;
- implementar retry idempotente e falha parcial por relay;
- publicar comunidade apenas com campos explicitamente públicos.

### Trilha Lightning

- definir e implementar a interface `LightningGateway`;
- escolher um provedor de sandbox após prova técnica curta;
- decodificar BOLT11 e validar rede, valor e expiração;
- persistir `payment_hash` sem expor invoice em logs;
- criar worker durável para `PayoutDispatchRequested`;
- implementar `PROCESSING`, `AMBIGUOUS`, `FAILED` e `SETTLED`;
- reconciliar timeout consultando o provedor antes de qualquer retry;
- gerar ledger e recibo apenas após resultado confirmado;
- testar concorrência entre requisições e worker.

### Critério de saída

Um teste automatizado cria a invoice sandbox, processa o outbox, simula timeout,
reconcilia o pagamento e prova que houve uma única liquidação e um único
recibo. Um badge consentido é confirmado por relays de teste.

Mais detalhes estão em
[Bitcoin, Lightning e Nostr](implementação/bitcoin.md).

## Fase 4 — Preparação do piloto

**Período:** 12 a 30 de outubro de 2026.

Objetivo: validar que produto, operação e proteção das participantes estão
prontos para um grupo fechado.

### Entregas

- testes ponta a ponta das jornadas de participante, revisor e administrador;
- auditoria de acessibilidade e testes em dispositivos móveis;
- observabilidade para sessão, outbox, pagamentos e divergência de ledger;
- painéis operacionais sem exposição de dados pessoais;
- backup, restauração e procedimento de continuidade testados;
- gestão e rotação de secrets;
- revisão de segurança independente e correção de achados críticos;
- aviso de privacidade, consentimentos, retenção e canal de atendimento;
- protocolo de suporte e incidente;
- treinamento das organizações revisoras;
- plano de pesquisa com participantes e critérios de interrupção.

### Critério de saída

O checklist de segurança está concluído, não há achado crítico aberto e a equipe
consegue detectar, interromper e reconciliar uma falha sem acessar chaves
privadas.

## Fase 5 — Piloto controlado

**Período:** 2 a 27 de novembro de 2026.

Objetivo: validar utilidade, segurança e operação com uma coorte pequena e
acompanhada.

### Estratégia

1. iniciar com dados e pagamentos sandbox;
2. acompanhar conclusão, abandono, suporte e tempo de revisão;
3. corrigir problemas de compreensão, acessibilidade e operação;
4. executar uma revisão `go/no-go`;
5. liberar micropagamentos reais apenas se todos os gates forem aprovados.

### Métricas do piloto

| Dimensão | Indicador |
|---|---|
| Jornada | proporção que conclui capacitação, tarefa e recebimento |
| Conversão em renda | participantes aprovadas e valor efetivamente liquidado |
| Experiência | tempo, abandono e pedidos de suporte por etapa |
| Qualidade | entregas aprovadas, corrigidas e rejeitadas |
| Financeiro | obrigações conciliadas, duplicidades e estados ambíguos |
| Segurança | acessos indevidos, incidentes e achados abertos |
| Operação | tempo de revisão e resolução de falhas |

Metas numéricas devem ser definidas com a organização piloto depois que tamanho
da coorte, tarefa e capacidade de suporte forem conhecidos.

### Gate para dinheiro real

O modo `REAL` permanece desabilitado se qualquer condição abaixo falhar:

- achado crítico ou alto sem mitigação;
- divergência entre provedor, obrigação, ledger e recibo;
- pagamento ambíguo sem processo de reconciliação;
- ausência de limites de tesouraria;
- backup ou restauração não testados;
- suporte, consentimento ou responsabilidade operacional indefinidos;
- pendência jurídica, contábil ou regulatória relevante.

## Fase 6 — Evolução pós-piloto

**A partir de 30 de novembro de 2026.**

A ordem deve ser definida pelos dados do piloto. Candidatos:

- painel e onboarding de empresas;
- painel de doadores e campanhas de fundo de impacto;
- mais trilhas, tarefas e critérios de elegibilidade;
- moderação Nostr e reputação verificável;
- Lightning Address e melhoria da carteira;
- capital de liquidez com contabilidade e risco próprios;
- integração Hodle/Pix, condicionada à viabilidade jurídica e operacional;
- automação de matching e relatórios agregados de impacto.

Capital de liquidez não deve financiar diretamente tarefas, e receita futura de
roteamento não deve ser apresentada como garantida.

## Caminho crítico

```text
base única e CI
  → autenticação e autorização
  → persistência e arquivos privados
  → gateway Lightning + worker + reconciliação
  → segurança, privacidade e operação
  → piloto sandbox
  → decisão sobre micropagamento real
```

Frontend adicional, Hodle/Pix, painel avançado de doadores e infraestrutura de
liquidez podem evoluir em paralelo somente se não retirarem capacidade desse
caminho crítico.

## Governança do roadmap

Ao final de cada fase:

1. demonstrar os critérios de saída;
2. registrar evidências de testes e riscos remanescentes;
3. atualizar o status da documentação;
4. revisar prazo, escopo e capacidade da fase seguinte;
5. decidir explicitamente entre avançar, corrigir ou reduzir escopo.

O roadmap deve ser revisado quinzenalmente. Itens sem responsável, critério de
aceite ou evidência verificável não devem ser considerados concluídos.
