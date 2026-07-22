# Fluxos Fechados do MVP

Este documento congela os fluxos do MVP para o Demo Day de 25 de julho de 2026. O objetivo é provar que uma participante consegue aprender uma competência, executar uma tarefa real, receber em Lightning e carregar uma conquista verificável no Nostr.

## 1. Decisões de escopo

1. Haverá trilhas curtas e tarefas de demonstração - comprovar conhecimento ao longo da trilha
2. A equipe cadastrará a tarefa em nome de uma empresa parceira; não haverá portal empresarial completo.
3. A tarefa estará financiada antes de aparecer para a participante.
4. A aprovação será humana em uma tela administrativa.
5. Pagamento Lightning e badge NIP-58 serão reais.
6. Pix será opcional e só será real se a integração Hodle estiver testada.
7. O histórico econômico do nó será simulado e identificado como tal.
8. Pagamento de trabalho e receita de roteamento continuarão separados.

## 2. Atores

| Ator | Responsabilidade |
|---|---|
| Participante | Entrar, aprender, executar a tarefa e receber |
| Revisor | Avaliar, aprovar ou solicitar correção |
| Administrador | Preparar conteúdo, financiamento e demonstração |
| Empresa parceira | Origem econômica da tarefa |
| Patrocinador | Origem do matching e acompanhamento de impacto |
| Plataforma | Controlar estados, ledger, badges e pagamentos |
| Signer Nostr | Assinar login sem expor a chave privada |
| Carteira Breez | Gerar invoice e receber Lightning |
| Tesouraria | Pagar a invoice e retornar confirmação |
| Relays Nostr | Receber e disponibilizar o badge |

## 3. Fluxo ponta a ponta

```text
Administrador prepara tarefa financiada
                    |
Participante entra com Nostr
                    |
Conclui módulo e avaliação
                    +------> recebe badge NIP-58
                    |
Reserva e executa microtarefa
                    |
Revisor aprova a entrega
                    |
Carteira gera invoice Lightning
                    |
Tesouraria paga a invoice
                    |
Participante recebe sats e recibo
                    |
Painel registra o impacto realizado
```

## 4. Preparação administrativa

Antes da apresentação, o administrador:

1. cadastra empresa parceira e trilha de cinco minutos;
2. define uma avaliação com nota mínima de 80%;
3. cadastra a tarefa, evidência, prazo e critérios de aprovação;
4. define remuneração total em sats e composição financeira;
5. reserva os recursos no ledger;
6. publica a tarefa somente após a validação financeira.

```text
DRAFT -> FUNDED -> PUBLISHED
```

Uma tarefa sem reserva suficiente não pode ser publicada.

## 5. Entrada com Nostr

1. A participante seleciona “Entrar com Nostr”.
2. O backend gera um desafio de uso único.
3. O signer apresenta e assina o desafio.
4. O backend verifica assinatura, validade e uso único.
5. A plataforma cria uma sessão ligada à chave pública.
6. A participante é direcionada à trilha.

```text
Frontend       Backend       Signer
   |--desafio---->|             |
   |<-------------|             |
   |------- solicitar assinatura>
   |<---------- evento assinado-|
   |--verificar-->|             |
   |<--sessão-----|             |
```

Assinatura inválida ou desafio expirado exigem um novo desafio. Se o signer falhar no Demo Day, uma conta pré-autenticada pode ser usada com o rótulo “Modo demonstração”, sem ser apresentada como login ao vivo.

## 6. Capacitação e badge

1. A participante inicia e consome o módulo.
2. Responde à avaliação curta.
3. Com pelo menos 80%, conclui a trilha e desbloqueia a tarefa.
4. O emissor publica um badge NIP-58 para sua chave pública.
5. O backend registra ID do evento, relays e estado da publicação.

```text
NOT_STARTED -> IN_PROGRESS -> PASSED
                            -> FAILED -> IN_PROGRESS
```

O badge comprova a capacitação. A execução da tarefa é uma conquista separada. Se os relays falharem, o badge fica em `PUBLISH_PENDING` e tenta novamente; isso não bloqueia tarefa ou pagamento.

## 7. Reserva e execução da tarefa

1. A participante vê empresa, valor, prazo e critérios.
2. Ao iniciar, o backend verifica pré-requisito, vaga e financiamento.
3. Cria uma atribuição exclusiva por 60 minutos.
4. A participante registra três problemas de usabilidade e uma recomendação.
5. Ao enviar, o backend registra conteúdo, horário e hash da evidência.

```text
AVAILABLE -> RESERVED -> IN_PROGRESS -> SUBMITTED -> UNDER_REVIEW
                    |
                    +-> EXPIRED
```

Se a reserva expirar, vaga e recursos voltam a ficar disponíveis. O administrador terá um reset controlado para repetir o cenário.

## 8. Revisão

O revisor avalia a entrega sem visualizar dados pessoais desnecessários e registra ator, decisão e justificativa.

### Aprovação

```text
UNDER_REVIEW -> APPROVED -> PAYMENT_PENDING
```

A aprovação cria obrigação financeira e não pode ser revertida para evitar pagamento.

### Correção

```text
UNDER_REVIEW -> CHANGES_REQUESTED -> RESUBMITTED -> UNDER_REVIEW
```

O MVP permite uma correção. Rejeição final exige justificativa humana; IA não decide o pagamento.

## 9. Pagamento Lightning

O MVP usa invoice BOLT11 gerada pela carteira Breez depois da aprovação:

1. a participante recebe “Aprovada — gerar pagamento”;
2. a carteira cria uma invoice pelo valor exato em sats;
3. o backend valida rede, valor, expiração e obrigação aberta;
4. cria tentativa com chave de idempotência da atribuição;
5. a tesouraria paga a invoice;
6. o backend registra identificador e confirmação;
7. a carteira confirma o recebimento;
8. atribuição e ledger mudam para pagos.

```text
APPROVED
   |
PAYMENT_PENDING
   |-- invoice inválida/expirada --> solicitar nova invoice
   |
PAYMENT_PROCESSING
   |-- falha temporária --> PAYMENT_FAILED --> retry idempotente
   |
PAID
```

Garantias:

- a tarefa não pode ser paga duas vezes;
- repetir a requisição com a mesma chave retorna o pagamento original;
- invoice expirada é substituída sem perder a aprovação;
- falha do badge não bloqueia pagamento;
- falha do Pix não desfaz pagamento Lightning.

## 10. Recibo

```text
Tarefa: Teste de usabilidade

Empresa parceira                 8.000 sats
Matching do patrocinador         2.000 sats
Bônus Lightning realizado          500 sats
─────────────────────────────────────────
Total recebido                  10.500 sats

Status: pago
Data e hora: ...
Identificador: ...
```

O valor em BRL informa cotação e horário de referência, sem prometer o valor líquido de uma conversão futura.

## 11. Pix opcional

Esse fluxo não integra o critério de sucesso do MVP:

1. participante solicita conversão;
2. Hodle retorna cotação, taxa e validade;
3. o sistema mostra valor líquido;
4. a participante confirma explicitamente;
5. o provedor atualiza o status por webhook.

Sem integração disponível, a interface deve indicar simulação ou encaminhamento externo. Pix fictício não pode ser mostrado como concluído.

## 12. Painel do patrocinador

O painel separa dois blocos.

### Impacto realizado

- tarefas pagas;
- sats distribuídos;
- matching utilizado;
- participantes e badges;
- composição dos pagamentos.

### Cenário de infraestrutura — simulação

- capital hipotético de 0,05 BTC;
- canais e liquidez;
- volume roteado;
- taxas brutas, custos e receita líquida;
- bônus potencial.

O painel nunca soma capital, receita simulada e impacto real em uma única métrica.

## 13. Fluxo financeiro consolidado

```text
Empresa -------- valor-base --------+
                                      |
Patrocinador ---- matching -----------+--> reserva da tarefa
                                      |          |
Receita líquida -- bônus realizado ---+          v
                                            tarefa aprovada
                                                   |
                                         pagamento Lightning
                                                   |
                                            carteira Breez
```

Capital de liquidez não entra na reserva:

```text
Capital BTC -> canais -> taxas brutas -> custos -> receita líquida
                                                        |
                                                bônus futuro realizado
```

## 14. Roteiro de demonstração

O happy path deve durar de três a cinco minutos:

1. mostrar a tarefa financiada;
2. entrar com Nostr;
3. concluir o quiz e mostrar o badge;
4. executar e enviar a tarefa;
5. aprovar no painel do revisor;
6. gerar a invoice no celular;
7. mostrar o pagamento chegando na Breez;
8. abrir o recibo;
9. encerrar no painel do patrocinador, distinguindo real e simulado.

## 15. Critério de fluxo fechado

O fluxo está fechado quando:

- não existe tarefa publicada sem financiamento;
- toda aprovação possui caminho determinístico para pagamento;
- toda falha temporária possui estado e retry;
- nenhum retry duplica pagamento;
- badge e pagamento não bloqueiam um ao outro;
- dados reais e simulados estão separados;
- cada valor pode ser rastreado até sua origem no ledger.
