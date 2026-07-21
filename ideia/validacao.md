# Validação da Ideia — Crash Test da Banca

## Veredito

A proposta tem alto alinhamento com o Hack4Freedom: resolve uma dor social específica, utiliza Lightning e Nostr de forma funcional e pode produzir uma demonstração memorável. Seu principal risco era depender de taxas de roteamento como fonte garantida para pagar trabalho. A versão revisada transforma essa receita em bônus complementar e ancora o valor-base das tarefas em demanda econômica real.

## Pontos fortes

- Dor urgente e bem delimitada: mulheres que não podem esperar meses até a primeira renda.
- Bitcoin usado como infraestrutura de liquidação, não como ativo especulativo.
- Identidade e reputação portáteis com eventos assinados no Nostr.
- Pagamento Lightning real oferece um momento forte para o Demo Day.
- Integração com Nostr e Breez habilita os blocos adicionais de premiação.
- Modelo com potencial de crescer para compradores globais de microtarefas.

## Fragilidades que precisam ser controladas

### Receita de roteamento

Um nó recebe taxas somente quando encaminha pagamentos com sucesso. A receita depende de conectividade, liquidez nos dois sentidos, política de taxas, disponibilidade e demanda. Abertura de canais, fechamento, rebalanceamento e operação possuem custos. Por isso, a apresentação não deve usar as expressões “rendimento infinito”, “renda garantida” ou “principal nunca é gasto”.

### Preservação do aporte

Depois da conversão de BRL para BTC, o patrocinador assume volatilidade cambial e custos operacionais. O capital deve ser descrito como denominado em BTC e resgatável conforme regras previamente acordadas, não como um valor garantido em reais.

### Origem das tarefas

Uma plataforma de trabalho precisa provar os dois lados do mercado. Para o MVP, uma única empresa parceira e uma tarefa real valem mais que dezenas de tarefas fictícias.

### Privacidade e Nostr

Badges e identidade podem ser públicos, mas situação de vulnerabilidade, respostas, documentos, localização e dados antifraude não devem ser publicados em relays. A usuária deve controlar quais conquistas associa publicamente ao perfil.

### Experiência financeira

A usuária não deve precisar entender canais, invoices, seed phrases ou nós para completar o fluxo principal. O produto deve oferecer backup assistido, linguagem em reais e transparência sobre taxas antes do saque.

## Perguntas difíceis do Demo Day

### 1. Se o nó não rotear pagamentos por três meses, quem paga as mulheres?

O valor-base é pago pelo comprador da tarefa e pode receber matching do fundo de impacto. A receita líquida do nó financia somente bônus adicionais.

### 2. Como o principal é preservado se o Bitcoin cair ou houver custos de canais?

Não existe garantia nominal em reais. O capital de liquidez é denominado em BTC, sujeito a volatilidade, custos e regras transparentes de resgate.

### 3. Por que não pagar tudo por Pix?

Pix continua disponível como saída para reais. Lightning permite receber microtrabalho global, de forma programável e diretamente em uma carteira autocustodial; a proposta combina esse alcance com a conveniência local do Pix.

## Nota simulada — versão original

| Critério | Peso | Nota |
|---|---:|---:|
| Resolução do problema | 25 | 15 |
| Impacto social e relevância | 25 | 21 |
| Necessidade / problema | 20 | 17 |
| Viabilidade e escalabilidade | 10 | 4 |
| Capacidade de execução | 10 | 5 |
| Inovação e originalidade | 10 | 9 |
| **Total** | **100** | **71** |

A nota de execução é provisória porque ainda depende da composição da equipe e das integrações concluídas.

## Meta da versão revisada

Com uma tarefa real, emissão de badge, pagamento Lightning funcionando e comunicação econômica transparente, o projeto pode atingir a faixa de **84 a 88 pontos**.

Para chegar a essa faixa, as prioridades são:

1. Provar demanda com um parceiro e uma tarefa real.
2. Demonstrar o pagamento Lightning ponta a ponta.
3. Mostrar a composição e a origem de cada pagamento.
4. Não confundir receita bruta de roteamento com lucro líquido.
5. Demonstrar cuidado real com privacidade, recuperação de chave e conversão para Pix.

## Referências técnicas

- [Lightning Labs — Channel Fees](https://docs.lightning.engineering/the-lightning-network/pathfinding/channel-fees)
- [Lightning Labs — Managing Liquidity](https://docs.lightning.engineering/the-lightning-network/liquidity/manage-liquidity)
- [Breez SDK — Payment Fundamentals](https://sdk-doc-spark.breez.technology/guide/payments.html)
- [Nostr Protocol — NIPs, incluindo NIP-58](https://github.com/nostr-protocol/nips)
- [Hodle — infraestrutura Pix e Bitcoin](https://hodle.com.br/)
