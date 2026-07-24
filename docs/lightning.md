# Canais Lightning, Roteamento e Receita do Nó

Este documento explica como o capital de liquidez pode ser utilizado em canais Lightning, como o nó recebe taxas e por que essa receita é variável. Ele complementa a [Arquitetura Financeira e Fluxo de Pagamentos](financeiro.md).

## 1. Princípio fundamental

Abrir um canal Lightning não gera rendimento automaticamente. Um canal funciona como uma estrada com capacidade financeira disponível. A plataforma só recebe taxas quando pagamentos escolhem passar pelo seu nó e são roteados com sucesso.

```text
Capital em BTC
      +
Canais bem posicionados
      +
Liquidez na direção correta
      +
Taxas competitivas e disponibilidade
      =
Possibilidade de rotear pagamentos
```

Mesmo com todos esses elementos, não existe garantia de volume nem de lucro.

## 2. Aporte do patrocinador

Considere um aporte de 0,05 BTC destinado à infraestrutura:

```text
Aporte total                      0,050 BTC

Canal com o nó A                 0,020 BTC
Canal com o nó B                 0,020 BTC
Reserva para custos e ajustes    0,010 BTC
```

A divisão é ilustrativa. A estratégia real depende dos pares escolhidos, dos custos on-chain e da necessidade de liquidez de entrada e saída.

Esse recurso é **capital de liquidez de impacto**, não uma doação consumível. Ele não é utilizado diretamente para pagar microtarefas.

## 3. O que significa abrir um canal

Um canal é uma conexão financeira entre dois nós Lightning. Ao abrir um canal, o BTC é bloqueado em uma saída on-chain controlada pelas regras das duas partes.

O BTC não foi entregue ao nó parceiro, mas também não está imediatamente disponível na carteira on-chain da plataforma.

Exemplo de um canal recém-aberto:

```text
Plataforma                         Nó parceiro
2.000.000 sats                         0 sats
████████████████████|--------------------
```

A capacidade total é de 2.000.000 sats. Como o saldo começa do lado da plataforma, ela possui principalmente **liquidez de saída**.

Depois que pagamentos movimentam o canal:

```text
Plataforma                         Nó parceiro
1.200.000 sats                   800.000 sats
████████████|████████--------------------
```

A capacidade total continua igual. O que mudou foi a distribuição do saldo entre os dois lados.

## 4. Liquidez de entrada e saída

Para enviar por um canal, o nó precisa de saldo do seu próprio lado. Isso é liquidez de saída.

Para receber por um canal, o nó precisa que exista saldo do lado remoto. Isso é liquidez de entrada.

```text
Saldo local disponível  -> capacidade de enviar
Saldo remoto disponível -> capacidade de receber
```

Um canal aberto somente com o capital da plataforma normalmente começa com muita capacidade de saída e pouca capacidade de entrada. Portanto, abrir canais não é suficiente para começar a rotear de forma útil.

A plataforma pode obter liquidez de entrada por meio de:

- canais abertos por outros nós em sua direção;
- compra ou aluguel de liquidez;
- swaps;
- pagamentos que alterem a distribuição dos saldos;
- rebalanceamentos;
- parcerias com nós que possuem fluxo complementar.

## 5. Como um pagamento é roteado

Para rotear, o nó recebe o pagamento por um canal e o encaminha por outro:

```text
Pessoa pagadora
      |
      v
    Nó A
      |
      | canal de entrada
      v
Nosso nó
      |
      | canal de saída
      v
    Nó B
      |
      v
Pessoa recebedora
```

Nosso nó precisa ter, ao mesmo tempo:

- capacidade de receber pelo canal com o nó A;
- capacidade de enviar pelo canal com o nó B;
- políticas de taxa e disponibilidade que tornem a rota competitiva.

O pagamento é atômico: ou todo o percurso é concluído, ou os saldos não são alterados.

## 6. Como a taxa é calculada

Cada nó define sua política de taxas. Em termos simplificados:

```text
Taxa = taxa-base + valor do pagamento × taxa proporcional
```

Exemplo hipotético:

```text
Taxa-base:           1 sat
Taxa proporcional: 500 ppm
Pagamento:     100.000 sats
```

PPM significa partes por milhão:

```text
Taxa proporcional = 100.000 × 500 / 1.000.000
Taxa proporcional = 50 sats

Taxa total = 1 + 50
Taxa total = 51 sats
```

No roteamento, o nosso nó poderia receber 100.051 sats por um canal e encaminhar 100.000 sats pelo outro:

```text
Valor recebido pelo nó      100.051 sats
Valor encaminhado           100.000 sats
────────────────────────────────────────
Taxa bruta                       51 sats
```

Esses 51 sats são receita bruta, não lucro líquido.

## 7. Por que a rede escolheria o nosso nó

A carteira que inicia o pagamento procura uma rota adequada. Entre os fatores considerados estão:

- capacidade suficiente;
- liquidez na direção necessária;
- taxas competitivas;
- disponibilidade e confiabilidade;
- probabilidade de o pagamento ser concluído;
- posição útil entre origem e destino.

Canais abertos com pares aleatórios podem permanecer praticamente sem uso. A operação exige seleção de pares, observação de fluxos e ajustes de liquidez e taxas.

## 8. Rebalanceamento

Depois de muitos pagamentos na mesma direção, um canal pode ficar sem saldo local suficiente.

Antes:

```text
Nosso nó                           Parceiro
1.500.000 sats                   500.000 sats
███████████████|█████--------------------
```

Depois de muitos pagamentos:

```text
Nosso nó                           Parceiro
100.000 sats                   1.900.000 sats
█|███████████████████--------------------
```

O canal continua com a mesma capacidade total, mas quase não consegue enviar na direção desejada.

Rebalancear significa reorganizar os saldos entre canais. Isso pode ser feito por pagamento circular, swap ou outro mecanismo de gerenciamento de liquidez. Normalmente há custos.

Exemplo:

```text
Taxas de roteamento recebidas    500 sats
Custo de rebalanceamento        -700 sats
────────────────────────────────────────
Resultado                       -200 sats
```

Nesse caso houve receita, mas a operação não foi lucrativa.

## 9. Custos da operação

Além do rebalanceamento, o nó pode ter:

- taxas on-chain para abrir canais;
- taxas on-chain para fechar canais;
- compra ou aluguel de liquidez;
- servidor ou computador sempre disponível;
- armazenamento, backup e monitoramento;
- conexão estável;
- manutenção e segurança;
- canais pouco utilizados;
- custo de oportunidade do BTC alocado.

O resultado correto deve ser calculado assim:

```text
Receita líquida = taxas de roteamento
                - rebalanceamentos
                - custos on-chain
                - compra de liquidez
                - infraestrutura
                - operação
```

## 10. Da receita líquida aos bônus

Exemplo mensal hipotético:

```text
Taxas de roteamento recebidas       30.000 sats
Rebalanceamentos                   -12.000 sats
Custos on-chain provisionados       -5.000 sats
Infraestrutura e operação           -3.000 sats
────────────────────────────────────────────────
Receita líquida                     10.000 sats
```

Os 10.000 sats líquidos podem alimentar uma pool de bônus:

```text
Pool de bônus: 10.000 sats

10 bônus de primeira tarefa
10 × 500 sats                        5.000 sats

20 bônus por conclusão de trilha
20 × 250 sats                        5.000 sats
```

O bônus só pode ser anunciado depois que a receita líquida existir. Se o nó não gerar lucro, o valor-base das tarefas continua sendo pago pelas empresas e pelo fundo de impacto previamente reservado.

## 11. Pagamento da usuária versus roteamento

O pagamento de uma microtarefa e a receita de roteamento são fluxos diferentes.

Quando a plataforma paga uma usuária, há uma despesa:

```text
Tesouraria da plataforma --------> Carteira da usuária
                    pagamento de trabalho
```

Quando o nó encaminha um pagamento de terceiros, pode receber uma taxa:

```text
Pagador ----> Nosso nó ----> Recebedor
                  |
                  v
            taxa de roteamento
```

O pagamento enviado para uma carteira Breez pode passar ou não pelo nó patrocinado. A rede escolhe a rota. A plataforma não deve contabilizar seu próprio pagamento à trabalhadora como receita de roteamento.

## 12. Capacidade realista de um nó com 0,05 BTC

Um nó com 0,05 BTC pode ser útil para:

- provar tecnicamente o modelo;
- demonstrar abertura e gerenciamento de canais;
- executar pagamentos reais;
- coletar métricas de roteamento;
- gerar uma pequena quantidade de taxas;
- mostrar transparência financeira.

Não é prudente afirmar que esse capital, sozinho, pagará uma quantidade relevante de microtarefas. A receita depende de volume, posição na rede, custos e capacidade operacional.

O modelo recomendado permanece:

```text
Empresa paga a tarefa           8.000 sats
Fundo de impacto complementa    2.000 sats
Lucro do nó oferece bônus         500 sats
─────────────────────────────────────────
Total recebido                 10.500 sats
```

## 13. Resgate do capital

Para devolver o saldo, os canais precisam ser fechados ou reorganizados. O valor recuperado dependerá de:

- saldo pertencente à plataforma em cada canal;
- taxas on-chain de fechamento;
- custos acumulados;
- eventuais prazos de fechamento;
- variação do BTC em relação ao real.

O acordo com o patrocinador deve definir:

- quem controla as chaves;
- prazo mínimo de alocação;
- condições e prazo de resgate;
- responsabilidade pelos custos;
- tratamento das receitas e prejuízos;
- riscos técnicos e de mercado.

Se as chaves estiverem somente com a plataforma, o patrocinador confia nela para operar e devolver os recursos. Estruturas de múltiplas assinaturas e segregação patrimonial podem reduzir certos riscos, mas aumentam a complexidade e não são necessárias para o happy path do MVP.

## 14. Analogia operacional

O capital de liquidez pode ser comparado a caminhões disponibilizados para uma transportadora:

| Lightning | Analogia |
|---|---|
| BTC alocado | Capacidade dos caminhões |
| Canais | Estradas e rotas disponíveis |
| Pagamentos | Cargas transportadas |
| Routing fees | Valor dos fretes |
| Rebalanceamento | Reposicionamento de caminhões vazios |
| Custos on-chain e operacionais | Combustível, pedágio e manutenção |
| Receita líquida | Fretes menos todos os custos |

Ter capacidade não garante lucro. Ela precisa estar nas rotas certas, na direção correta e atender a uma demanda suficiente.

## 15. Como apresentar no hackathon

A formulação recomendada é:

> O capital patrocinado cria uma infraestrutura Lightning experimental. Quando essa infraestrutura gera receita líquida, o resultado financia bônus sociais. O pagamento-base do trabalho vem de compradores de tarefas e de recursos previamente reservados, portanto não depende de rendimento futuro ou garantido.

No MVP, o painel deve separar:

- capital total aportado em BTC;
- BTC alocado em cada canal;
- liquidez local e remota;
- volume efetivamente roteado;
- taxas brutas recebidas;
- custos de abertura e rebalanceamento;
- receita líquida;
- bônus efetivamente distribuídos.

Simulações devem ser identificadas claramente e não podem ser apresentadas como tráfego ou lucro real.

## 16. Referências técnicas

- [Lightning Labs — Channel Fees](https://docs.lightning.engineering/the-lightning-network/pathfinding/channel-fees)
- [Lightning Labs — Managing Liquidity](https://docs.lightning.engineering/the-lightning-network/liquidity/manage-liquidity)
- [Lightning Labs — Managing Channel Liquidity](https://docs.lightning.engineering/lightning-network-tools/lightning-terminal/channel-liquidity)
