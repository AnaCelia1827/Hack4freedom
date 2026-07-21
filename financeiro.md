# Arquitetura Financeira e Fluxo de Pagamentos

Este documento explica como o dinheiro entra, é separado e chega à trabalhadora. A regra central é que **pagamento por trabalho, fundo de impacto e capital de liquidez são recursos diferentes e nunca devem ser contabilizados como se fossem o mesmo caixa**.

## 1. Visão geral

Existem três fontes principais de recursos:

```text
1. Pagamento da tarefa -> remunera o trabalho realizado
2. Fundo de impacto    -> complementa e incentiva a participação
3. Capital de liquidez -> opera na Lightning e pode gerar bônus
```

Além delas, a plataforma pode cobrar uma taxa de serviço para financiar sua própria operação.

## 2. Os quatro caixas

### 2.1 Caixa de tarefas

É financiado pelas empresas ou organizações que precisam de uma entrega. Esse dinheiro remunera trabalho real e verificável.

Exemplos de tarefas:

- teste de usabilidade;
- classificação de imagens;
- revisão ou transcrição de texto;
- validação de informações;
- pesquisa de preços;
- avaliação de respostas de IA;
- curadoria ou organização de dados.

Antes de a tarefa ser disponibilizada, seu valor-base precisa estar reservado. Assim, uma tarefa aprovada não depende de uma receita ou doação futura para ser paga.

### 2.2 Fundo de impacto

É um orçamento consumível aportado por patrocinadores, ONGs ou empresas ESG. Pode financiar:

- matching sobre o valor da tarefa;
- primeiros trabalhos de cada participante;
- bônus por conclusão de trilhas;
- capacitação e suporte;
- campanhas para públicos ou regiões específicas.

Esse fundo diminui à medida que os benefícios são distribuídos. O patrocinador recebe métricas de impacto, mas não possui direito automático de resgate desse recurso.

### 2.3 Capital de liquidez

É capital denominado em BTC e alocado na infraestrutura Lightning. Não é usado diretamente para pagar tarefas. Sua função é abrir canais, prover liquidez e permitir a operação de pagamentos.

O funcionamento técnico de canais, liquidez de entrada e saída, taxas e rebalanceamento está detalhado em [Canais Lightning, Roteamento e Receita do Nó](lightning.md).

Esse capital:

- está sujeito à volatilidade do Bitcoin;
- pode ter custos de abertura, fechamento e rebalanceamento;
- segue prazo e regras de resgate previamente acordados;
- não possui preservação nominal ou retorno garantido em reais;
- deve ser contabilizado separadamente do fundo de impacto.

O termo recomendado é **capital de liquidez de impacto**, e não “doação sem perda”.

### 2.4 Caixa operacional

Recebe a taxa de serviço cobrada pela plataforma e financia:

- controle de qualidade;
- atendimento e suporte;
- infraestrutura técnica;
- aquisição de compradores e participantes;
- custos administrativos e de compliance.

Esse caixa não deve ser confundido com o valor reservado para as trabalhadoras.

## 3. Exemplo de uma microtarefa

Considere uma tarefa que remunera o equivalente a R$ 10:

> Testar uma tela de aplicativo e registrar três problemas de usabilidade.

A composição pode ser:

```text
Empresa contratante                 R$ 8
Matching do fundo de impacto        R$ 2
────────────────────────────────────────
Remuneração total                  R$ 10
```

A empresa paga pelo valor econômico da entrega. O patrocinador complementa a remuneração para acelerar a entrada da participante no mercado.

No momento da liquidação, o valor é convertido ou referenciado em satoshis e enviado pela Lightning Network.

## 4. Fluxo completo da tarefa

```text
Empresa publica a tarefa
          |
          v
Valor-base é reservado
          |
          v
Matching do patrocinador é reservado
          |
          v
Usuária conclui a capacitação
          |
          v
Executa e envia a tarefa
          |
          v
Empresa ou revisor aprova
          |
          v
Plataforma paga em satoshis
na carteira Breez
          |
          +----> Usuária mantém em Bitcoin
          |
          +----> Usuária converte para Pix
```

O dinheiro deve ser reservado antes do início da tarefa. Após a aprovação, ele muda de “reservado” para “a pagar” e o pagamento Lightning é iniciado.

## 5. Estados financeiros de uma tarefa

Cada tarefa deve passar pelos seguintes estados:

| Estado | Significado |
|---|---|
| Criada | A tarefa existe, mas ainda não pode ser executada |
| Financiada | Valor-base e matching necessários estão disponíveis |
| Reservada | Os recursos foram separados para uma participante |
| Em análise | A entrega foi enviada e aguarda revisão |
| Aprovada | Existe obrigação de pagamento |
| Paga | O pagamento Lightning foi confirmado |
| Rejeitada | A entrega não cumpriu os critérios documentados |
| Estornada | A reserva foi devolvida ao caixa de origem conforme as regras |

Uma tarefa só pode ser publicada como disponível depois de atingir o estado **Financiada**.

## 6. Modalidades de participação do patrocinador

O patrocinador pode escolher uma ou ambas as modalidades.

### 6.1 Aporte no fundo de impacto

Exemplo:

```text
Patrocinador aporta R$ 10.000
            |
            v
Fundo de matching
            |
            +---- R$ 2 para a tarefa de Ana
            +---- R$ 3 para a tarefa de Beatriz
            +---- R$ 2 para a tarefa de Carla
            +---- outros incentivos
```

Possíveis regras de campanha:

- complementar 20% de cada tarefa;
- financiar os três primeiros trabalhos de cada mulher;
- oferecer bônus por progressão;
- limitar a campanha a uma região ou trilha;
- estabelecer valor máximo por participante.

### 6.2 Aporte de capital de liquidez

Exemplo:

```text
Patrocinador aporta 0,05 BTC
            |
            v
Plataforma abre canais Lightning
            |
            v
O nó roteia pagamentos
            |
            v
Recebe taxas variáveis
            |
            v
Desconta custos operacionais
            |
            v
Receita líquida alimenta bônus
```

O principal não é distribuído às trabalhadoras. Ele permanece alocado na infraestrutura até o encerramento ou resgate, conforme as regras acordadas.

## 7. Receita da infraestrutura Lightning

O nó recebe taxas somente quando encaminha pagamentos com sucesso. A receita líquida deve ser calculada assim:

```text
Receita líquida = taxas de roteamento recebidas
                - custos on-chain
                - custos de rebalanceamento
                - infraestrutura e operação do nó
```

Exemplo:

```text
Taxas de roteamento recebidas       20.000 sats
Rebalanceamento                    - 7.000 sats
Custos operacionais                - 3.000 sats
────────────────────────────────────────────────
Receita líquida                     10.000 sats
```

Os 10.000 sats líquidos podem alimentar uma pool de bônus para:

- primeira tarefa aprovada;
- conclusão de uma trilha;
- campanhas especiais;
- matching adicional.

O bônus só pode ser prometido depois que a receita líquida existir. Se o nó não gerar lucro, o pagamento-base continua coberto pela empresa contratante e pelo fundo de impacto reservado.

## 8. Composição do pagamento recebido

O recibo deve mostrar a origem de cada parcela:

```text
Tarefa: teste de usabilidade

Empresa contratante             8.000 sats
Matching do patrocinador        2.000 sats
Bônus da infraestrutura           500 sats
─────────────────────────────────────────
Total recebido                 10.500 sats
```

Essa transparência permite que:

- a trabalhadora entenda pelo que recebeu;
- a empresa confirme quanto pagou pela entrega;
- o patrocinador acompanhe o impacto financiado;
- a plataforma não apresente bônus como se fossem receita comercial;
- a auditoria reconcilie cada pagamento com seus caixas de origem.

## 9. Modelo de receita da plataforma

A sustentabilidade da plataforma deve vir principalmente de uma taxa cobrada pela intermediação e pelo controle de qualidade.

Exemplo de pacote empresarial:

```text
Empresa paga pelo pacote          R$ 1.000
Pagamento das trabalhadoras       R$   800
Operação e controle de qualidade  R$   150
Receita líquida da plataforma     R$    50
```

A proporção é apenas ilustrativa. No MVP, a interface deve separar claramente:

- remuneração das trabalhadoras;
- matching do patrocinador;
- taxa operacional;
- custos de conversão e pagamento;
- receita ou bônus Lightning.

## 10. Conversão para Pix

O pagamento é concluído quando os satoshis chegam à carteira da usuária. A conversão para Pix é uma operação posterior e opcional.

Para evitar que taxas consumam micropagamentos, a plataforma pode oferecer:

- saldo acumulado;
- valor mínimo para conversão;
- saques agrupados;
- estimativa de taxa antes da confirmação;
- escolha entre manter os satoshis ou converter para reais.

A taxa de conversão nunca deve ser escondida nem descontada sem confirmação explícita.

## 11. Regras financeiras obrigatórias

1. Pagamento por trabalho, fundo de impacto, capital de liquidez e caixa operacional ficam separados.
2. Nenhuma tarefa é publicada sem recursos suficientes reservados.
3. Tarefa aprovada gera obrigação de pagamento, independentemente do desempenho do nó.
4. Receita de roteamento só é distribuída depois da dedução dos custos.
5. O capital de liquidez é denominado em BTC e não possui garantia em reais.
6. O valor e os critérios de aprovação são informados antes do início da tarefa.
7. Toda conversão ou saque exibe previamente suas taxas.
8. Cada pagamento mantém um registro de origem, aprovação e confirmação Lightning.
9. Simulações financeiras são identificadas como simulações.
10. A plataforma não utiliza as expressões “rendimento garantido”, “rendimento infinito” ou “principal sem risco”.

## 12. Resumo do modelo

| Fonte | Natureza | Pode ser consumida? | Utilização |
|---|---|---:|---|
| Empresa contratante | Pagamento comercial | Sim | Valor-base das tarefas |
| Fundo de impacto | Doação ou orçamento consumível | Sim | Matching, formação e incentivos |
| Capital de liquidez | Capital denominado em BTC | Não durante a alocação | Operação de canais Lightning |
| Receita líquida do nó | Receita variável e não garantida | Sim | Bônus adicionais |
| Taxa da plataforma | Receita comercial | Sim | Sustentação da operação |

## 13. Princípio central

> **O trabalho é pago por quem recebe seu valor; o fundo de impacto acelera a inclusão; e a infraestrutura Lightning amplia o impacto quando gera receita líquida.**
