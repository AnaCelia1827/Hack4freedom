# [Nome do Projeto]

> **Hack4Freedom Brasil 2026**
> Microcapacitação, trabalho digital e pagamentos instantâneos para mulheres brasileiras, com identidade portátil no Nostr e infraestrutura Lightning financiada por capital de impacto.

## 1. Resumo em uma frase

Uma plataforma que transforma trilhas curtas de aprendizagem em acesso a microtarefas digitais reais, paga cada trabalho aprovado em satoshis e registra as competências da usuária como badges assinados e portáteis no Nostr.

## 2. O problema

Mulheres em situação de vulnerabilidade econômica precisam gerar renda agora. Programas tradicionais de capacitação costumam exigir semanas ou meses antes de oferecer qualquer retorno financeiro, um intervalo incompatível com necessidades imediatas como alimentação, transporte e cuidados com os filhos.

Ao mesmo tempo, empresas precisam executar tarefas digitais pequenas e verificáveis, enquanto ONGs e fundos de impacto procuram modelos mensuráveis que não dependam exclusivamente de novas doações.

O problema não é apenas falta de capacitação. É a ausência de uma ponte curta e confiável entre **aprender, provar uma competência e receber pelo primeiro trabalho**.

## 3. A solução

A plataforma combina quatro elementos:

1. **Microcapacitação:** módulos curtos, práticos e ligados a uma tarefa concreta.
2. **Microtarefas reais:** atividades fornecidas por empresas e organizações, como testes de QA, curadoria, revisão e anotação de dados.
3. **Pagamento instantâneo:** após a aprovação, a trabalhadora recebe satoshis diretamente em uma carteira integrada com Breez, com possibilidade de conversão para Pix.
4. **Reputação portátil:** conclusões e competências geram badges assinados no Nostr, que podem ser verificados fora da plataforma.

O objetivo é reduzir o tempo entre o início do aprendizado e a primeira renda de meses para minutos ou horas.

## 4. Modelo econômico sustentável

O pagamento não depende exclusivamente de taxas de roteamento da Lightning. A operação possui três fontes complementares:

O fluxo detalhado, os estados de reserva e as regras de separação dos caixas estão documentados em [Arquitetura Financeira e Fluxo de Pagamentos](financeiro.md).

### 4.1 Empresas compradoras de tarefas

Empresas e organizações pagam pelo trabalho produzido. Essa receita financia o valor-base da microtarefa e cria demanda econômica real para a plataforma.

### 4.2 Fundo de matching e impacto

Patrocinadores podem aportar um orçamento consumível que complementa os primeiros pagamentos, subsidia capacitações e oferece bônus por progressão.

### 4.3 Capital de liquidez Lightning

Patrocinadores também podem fornecer capital denominado em BTC para canais Lightning. A infraestrutura pode gerar taxas quando roteia pagamentos com sucesso. Depois de descontados custos de abertura e fechamento de canais, rebalanceamento, disponibilidade e operação, a receita líquida pode financiar bônus adicionais.

Os detalhes de abertura de canais, liquidez direcional, roteamento, rebalanceamento e resgate estão em [Canais Lightning, Roteamento e Receita do Nó](lightning.md).

As taxas de roteamento são **variáveis e não garantidas**. O capital de liquidez permanece sujeito à volatilidade do Bitcoin, a custos operacionais e às regras de resgate acordadas. O projeto não promete preservação nominal do aporte em reais.

```text
Capital de liquidez
        |
        v
Canais Lightning -> receita bruta -> custos -> receita líquida
                                                |
                                                v
                                         bônus de impacto

Empresa contratante -> pagamento da tarefa -> trabalhadora
Patrocinador         -> fundo de matching   -> trabalhadora
```

## 5. Por que Bitcoin e não apenas Pix?

O projeto não pretende substituir o Pix. O Pix continua sendo uma saída importante para despesas em reais.

A Lightning Network permite pagamentos globais de baixo valor, programáveis e quase instantâneos, inclusive para uma carteira autocustodial. Isso possibilita que uma tarefa seja financiada por uma organização de qualquer lugar e liquidada diretamente para a trabalhadora, sem que a plataforma precise limitar sua demanda ao mercado brasileiro.

O diferencial está na combinação entre acesso a demanda global, liquidação Lightning, identidade portátil e saída opcional para Pix.

## 6. Arquitetura tecnológica

O mapeamento completo de features, componentes e prioridades está em [Arquitetura de Tecnologias por Feature](tecnologias.md).

### 6.1 Nostr: identidade, comunidade e badges

- A chave pública identifica a usuária de forma portátil.
- A comunidade e as interações públicas podem usar eventos Nostr.
- Conclusões de trilhas geram badges assinados com NIP-58.
- O badge funciona como evidência verificável de uma conquista, mas não é apresentado como uma credencial W3C completa.
- Dados pessoais, respostas privadas, informações de segurança e mecanismos antifraude permanecem no backend protegido.

Nostr não substitui todo o banco de dados. Ele oferece a camada de identidade e comprovação portátil. Também não se promete armazenamento eterno nos relays; o termo correto é **currículo portátil, assinado e verificável**.

### 6.2 Breez SDK: carteira da usuária

O Breez SDK fornece a experiência de carteira integrada e autocustodial para receber pagamentos. A plataforma mantém separada a tesouraria pagadora, que liquida uma invoice ou Lightning Address gerada para a usuária.

```text
Tesouraria da plataforma
        |
        v
Invoice / Lightning Address
        |
        v
Carteira Breez da usuária
```

### 6.3 Hodle: ponte entre Bitcoin e Pix

A integração com a Hodle pode atender depósitos e conversões entre BRL e Bitcoin. Como taxas de conversão podem consumir uma parcela relevante de pagamentos muito pequenos, o produto deve oferecer saldo acumulado, valor mínimo ou saques agrupados.

### 6.4 Backend

O backend em Python/Flask e SQLite gerencia:

- trilhas e tarefas;
- evidências e aprovação;
- separação contábil entre valor da tarefa, matching e bônus;
- antifraude e proteção de dados sensíveis;
- emissão do badge Nostr;
- acionamento e confirmação do pagamento Lightning;
- simulação transparente da economia de um nó de roteamento.

## 7. Jornada principal

1. A usuária entra com uma identidade Nostr.
2. Conclui um módulo prático de aproximadamente cinco minutos.
3. Recebe um badge NIP-58 relacionado à competência.
4. Destrava uma microtarefa fornecida por uma empresa parceira.
5. Envia a entrega e recebe aprovação.
6. A tesouraria paga uma invoice Lightning.
7. Os satoshis aparecem na carteira Breez da usuária.
8. O recibo identifica a composição do pagamento: comprador, matching e eventual bônus da infraestrutura.
9. A usuária mantém os satoshis ou solicita conversão para Pix.

## 8. Escopo do MVP para o Demo Day

O MVP deve provar um caminho completo e real:

- [ ] Login ou criação de identidade Nostr sem exposição da chave privada.
- [ ] Um módulo curto de capacitação.
- [ ] Emissão de um badge NIP-58.
- [ ] Uma microtarefa real, preferencialmente fornecida por um parceiro.
- [ ] Tela simples de revisão e aprovação.
- [ ] Pagamento Lightning real para uma carteira Breez.
- [ ] Comprovante com a origem dos recursos.
- [ ] Painel do patrocinador separando capital em BTC, receita bruta, custos e receita líquida.
- [ ] Simulação claramente identificada quando não houver nó de produção.

Uma boa tarefa para a demonstração é pedir à participante que teste uma tela do próprio produto e registre problemas de usabilidade. Dessa forma, a entrega possui valor real e pode ser validada diante da banca.

## 9. Métricas de sucesso

Para evitar métricas de vaidade, o projeto mede:

- tempo entre cadastro e primeira renda;
- percentual de mulheres que concluem uma trilha e executam uma tarefa;
- valor pago por trabalho real;
- recorrência de contratantes;
- custo operacional por pagamento;
- percentual da remuneração vindo de demanda real, matching e bônus;
- quantidade de badges emitidos e verificáveis.

## 10. Diferenciais competitivos

- **Renda próxima do aprendizado:** cada trilha está ligada a uma oportunidade concreta.
- **Trabalho, não recompensa artificial:** o valor-base vem de uma entrega econômica real.
- **Identidade portátil:** a reputação não fica presa ao banco de dados da plataforma.
- **Liquidação global:** Lightning amplia a origem possível das oportunidades.
- **Autocustódia com saída local:** a usuária controla o saldo e pode optar por Pix.
- **Infraestrutura como multiplicador:** a receita líquida do nó amplia o impacto, sem ser tratada como rendimento garantido.

## 11. Riscos e mitigação

| Risco | Mitigação |
|---|---|
| Receita de roteamento insuficiente | Não usá-la para garantir o valor-base das tarefas |
| Volatilidade do BTC | Denominar o capital de liquidez em BTC e comunicar o risco claramente |
| Custos de canais e rebalanceamento | Mostrar receita líquida, não apenas taxas brutas |
| Falta de compradores | Começar com uma tarefa real de um parceiro âncora |
| Taxa elevada no off-ramp | Permitir saldo acumulado e saques agrupados |
| Perda de chave | Fluxo assistido de backup e recuperação, sem custódia silenciosa |
| Exposição de dados pessoais | Manter dados sensíveis fora de eventos públicos do Nostr |
| Fraude em tarefas | Evidência verificável, revisão humana e limites no MVP |

## 12. Pitch de 45 segundos

Mulheres em vulnerabilidade frequentemente precisam escolher entre aprender e gerar renda imediata. Nossa plataforma transforma capacitações curtas em acesso a microtarefas digitais reais. Cada tarefa aprovada é paga instantaneamente em satoshis, diretamente em uma carteira autocustodial integrada com Breez. As competências conquistadas viram badges portáteis e verificáveis no Nostr. Empresas financiam o trabalho produzido, enquanto patrocinadores oferecem matching e capital para infraestrutura Lightning. A receita líquida dessa infraestrutura amplia os pagamentos, sem ser tratada como renda garantida. Assim, criamos uma ponte entre aprendizado, primeiro rendimento e reputação profissional portátil.

---

*Construído com propósito para o Hack4Freedom Brasil 2026.*
