---
sidebar_position: 1
sidebar_label: Visão geral
---

# Visão geral do projeto — Stark

![Apresentação da Stark: capacitação, trabalho e pagamento com tecnologias abertas](/img/apresentação.gif)

*Apresentação visual da Stark. Fonte: produzido pelas autoras (2026).*

## Introdução

A **Stark** conecta **capacitação curta, trabalho digital, identidade portátil e
pagamento rápido**. A plataforma foi criada para mulheres em vulnerabilidade
econômica que precisam transformar aprendizado em uma oportunidade concreta de
renda.

Na mesma jornada, a participante aprende uma competência, aplica o conhecimento
em uma tarefa financiada, recebe avaliação humana e, após a aprovação, é paga
pela Lightning Network. Nostr permite autenticação segura e reputação
verificável, respeitando a escolha sobre o que permanece privado.

> **A Stark encurta o caminho entre aprender, demonstrar competência e receber
> por um trabalho aprovado.**

O nome homenageia **Elizabeth Stark**, cofundadora e CEO da
[Lightning Labs](https://lightning.engineering/team/). A Stark é um projeto
independente e não possui vínculo institucional ou comercial com ela ou com a
empresa.

## Problema

No Brasil, a vulnerabilidade econômica pode combinar baixa renda, informalidade,
dependência financeira, sobrecarga de cuidado, violência, dificuldade de
reinserção profissional e acesso digital limitado.

| Evidência | Impacto |
|---|---|
| Mulheres dedicavam 21,3 horas semanais a cuidados e afazeres; homens, 11,7 horas | Menos tempo contínuo para capacitação e trabalho |
| Mulheres ocupadas recebiam, em média, R$ 2.778 em 2024; homens, R$ 3.533 | Menor capacidade de formar reserva financeira |
| A informalidade atingiu 39,0% da população ocupada em 2024 | Renda instável e menor proteção social |
| 32% das mulheres usuárias de Internet acessavam somente pelo celular | Soluções dependentes de computador ampliam barreiras |
| Entre mulheres que relataram violência, 46% apontaram impacto no trabalho e 42% nos estudos | Violência também interrompe renda e aprendizagem |

Fontes: [IBGE](https://biblioteca.ibge.gov.br/visualizacao/livros/liv102066_informativo.pdf),
[Síntese de Indicadores Sociais 2025](https://agenciadenoticias.ibge.gov.br/media/com_mediaibge/arquivos/71016b2eb0a5feb8f7685271b1233db7.pdf),
[PNAD Contínua 2024](https://agenciadenoticias.ibge.gov.br/agencia-sala-de-imprensa/2013-agencia-de-noticias/releases/42530-pnad-continua-em-2024-taxa-anual-de-desocupacao-foi-de-6-6-enquanto-taxa-de-subutilizacao-foi-de-16-2),
[TIC Domicílios 2024](https://cetic.br/pt/tics/domicilios/2024/individuos/C16B/expandido/)
e [DataSenado 2025](https://www.senado.leg.br/institucional/datasenado/relatorio_online/pesquisa_violencia_domestica/2025/interativo.html).

A principal lacuna está entre **capacitar e gerar renda**. Um curso isolado não
garante oportunidade; uma tarefa sem recursos reservados não garante pagamento;
e possuir uma conta não garante controle ou privacidade financeira.

Empresas possuem demandas digitais verificáveis, enquanto ONGs e patrocinadores
precisam criar oportunidades e comprovar resultados sem tornar sua operação
financeiramente inviável.

Consulte [Mulheres em vulnerabilidade](problema/problema.md),
[Contexto brasileiro](problema/evidencias.md) e
[Sustentabilidade das ONGs](problema/negocio.md).

## Proposta de valor

| Público | Valor entregue |
|---|---|
| **Participantes** | capacitação ligada a tarefas reais, pagamento Lightning, identidade sob controle e reputação portátil |
| **Empresas** | entregas digitais com escopo, remuneração e critérios definidos |
| **Organizações** | acompanhamento da jornada e resultados sem acesso desnecessário a dados sensíveis |
| **Patrocinadores** | rastreabilidade do recurso e impacto baseado em trabalho e renda realizados |

Os principais benefícios são:

- menor tempo entre aprender e receber;
- tarefa integralmente financiada antes da publicação;
- correção justificada antes de uma rejeição final;
- pagamento rápido e auditável;
- experiência mobile-first;
- privacidade e consentimento por padrão.

Veja a [Proposta de valor](solucao/proposta_valor.md).

## Como funciona

```text
identidade Nostr
  → microcapacitação
  → tarefa financiada
  → entrega e revisão humana
  → pagamento Lightning
  → recibo e reputação verificável
```

A participante precisa compreender o valor, o trabalho e os critérios, mas não
operar canais, roteamento ou infraestrutura Bitcoin.

## Público-alvo

A usuária principal é a **mulher adulta em vulnerabilidade econômica**, com
acesso a celular, sem renda estável ou em reinserção profissional, que encontra
dificuldade para transformar capacitação em trabalho remunerado.

A participação não exige declaração ou comprovação de violência.

| Público complementar | Papel |
|---|---|
| Organização parceira | mobilizar, orientar e acompanhar participantes |
| Empresa contratante | financiar tarefas e utilizar as entregas |
| Revisor | avaliar segundo critérios previamente definidos |
| Patrocinador | financiar impacto ou infraestrutura |
| Administrador | configurar conteúdo, conciliação e suporte |

Veja [Público-alvo](usuario/publico_alvo.md) e
[Proto-personas](usuario/personas.md).

## Modelo financeiro

O pagamento pode combinar:

1. **valor-base**, financiado por quem utiliza a entrega;
2. **matching de impacto**, previamente reservado por patrocinadores;
3. **bônus opcional**, vindo apenas de resultado Lightning positivo, conciliado
   e já realizado.

Capital de liquidez, fundo de impacto, receita operacional e obrigações são
separados no ledger. O capital destinado a canais Lightning não é receita, não
paga tarefas diretamente e não possui retorno garantido.

A sustentabilidade deve vir principalmente de serviços B2B relacionados à
preparação das tarefas, capacitação, revisão, pagamento e relatórios. Doações
ampliam o impacto, mas não substituem indefinidamente a demanda comercial.

Consulte [Modelo financeiro](negocios/financeiro.md) e
[Análise de mercado](negocios/mercado.md).

## Tecnologias

| Tecnologia | Aplicação |
|---|---|
| React, TypeScript e Vite | interface web responsiva e mobile-first |
| Python e Flask | API e regras de negócio |
| PostgreSQL e SQLAlchemy | persistência, ledger e idempotência |
| Nostr | identidade, autenticação e reputação portátil |
| Bitcoin e Lightning | pagamentos em satoshis |
| NIP-58 | badges publicados mediante consentimento |
| Hodle/Pix | conversão opcional para reais, ainda planejada |

A autenticação Nostr segura e o pagamento Lightning real integram o fluxo atual.
Badges, comunidade, capital de liquidez e conversão Pix possuem maturidade
própria e não devem ser apresentados como concluídos sem validação.

Consulte [Arquitetura da solução](solucao/arquitetura.md) e
[Arquitetura técnica](implementação/arquitetura_tecnica.md).

## Diferenciais

- capacitação vinculada a uma oportunidade concreta;
- tarefas remuneradas e previamente financiadas;
- identidade e reputação portáteis;
- pagamento Lightning real;
- privacidade de dados sensíveis;
- transparência entre remuneração, doação, capital, custos e impacto;
- experiência pensada para celular e rotinas fragmentadas.

## Estado atual

A Stark está em estágio de **MVP integrado e preparação para piloto
controlado**. As prioridades são persistência durável, autorização completa,
armazenamento privado, limites de tesouraria, testes ponta a ponta, segurança e
validação com participantes, organizações e empresas.

Veja o [Status do projeto](status.md) e o [Roadmap](roteiro.md).

## Limites da solução

A Stark não substitui acolhimento psicossocial, jurídico, de saúde ou moradia;
não garante emprego ou renda recorrente; não exige relato de violência; não
apresenta Bitcoin como investimento; e não publica dados pessoais ou situação
de vulnerabilidade no Nostr.

## Conclusão

A Stark utiliza tecnologias abertas para criar uma ponte entre capacitação e
renda. Ao aproximar participantes, organizações, empresas e patrocinadores, a
plataforma transforma aprendizado em entrega verificável e trabalho aprovado em
pagamento rastreável, sem tratar tecnologia como solução isolada para a
vulnerabilidade.
