---
sidebar_position: 2
sidebar_label: Personas
---

# Proto-personas

## Como interpretar

As personas abaixo são **proto-personas**: modelos provisórios construídos a partir das evidências disponíveis e do fluxo do MVP. Nomes e situações são ilustrativos; não representam entrevistas já realizadas.

Elas servem para explicitar necessidades diferentes e orientar testes. Devem ser revisadas depois das primeiras entrevistas com participantes, organizações e empresas.

## Base de evidências

As características escolhidas refletem:

- menor participação feminina no mercado e maior carga de cuidado, documentadas pelo [IBGE](https://biblioteca.ibge.gov.br/visualizacao/livros/liv102066_informativo.pdf);
- acesso exclusivamente móvel mais frequente entre mulheres, conforme a [TIC Domicílios 2024](https://cetic.br/pt/tics/domicilios/2024/individuos/C16B/expandido/);
- menor letramento financeiro entre mulheres e pessoas com renda familiar de até dois salários mínimos, identificado pelo [Banco Central](https://www.bcb.gov.br/cidadaniafinanceira/letramento_financeiro);
- impacto da violência sobre rotina, trabalho e estudos, registrado pelo [DataSenado 2025](https://www.senado.leg.br/institucional/datasenado/relatorio_online/pesquisa_violencia_domestica/2025/interativo.html);
- dificuldade operacional e financeira de organizações sociais, descrita em [Sustentabilidade das ONGs](../problema/negocio.md).

## Persona principal: Paula, renda informal e tempo fragmentado

![Persona Paula Santos, cuidadora e trabalhadora informal, com necessidades de tarefas rápidas, progresso salvo e recebimento confirmado](/img/persona1.png)

**Arquétipo:** mulher adulta, mãe ou cuidadora, com renda variável e acesso principal pelo celular.

| Aspecto | Hipótese |
|---|---|
| Contexto | Alterna trabalhos informais e cuidado de dependentes |
| Dispositivo | Android de entrada, pacote de dados limitado e pouco armazenamento |
| Objetivo | Conseguir uma renda complementar sem assumir uma formação longa |
| Motivação | Receber por algo concreto e construir experiência demonstrável |
| Barreiras | Interrupções, conexão instável, medo de fraude e pouca familiaridade com Bitcoin |
| Critério de confiança | Ver valor, prazo, empresa e regra de aprovação antes de começar |
| Sucesso | Concluir pelo celular e receber o valor líquido esperado |

### O que Paula precisa do produto

- linguagem simples e valores também apresentados em reais;
- progresso salvo automaticamente;
- tarefa curta, com exemplo de entrega aceita;
- consumo reduzido de dados;
- pagamento confirmado de forma inequívoca;
- opção de acumular saldo quando a conversão imediata não compensa.

### Hipóteses críticas

- blocos curtos realmente cabem em sua rotina;
- a tarefa pode ser executada integralmente pelo celular;
- a explicação de satoshis não reduz confiança;
- o valor da tarefa compensa tempo e conectividade.

## Persona de segurança: Aline, reinserção com necessidade de privacidade

![Persona Aline, em reinserção profissional, com necessidades de privacidade, notificações discretas e apoio humano](/img/persona2.png)

**Arquétipo:** mulher afastada do mercado que busca recuperar renda própria e pode conviver com controle financeiro ou digital.

| Aspecto | Hipótese |
|---|---|
| Contexto | Possui lacuna profissional e pouca experiência recente comprovável |
| Dispositivo | Pode usar aparelho compartilhado ou monitorado |
| Objetivo | Retomar atividade remunerada de forma gradual e segura |
| Motivação | Ampliar autonomia sem expor sua situação pessoal |
| Barreiras | Baixa confiança, receio de notificações, perda de credenciais e exposição pública |
| Critério de confiança | Controle sobre dados, sessão, carteira e publicação do badge |
| Sucesso | Receber e registrar competência sem criar novo risco |

### O que Aline precisa do produto

- participação sem necessidade de declarar violência;
- coleta mínima de dados e notificações discretas;
- saída rápida e encerramento de sessão;
- explicação clara sobre chave, carteira e recuperação;
- badge privado por padrão, com publicação opcional;
- apoio humano em decisões irreversíveis;
- critérios de revisão objetivos e possibilidade de correção.

### Hipóteses críticas

- uma carteira no mesmo aparelho é segura em seu contexto;
- o controle da chave é compreensível e praticável;
- o badge público é desejado;
- a organização parceira possui protocolo para situações de risco.

Essa persona não autoriza o produto a identificar, classificar ou diagnosticar vítimas. Ela existe para que segurança e privacidade façam parte do fluxo padrão.

## Persona operacional: Daniela, articuladora de organização social

![Persona Daniela Ribeiro, articuladora de organização social, com necessidades de acompanhamento, revisão e indicadores](/img/persona3.png)

**Arquétipo:** profissional de uma ONG ou coletivo que acompanha mulheres e acumula funções de mobilização, suporte e prestação de contas.

| Aspecto | Hipótese |
|---|---|
| Contexto | Equipe pequena, orçamento restrito e programas financiados por ciclos |
| Objetivo | Converter capacitação em oportunidades sem criar nova operação pesada |
| Motivação | Demonstrar resultados concretos às participantes e financiadores |
| Barreiras | Pouco tempo, múltiplas ferramentas, suporte individual e exigência de relatórios |
| Critério de confiança | Clareza sobre responsabilidades, dados coletados e origem dos pagamentos |
| Sucesso | Acompanhar evolução e resolver exceções sem acessar informações desnecessárias |

### O que Daniela precisa do produto

- convite e acompanhamento simples das participantes;
- visão de progresso por etapa, não de dados íntimos;
- protocolos claros para suporte e encaminhamento;
- fila de revisão com critérios previamente definidos;
- histórico de decisões e pagamentos;
- indicadores exportáveis e distinguíveis de métricas de vaidade.

### Hipóteses críticas

- a organização aceita atuar como canal de confiança;
- possui capacidade para suporte no piloto;
- consegue revisar ou indicar revisores;
- considera os indicadores úteis para prestação de contas.

## Perfis complementares

| Perfil | Decisão principal | Informação necessária |
|---|---|---|
| Gestora da empresa contratante | Vale financiar e repetir essas tarefas? | Qualidade, prazo, custo, taxa de correção e utilidade da entrega |
| Patrocinador de impacto | O recurso gerou resultado verificável? | Participantes pagas, valores, origem e destino do recurso |
| Provedor de liquidez | O risco e o desempenho foram apresentados corretamente? | Capital em BTC, canais, custos e receita líquida |
| Revisor | A entrega atende ao combinado? | Critérios, evidência, histórico e possibilidade de solicitar correção |

Esses perfis não devem alterar a prioridade de produto: o fluxo da participante precisa funcionar antes de painéis avançados.

## Anti-personas e limites

O MVP não foi desenhado para:

- pessoas buscando rendimento com Bitcoin;
- trabalhadores que precisam de salário estável garantido;
- tarefas que exigem computador, software especializado ou longas jornadas;
- empresas buscando mão de obra sem remuneração ou abaixo de um valor justo;
- organizações interessadas em expor histórias pessoais como prova de impacto;
- casos que dependem de resposta emergencial ou proteção especializada.

## Plano de validação

Cada proto-persona deve ser confrontada com evidência primária:

| Grupo | Método inicial | Quantidade indicativa | Decisão que informa |
|---|---|---:|---|
| Potenciais participantes | Entrevista semiestruturada | 5 a 8 | Rotina, confiança, privacidade e valor |
| Participantes do piloto | Teste moderado no celular | 5 | Compreensão e conclusão do fluxo |
| Organizações | Entrevista operacional | 3 a 5 | Recrutamento, suporte e indicadores |
| Empresas | Entrevista de demanda | 3 a 5 | Tipos, critérios e preço das tarefas |
| Revisores | Teste de avaliação | 2 a 3 | Clareza e consistência da aprovação |

As quantidades servem para descoberta qualitativa do MVP, não para inferência estatística. Padrões observados devem ser registrados junto com divergências; uma única história não deve ser generalizada para todo o público.
