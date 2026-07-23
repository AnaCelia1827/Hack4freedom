# Contexto do Projeto e Arquitetura de Negócios
teste com git
Este documento define a visão do produto, a arquitetura financeira e as regras de negócio do projeto para o **Hack4Freedom Brasil — julho de 2026, São Paulo**.

## 1. Cenário

O projeto está no cruzamento entre impacto social no Brasil e tecnologias de liberdade financeira. O foco é utilizar Bitcoin, Lightning Network e Nostr para criar uma ponte entre capacitação, trabalho digital e renda imediata, com privacidade, identidade portátil e menor dependência de intermediários.

## 2. Problema

### 2.1 Para a trabalhadora

Mulheres em situação de vulnerabilidade econômica não têm o luxo de passar meses estudando antes de receber. A necessidade diária de renda impede a participação ou conclusão de muitos programas tradicionais de capacitação.

### 2.2 Para empresas e organizações

Empresas possuem tarefas digitais pequenas e verificáveis, mas nem sempre contam com um processo acessível para capacitar, contratar e remunerar novos talentos. ONGs e fundos de impacto, por sua vez, precisam demonstrar resultados e reduzir sua dependência de ciclos contínuos de captação.

### 2.3 Hipótese central

Se uma trilha curta estiver diretamente vinculada a uma tarefa remunerada, a participante poderá aprender, demonstrar competência e receber sua primeira renda no mesmo fluxo.

## 3. Solução

A plataforma oferece:

- microcapacitações associadas a oportunidades concretas;
- microtarefas financiadas por empresas e organizações;
- pagamentos instantâneos em satoshis;
- carteira integrada com Breez;
- badges de competência assinados no Nostr;
- saída opcional para Pix;
- painel de transparência para patrocinadores.

O produto deve esconder a complexidade do Bitcoin. A usuária não precisa entender canais, roteamento ou invoices para concluir uma tarefa e receber.

## 4. Arquitetura financeira

O pagamento de cada tarefa pode ser composto por três fontes:

Para o fluxo completo de aportes, reservas, aprovação, pagamento Lightning e conversão para Pix, consulte [Arquitetura Financeira e Fluxo de Pagamentos](ideia/financeiro.md).

1. **Valor-base da tarefa:** pago pela empresa ou organização que recebe a entrega.
2. **Matching de impacto:** orçamento consumível aportado por patrocinadores para complementar renda, formação e primeiros trabalhos.
3. **Bônus de infraestrutura:** parcela da receita líquida obtida com a operação Lightning, quando existir.

Essa separação é uma regra de negócio. A plataforma nunca deve depender de taxas futuras de roteamento para garantir o valor-base já prometido à trabalhadora.

### 4.1 Capital de liquidez

Patrocinadores podem fornecer capital denominado em BTC para abrir canais e prover liquidez à Lightning Network. Esse capital:

- permanece sujeito à variação do preço do Bitcoin;
- pode sofrer custos de abertura e fechamento de canais;
- exige gerenciamento de liquidez e rebalanceamento;
- não possui retorno ou preservação nominal garantidos em reais;
- segue regras de resgate e risco explicitamente aceitas pelo patrocinador.

Para uma explicação operacional completa, consulte [Canais Lightning, Roteamento e Receita do Nó](ideia/lightning.md).

### 4.2 Receita da infraestrutura

O nó recebe taxas apenas ao rotear pagamentos com sucesso. A métrica relevante é a receita líquida:

```text
Receita líquida = taxas de roteamento
                - custos on-chain
                - custos de rebalanceamento
                - infraestrutura e operação
```

Expressões como “rendimento infinito”, “retorno garantido” e “principal nunca é gasto” não devem ser usadas na apresentação, no produto ou na documentação.

## 5. Arquitetura tecnológica do MVP

A seleção detalhada de bibliotecas, protocolos e prioridades está em [Arquitetura de Tecnologias por Feature](ideia/tecnologias.md). O escopo implementável está definido em [Requisitos do Produto](ideia/requisitos.md), com estados e exceções em [Fluxos Fechados do MVP](ideia/fluxos.md).

### 5.1 Nostr

Nostr é usado para identidade portátil, comunidade e emissão de badges de conclusão pelo NIP-58. O badge é uma evidência assinada e verificável, não uma credencial W3C completa nem uma promessa de armazenamento eterno.

Dados pessoais, entregas privadas, informações antifraude e dados relacionados à vulnerabilidade da usuária ficam no backend protegido. A publicação de uma conquista no perfil deve respeitar a escolha da usuária.

### 5.2 Breez SDK

O Breez SDK fornece a experiência de carteira integrada para a usuária receber e controlar seus satoshis. A carteira pagadora da plataforma é um componente separado e liquida uma invoice ou Lightning Address associada à trabalhadora.

### 5.3 Hodle

A Hodle funciona como ponte entre Pix e Bitcoin para os fluxos suportados. O produto deve exibir taxas de conversão antes da confirmação e permitir acúmulo de saldo ou saque agrupado, evitando que custos fixos ou percentuais consumam micropagamentos.

### 5.4 Backend

O backend em Python/Flask e SQLite gerencia:

- conteúdo, tarefas e desbloqueios;
- evidências, revisão e aprovação;
- origem e composição dos pagamentos;
- emissão de badges;
- disparo e confirmação Lightning;
- dados sensíveis e mecanismos antifraude;
- simulação financeira identificada como simulação.

## 6. Regras de negócio

1. Toda tarefa deve informar valor, critério de aprovação e origem dos recursos antes do início.
2. Uma tarefa aprovada gera obrigação de pagamento independentemente da receita do nó.
3. O bônus de infraestrutura só pode distribuir receita líquida já realizada.
4. Capital de liquidez, orçamento de matching e receita operacional são contabilizados separadamente.
5. Nenhum dado pessoal sensível é publicado no Nostr por padrão.
6. A usuária controla sua carteira ou recebe uma explicação explícita se algum fluxo experimental não for autocustodial.
7. Toda taxa de saque ou conversão é mostrada antes da confirmação.
8. Simulações devem ser visualmente identificadas e não podem parecer transações reais.

## 7. Objetivo para o Demo Day — 25 de julho de 2026

O MVP deve demonstrar o caminho completo:

1. Entrada com identidade Nostr.
2. Conclusão de uma trilha curta.
3. Emissão de um badge NIP-58.
4. Desbloqueio e execução de uma tarefa real.
5. Aprovação da entrega.
6. Pagamento Lightning real em uma carteira Breez.
7. Exibição da origem do pagamento.
8. Painel do patrocinador separando capital em BTC, receita bruta, custos e receita líquida.

O momento central da apresentação é a confirmação do pagamento no celular, apoiada por uma explicação econômica honesta e verificável.

## 8. Critério de sucesso do MVP

O MVP será considerado bem-sucedido se provar que uma participante consegue sair do cadastro ao primeiro pagamento sem precisar compreender a infraestrutura técnica subjacente e se a banca consegue verificar:

- que a tarefa produziu valor real;
- quem financiou o pagamento;
- que o pagamento Lightning aconteceu;
- que o badge pertence à identidade da participante;
- que capital, receita e impacto não foram contabilizados como se fossem a mesma coisa.
