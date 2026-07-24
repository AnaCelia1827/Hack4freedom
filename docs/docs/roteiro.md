---
sidebar_position: 9
sidebar_label: Roteiro de implementação
---

# Roadmap

## Premissas do planejamento

O roadmap parte de uma versão funcional que já possui **autenticação Nostr
segura de ponta a ponta** e **pagamento Lightning real**. As próximas etapas
priorizam confiabilidade, validação com usuárias e organizações, sustentabilidade
financeira e crescimento responsável.

As metas abaixo são referências de planejamento. Devem ser revisadas
trimestralmente conforme capacidade da equipe, financiamento, resultados do
piloto e riscos identificados.

## Fase 1: Validação e MVP — meses 1 a 12

Esta fase é sustentada por recursos de hackathon, grants, doações institucionais
e eventual rodada pre-seed. O objetivo é validar o *Product-Market Fit*,
comprovar que capacitação pode ser convertida em renda e tornar o ciclo Nostr e
Lightning seguro, persistente e operável.

| Foco estratégico | Prioridade de implementação técnica | Marcos de negócio e financeiros |
|---|---|---|
| **Segurança e confiabilidade** | **Identidade e autorização:** consolidar verificação Nostr, sessões persistentes, controle por papel e propriedade, proteção CSRF, rate limiting e auditoria. | **Piloto seguro:** concluir revisão independente sem achado crítico aberto e operar sem acesso indevido ou exposição de chave privada. |
| **Persistência da jornada** | **Core da plataforma:** persistir capacitação, evidências, tarefas, reservas, entregas e revisões em PostgreSQL; armazenar arquivos em ambiente privado. | **Continuidade operacional:** 100% das jornadas essenciais retomáveis após reinício, sem perda ou duplicidade. |
| **Pagamento real confiável** | **Serviço financeiro:** fortalecer validação BOLT11, outbox, worker, idempotência, ledger, recibos e reconciliação de pagamentos `AMBIGUOUS`. | **Prova de valor:** pelo menos 99% dos pagamentos concluídos ou reconciliados corretamente e nenhuma liquidação duplicada. |
| **Identidade e reputação** | **Serviço Nostr:** publicar badges NIP-58 após consentimento, registrar confirmações por relay e implementar retry idempotente. | **Reputação verificável:** primeiras participantes com capacitação e badge verificáveis sem exposição de dados sensíveis. |
| **Validação com participantes** | **Experiência web:** melhorar acessibilidade, onboarding, linguagem financeira, suporte mobile e testes ponta a ponta. | **Validação de uso:** piloto com até 100 participantes, acompanhado por organizações parceiras, medindo conclusão, abandono e suporte. |
| **Oferta de trabalho** | **Marketplace inicial:** consolidar cadastro, funding, elegibilidade, reserva de vaga, entrega e revisão de tarefas reais. | **Conversão em renda:** pelo menos 30 tarefas remuneradas concluídas e liquidadas durante o piloto. |
| **Parcerias e funding** | **Painel operacional mínimo:** visão separada para organização, empresa e financiador, com valores realizados distintos de simulações. | **Ecossistema inicial:** validar operação com 2 a 3 organizações e 3 a 5 empresas ou financiadores parceiros. |
| **Privacidade e conformidade** | **Governança de dados:** retenção, consentimento, exclusão, gestão de secrets, backup e resposta a incidentes. | **Prontidão institucional:** política de privacidade, responsabilidades operacionais e processo de suporte definidos antes de ampliar o piloto. |

### Critério de conclusão da Fase 1

A fase termina quando a jornada abaixo puder ser repetida com dados persistentes,
controle de acesso, evidência auditável e pagamento conciliado:

```text
login Nostr → capacitação → tarefa → entrega → revisão
            → pagamento Lightning → ledger → recibo
```

Além do funcionamento técnico, o piloto precisa demonstrar que participantes
compreendem a jornada, organizações conseguem operá-la e empresas percebem valor
nas tarefas entregues.

## Fase 2: Escala e sustentabilidade — meses 13 a 36

Esta fase concentra crescimento no Brasil, retenção de participantes e
organizações, aumento da oferta de trabalho e redução da dependência de doações.
A arquitetura deve escalar de forma incremental: o monólito modular permanece
como base, e serviços independentes são extraídos apenas quando volume,
segurança ou operação justificarem.

| Foco estratégico | Prioridade de implementação técnica | Marcos de negócio e financeiros |
|---|---|---|
| **Escala operacional** | **Plataforma e workers:** filas duráveis, observabilidade, autoscaling, recuperação de falhas e separação dos serviços financeiros e de publicação Nostr. | **Confiabilidade:** disponibilidade mensal superior a 99,5% nos fluxos críticos e pagamento corretamente conciliado em mais de 99,5% dos casos. |
| **Retenção e progressão profissional** | **Learning e reputação:** novas trilhas, níveis de habilidade, histórico verificável e recomendação de tarefas por elegibilidade. | **Retenção:** aumentar recorrência de capacitação e proporção de participantes que concluem mais de uma tarefa remunerada. |
| **Oferta B2B** | **Portal de empresas:** criação de campanhas, gestão de tarefas, critérios de revisão, contratos, faturamento e APIs de integração. | **Receita recorrente:** contratos B2B e taxas de serviço passam a financiar parte crescente da operação. |
| **Fundo de impacto** | **Contas e campanhas:** separar aportes, reservas, matching, recompensas e saldo disponível no ledger. | **Transparência:** 100% dos recursos vinculados a finalidade, origem e impacto conciliáveis. |
| **Capital e infraestrutura Lightning** | **Tesouraria e liquidez:** monitoramento de nó, canais, reservas, custos, routing fees e limites de risco, sempre separados do fundo de impacto. | **Validação financeira:** comprovar receitas e custos realizados antes de destinar qualquer resultado líquido a incentivos. |
| **Conversão opcional para reais** | **Gateway fiat:** avaliar e integrar Hodle/Pix com cotação, consentimento, limites, status e reconciliação. | **Acessibilidade financeira:** oferecer saída em reais somente após validação jurídica, operacional e de demanda. |
| **Impacto e ESG** | **API de relatórios:** indicadores agregados de capacitação, trabalho, renda e financiamento, com proteção contra reidentificação. | **Monetização institucional:** relatórios e serviços para empresas e patrocinadores tornam-se uma fonte recorrente de receita. |
| **Expansão nacional** | **Configuração multi-organização:** permissões, conteúdo, campanhas e relatórios isolados por parceiro. | **Escala:** alcançar pelo menos 1.000 participantes e uma rede ativa de organizações e empresas em mais de uma região brasileira. |
| **Sustentabilidade** | **FinOps e métricas unitárias:** acompanhar custo por participante, tarefa, pagamento, suporte e parceiro. | **Equilíbrio operacional:** alcançar receita recorrente e financiamento contratado suficientes para cobrir a operação principal até o final da fase. |

### Critério de conclusão da Fase 2

A plataforma deve demonstrar que consegue crescer sem misturar recursos,
comprometer a segurança ou depender exclusivamente de novas doações para manter
a operação principal.

As metas de retenção, receita e volume devem ser recalculadas a partir dos dados
reais da Fase 1, evitando projeções sem base observada.

## Fase 3: Liderança e expansão — meses 37 em diante

Esta fase busca consolidar a plataforma como infraestrutura de capacitação,
trabalho e autonomia financeira para mulheres, começando pelo Brasil e
expandindo apenas quando houver capacidade operacional, segurança e adequação
regulatória.

| Foco estratégico | Implementação técnica — inovação e expansão | Marcos de negócio e financeiros |
|---|---|---|
| **Diversificação de oportunidades** | Marketplace para diferentes formatos de trabalho, projetos coletivos, mentorias e contratação recorrente. | **Expansão de renda:** receitas B2B e taxas de serviço tornam-se a principal fonte de sustentabilidade. |
| **Infraestrutura aberta** | APIs e integrações para ONGs, plataformas de educação, empresas, carteiras e sistemas de impacto. | **Efeito de rede:** parceiros passam a originar capacitações, tarefas e pagamentos por integração. |
| **Reputação interoperável** | Credenciais Nostr portáveis, consentidas e verificáveis entre organizações, sem centralizar dados sensíveis. | **Mobilidade profissional:** participantes utilizam sua reputação fora da plataforma para acessar novas oportunidades. |
| **Liquidez Lightning sustentável** | Automação de liquidez, políticas de risco, múltiplos provedores e contingência de tesouraria. | **Eficiência financeira:** custos de pagamento e liquidez permanecem previsíveis e cobertos pelo modelo de receita. |
| **Governança do ecossistema** | Painéis de auditoria, regras transparentes de funding e participação progressiva de organizações e participantes nas decisões. | **Maturidade institucional:** decisões de alocação e impacto possuem prestação de contas e representação das pessoas atendidas. |
| **Expansão regional** | Infraestrutura multi-região, localização, moedas, requisitos regulatórios e relays adequados a cada país. | **Expansão responsável:** entrada em novos países somente após consolidar operação e sustentabilidade no Brasil. |
| **Resiliência em ambientes restritivos** | Arquitetura com minimização de dados, comunicação descentralizada e opções seguras de identidade e pagamento. | **Alcance internacional:** apoiar organizações que atendem mulheres sob censura sem aumentar sua exposição ou risco. |

### Critério de evolução da Fase 3

Novos países, produtos financeiros ou modelos de governança só devem ser
adotados quando:

- o núcleo brasileiro estiver sustentável;
- não houver achados críticos de segurança;
- riscos jurídicos e operacionais estiverem mapeados;
- participantes e organizações tiverem representação nas decisões;
- receitas, custos, reservas e impacto puderem ser auditados separadamente.

## Indicadores permanentes

Todas as fases devem acompanhar um conjunto mínimo de indicadores:

| Dimensão | Indicadores |
|---|---|
| **Impacto** | participantes capacitadas, tarefas concluídas, renda liquidada e recorrência |
| **Produto** | ativação, conclusão, abandono, tempo de jornada e pedidos de suporte |
| **Qualidade** | aprovação, correção, disputa e satisfação de participantes e empresas |
| **Financeiro** | funding reservado, pagamentos conciliados, custos e saldo por finalidade |
| **Lightning** | sucesso, tempo de liquidação, taxas, estados ambíguos e disponibilidade |
| **Segurança** | incidentes, acessos indevidos, vulnerabilidades e tempo de correção |
| **Sustentabilidade** | receita recorrente, dependência de doações, custo por tarefa e runway |

O roadmap deve ser revisado trimestralmente. Nenhum item é considerado concluído
sem responsável, critério de aceite e evidência verificável.
