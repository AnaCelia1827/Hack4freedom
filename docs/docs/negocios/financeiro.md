---
sidebar_position: 2
sidebar_label: Modelo Financeiro
---

# Modelo financeiro

## Visão geral

O modelo separa o valor econômico do trabalho, o recurso filantrópico e o capital usado na infraestrutura Lightning. Essa separação evita que uma tarefa aprovada dependa de uma doação futura, do preço do Bitcoin ou de uma receita de roteamento ainda não realizada.

```text
Empresa ───────── valor-base + taxa de serviço ───────┐
Doador de impacto ───────── matching ─────────────────┼─> pagamento
Receita líquida realizada do nó ─ bônus opcional ─────┘

Doador de liquidez ─> capital em BTC ─> canais Lightning
                                      └─> taxas - custos = resultado líquido
```

O trabalho deve ser pago principalmente por quem utiliza a entrega. Doações ampliam o impacto; não substituem indefinidamente a demanda comercial.

## Caixas e ledger

### Separação dos recursos

| Caixa ou conta de controle | Origem | Uso permitido | Pode pagar tarefas? |
|---|---|---|---|
| **Tarefas** | Empresas e organizações contratantes | Valor-base previamente contratado | Sim |
| **Impacto** | Doações e patrocínios | Matching, primeira tarefa, formação e campanhas definidas | Sim, conforme a campanha |
| **Obrigações a pagar** | Transferência dos caixas de tarefas, impacto e bônus | Valores já devidos após a aprovação | Sim, exclusivamente à participante |
| **Capital de liquidez** | Aporte denominado em BTC | Abertura e operação de canais Lightning | Não |
| **Resultado Lightning** | Taxas de roteamento efetivamente recebidas | Custos do nó e, depois da apuração, bônus de impacto | Somente o resultado líquido realizado |
| **Operacional** | Taxas comerciais e receitas de serviço | Equipe, tecnologia, suporte, vendas, contabilidade e conformidade | Não |

O **ledger operacional** registra cada movimentação como lançamentos vinculados entre origem e destino. O saldo apresentado no painel deve ser reconstruível pelos eventos, não mantido apenas como um número editável.

Cada lançamento precisa conter:

- identificador único da transação e do lançamento;
- contas de origem e destino;
- valor, ativo (`BRL` ou `BTC/sats`) e cotação de referência, quando houver;
- tarefa, campanha, doador ou canal relacionado;
- estado, data, responsável e evidência externa;
- ambiente `REAL`, `SANDBOX` ou `MOCK`.

Lançamentos confirmados não são apagados nem alterados. Erros são corrigidos por **lançamentos compensatórios**, preservando a trilha de auditoria. O ledger deve ser conciliado com contas bancárias, carteiras, canais e provedores de pagamento. Ele apoia a gestão, mas não substitui escrituração contábil, fiscal ou trabalhista.

## Política de reservas

O saldo disponível de cada caixa deve obedecer à seguinte relação:

```text
saldo disponível = saldo conciliado
                  - valores reservados
                  - obrigações a pagar
                  - retiradas pendentes
                  - custos de liquidação estimados
```

As reservas mínimas são:

1. **Cobertura de tarefas:** 100% do valor-base e do matching anunciado antes da publicação.
2. **Obrigações aprovadas:** segregação imediata do valor devido, mesmo que carteira, badge ou integração estejam temporariamente indisponíveis.
3. **Liquidação:** margem para taxas de rede, conversão e falhas de pagamento, revisada com dados reais.
4. **Operação Lightning:** saldo on-chain para abertura, fechamento e rebalanceamento, sem consumir o principal reservado a resgates.
5. **Operação da plataforma:** meta interna inicial de três meses de custos fixos e evolução para seis meses. Essa é uma política de prudência, não um requisito legal universal.

O capital de liquidez e o fundo de impacto não podem cobrir déficit operacional. A cobertura de tarefas deve permanecer igual ou superior a `1,00`.

## Composição dos pagamentos

| Parcela | Financiador | Quando pode ser prometida | Natureza |
|---|---|---|---|
| **Valor-base** | Empresa ou organização que utiliza a entrega | Após contratação e reserva | Remuneração pelo trabalho |
| **Matching** | Fundo de impacto | Após reserva da campanha | Complemento filantrópico |
| **Bônus** | Resultado líquido já realizado da infraestrutura | Somente após a apuração | Incentivo variável e não garantido |

Exemplo ilustrativo:

```text
Valor-base da empresa            8.000 sats
Matching do fundo de impacto     2.000 sats
Bônus já realizado                 500 sats
──────────────────────────────────────────
Total bruto                     10.500 sats
Taxas informadas antes do saque       X sats
Total líquido                   10.500 - X sats
```

O recibo informa cada origem, o total em sats, a referência em reais com horário da cotação e todas as taxas. O pagamento é concluído quando chega à carteira Lightning da participante. A conversão para Pix é posterior e opcional; sua cotação, tarifa e valor líquido devem ser aceitos previamente.

## Papel do doador

Existe um único perfil de **Doador**, com duas modalidades que não compartilham saldo:

### Fundo de impacto

É consumível e, por padrão, não resgatável. O doador escolhe finalidade, público, limite por participante, prazo e regra de matching. O painel apresenta somente impacto verificável: valores reservados e pagos, participantes remuneradas, tarefas concluídas e saldo remanescente.

### Capital de liquidez de impacto

É um aporte em BTC destinado à infraestrutura Lightning. O contrato precisa estabelecer titularidade, controle das chaves, prazo, custos, política de canais, resgate, tratamento do resultado e riscos. O painel separa:

- principal aportado e alocado;
- liquidez local e remota;
- volume roteado;
- taxas brutas;
- custos on-chain, de rebalanceamento e operação;
- resultado líquido;
- bônus efetivamente distribuídos.

O capital fica sujeito à volatilidade do BTC e a perdas e custos técnicos. Não há preservação nominal nem retorno garantido em reais. Se houver remuneração financeira ao provedor de capital, o arranjo exigirá avaliação jurídica e regulatória própria e permanece fora do modelo básico do MVP.

## Capital de liquidez e resultado do nó

O principal de liquidez não é receita e não entra na reserva das tarefas.

Na Lightning, a receita depende das taxas configuradas, das rotas efetivamente escolhidas e da liquidez disponível em cada direção; a própria documentação da Lightning Labs trata [taxas de canais](https://docs.lightning.engineering/the-lightning-network/pathfinding/channel-fees) e [gestão de liquidez](https://docs.lightning.engineering/the-lightning-network/liquidity/manage-liquidity) como variáveis operacionais, não como rendimento assegurado.

```text
resultado líquido do nó = taxas de roteamento recebidas
                         - taxas on-chain
                         - rebalanceamento e swaps
                         - compra de liquidez
                         - infraestrutura e operação atribuíveis
```

Somente um resultado líquido positivo, conciliado e já realizado pode ser transferido à pool de bônus. Receita futura, volume roteado e valorização do BTC não são lucro disponível.

## Custos

| Grupo | Principais itens | Direcionador |
|---|---|---|
| **Por tarefa** | revisão, controle de qualidade, pagamento, conversão e suporte | tarefas enviadas e aprovadas |
| **Tecnologia** | hospedagem, banco, observabilidade, backups, segurança e carteira | usuários ativos e transações |
| **Lightning** | abertura e fechamento de canais, rebalanceamento, liquidez e operação do nó | canais, volume e condições da rede |
| **Operação** | atendimento, organizações parceiras, prevenção a fraude e gestão de exceções | participantes e parceiros ativos |
| **Comercial** | prospecção, desenho de tarefas e gestão de contas B2B | clientes e pacotes contratados |
| **Governança** | contabilidade, jurídico, privacidade, segurança e auditoria | complexidade e exigências regulatórias |

O custo por tarefa aprovada deve incluir retrabalho e tarefas rejeitadas; caso contrário, a margem fica artificialmente elevada.

## Receita e sustentabilidade

A fonte principal de sustentabilidade é a **taxa B2B pelo serviço de intermediação, preparação da força de trabalho, controle de qualidade, pagamento e relatório**. Receitas complementares podem vir de operação de campanhas patrocinadas e relatórios institucionais, desde que não haja cobrança oculta sobre a remuneração ou a doação.

Exemplo inicial para teste de preço, não projeção:

| Destinação de um pacote B2B | Valor | Percentual |
|---|---:|---:|
| Remuneração das participantes | R$ 800 | 80% |
| Operação e controle de qualidade | R$ 150 | 15% |
| Contribuição para custos fixos e reserva | R$ 50 | 5% |
| **Preço do pacote** | **R$ 1.000** | **100%** |

Matching é adicional ao pacote e não compõe receita comercial. O ponto de equilíbrio deve ser calculado por:

```text
margem de contribuição por pacote = receita do pacote
                                   - remuneração
                                   - custos variáveis

pacotes para equilíbrio = custos fixos mensais
                        / margem de contribuição por pacote
```

O modelo só é sustentável quando a margem comercial cobre a operação sem depender de novos aportes de impacto. Doações podem financiar inclusão e expansão; receita líquida do nó pode gerar bônus; nenhuma das duas deve sustentar a promessa central de pagamento.

### Indicadores financeiros

- cobertura de tarefas e obrigações;
- margem de contribuição por tarefa e por cliente;
- custo por participante remunerada;
- receita recorrente e retenção de compradores;
- percentual da remuneração financiado por demanda comercial;
- meses de reserva operacional;
- prazo médio entre aprovação e pagamento;
- custo de conversão como percentual do valor recebido;
- resultado Lightning bruto, custos e líquido, sempre separados.

## Limite regulatório

Desde 2 de fevereiro de 2026, a [Resolução BCB nº 520](https://www.bcb.gov.br/estabilidadefinanceira/exibenormativo?numero=520&tipo=Resolu%C3%A7%C3%A3o+BCB) disciplina prestadores de serviços de ativos virtuais, incluindo autorização, segregação de ativos, prova de reservas e transparência de tarifas. O Banco Central também passou a exigir identificação e registros em determinadas transferências envolvendo carteiras autocustodiadas, conforme a [Resolução BCB nº 521](https://www.bcb.gov.br/estabilidadefinanceira/exibenormativo?numero=521&tipo=Resolu%C3%A7%C3%A3o+BCB).

A classificação concreta depende de quem custodia, converte, intermedeia e transmite os ativos. Antes de operar dinheiro real em escala, o projeto deve obter análise jurídica e contábil e priorizar provedores autorizados para custódia ou conversão quando a atividade entrar no perímetro regulado.

## Premissas que o piloto precisa validar

1. Empresas aceitam o preço e percebem valor nas entregas.
2. A margem cobre revisão, suporte, pagamento e retrabalho.
3. O ticket não torna as taxas de conversão desproporcionais.
4. Participantes entendem valor bruto, líquido e opção de Pix.
5. Doadores compreendem a diferença entre impacto e liquidez.
6. A conciliação consegue reconstruir integralmente cada saldo.
7. Existe demanda comercial suficiente para reduzir a dependência de matching.
