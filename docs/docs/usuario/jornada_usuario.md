---
sidebar_position: 3
sidebar_label: Jornada da Usuária
---

# Jornada da participante

## Objetivo da jornada

A jornada principal deve permitir que uma participante saia do primeiro contato até o recebimento por uma tarefa real sem precisar compreender a infraestrutura de Nostr, Lightning ou canais de pagamento.

```text
descobrir → confiar → entrar → aprender → escolher
          → executar → revisar → receber → progredir
```

O início e o fim não são apenas telas: confiança antecede o cadastro e utilidade posterior determina se o primeiro pagamento se transforma em nova oportunidade.

## Jornada ponta a ponta

| Etapa | Ação da participante | Pergunta principal | Fricção ou risco | Resposta esperada do produto | Indicador |
|---|---|---|---|---|---|
| 1. Descoberta | Recebe convite de uma organização ou parceira | “Isso é legítimo?” | Medo de golpe ou promessa falsa | Mostrar organização responsável, tarefa real e ausência de cobrança | Convites aceitos |
| 2. Avaliação | Consulta tempo, requisitos e forma de pagamento | “Serve para mim?” | Pouco tempo, celular limitado ou expectativa de emprego | Explicar duração, dispositivo, valor e limites da proposta | Início após visualizar condições |
| 3. Entrada | Cria ou conecta identidade | “Vou perder acesso ou expor meus dados?” | Termos técnicos, signer e chave | Fluxo assistido, linguagem simples e nenhuma chave privada enviada ao servidor | Entrada concluída e abandonos por etapa |
| 4. Capacitação | Faz módulo e avaliação curta | “Consigo terminar agora?” | Interrupção, dados móveis e dificuldade de leitura | Conteúdo leve, progresso automático, retomada e feedback | Conclusão e tentativas |
| 5. Oportunidade | Analisa e reserva uma tarefa | “O esforço compensa?” | Valor ou critérios ambíguos | Exibir empresa, escopo, prazo, valor, critérios e recursos já reservados | Tarefas visualizadas e reservadas |
| 6. Execução | Produz e envia a entrega | “Estou fazendo corretamente?” | Falta de exemplo, perda de conexão ou reserva expirada | Instruções, exemplo, salvamento e aviso de prazo | Envios e tempo de execução |
| 7. Revisão | Aguarda decisão ou realiza correção | “Serei paga?” | Ansiedade, rejeição opaca ou viés | Prazo de revisão, critérios, justificativa humana e uma correção | Aprovação, correção e tempo de revisão |
| 8. Pagamento | Gera cobrança e recebe satoshis | “Quanto recebi de verdade?” | Invoice expirada, falha técnica ou unidade desconhecida | Retry idempotente, confirmação e recibo em sats e referência em reais | Pagamentos concluídos e tempo de liquidação |
| 9. Uso da renda | Mantém saldo ou solicita Pix | “Quanto ficará disponível em reais?” | Taxas consumirem micropagamento | Mostrar cotação, taxa e valor líquido antes da confirmação; permitir acumular | Valor líquido e opção escolhida |
| 10. Progressão | Consulta badge e novas tarefas | “Isso abre outra oportunidade?” | Exposição pública ou credencial sem utilidade | Badge privado por padrão, publicação consentida e próximos passos | Retorno, novas tarefas e uso do badge |

## Momento decisivo

O momento de maior valor é:

```text
entrega aprovada → pagamento confirmado no celular
```

Para a participante, a confirmação precisa responder:

- qual tarefa foi paga;
- qual valor foi prometido;
- quanto foi efetivamente recebido;
- quem financiou o pagamento;
- quais taxas existem;
- o que pode ser feito a seguir.

O badge é complementar. Se sua emissão falhar, pagamento e recibo não podem ser bloqueados.

## Estados alternativos

### Interrupção

A participante pode ser interrompida por cuidado, trabalho, falta de conexão ou necessidade de sair rapidamente do aplicativo. O sistema deve salvar progresso, informar o prazo restante e permitir retomada sem repetir etapas desnecessárias.

### Correção da entrega

```text
EM_REVISÃO → CORREÇÃO_SOLICITADA → REENVIADA → EM_REVISÃO
```

A solicitação deve apontar o critério não atendido e oferecer uma tentativa de correção. Rejeição final exige justificativa humana e canal de contestação; uma decisão automática não pode cancelar pagamento.

### Falha de pagamento

```text
APROVADA → PAGAMENTO_PENDENTE → PROCESSANDO
                                  ├─→ PAGO
                                  └─→ FALHOU → NOVA_TENTATIVA
```

A aprovação cria obrigação de pagamento. Invoice expirada ou falha temporária não pode fazer a participante perder o valor, e novas tentativas não podem pagar duas vezes.

### Conversão para Pix

Pix é uma opção posterior ao recebimento. Antes da confirmação, devem aparecer cotação, validade, taxa e valor líquido. Se a integração estiver simulada, isso precisa estar visível; uma conversão fictícia nunca deve aparecer como concluída.

### Badge e privacidade

A conclusão pode gerar badge verificável, mas sua associação pública à identidade deve ser opcional. O produto não publica vulnerabilidade, valor recebido, documentos, localização nem conteúdo privado da entrega.

## Jornada de serviço

| Etapa visível | Participante | Organização/revisor | Plataforma |
|---|---|---|---|
| Convite | Decide participar | Apresenta a oportunidade e oferece apoio | Registra origem do convite |
| Capacitação | Aprende e responde | Apoia sem responder pela participante | Salva progresso e verifica conclusão |
| Tarefa | Reserva, executa e envia | Esclarece critérios quando necessário | Garante vaga e recursos reservados |
| Revisão | Recebe decisão | Avalia com justificativa | Registra ator, decisão e histórico |
| Pagamento | Confirma recebimento | Atua em exceções | Liquida, impede duplicidade e emite recibo |
| Continuidade | Escolhe badge e nova tarefa | Acompanha evolução consentida | Oferece histórico e próximos passos |

Esse desenho evita que a organização opere silenciosamente a conta ou a carteira da participante. Apoio não deve se transformar em controle sobre identidade ou renda.

## Requisitos de confiança

Em todos os pontos da jornada:

- nenhuma taxa pode aparecer somente depois do trabalho;
- tarefas devem estar financiadas antes de serem publicadas;
- a participante não paga para acessar uma oportunidade;
- situação de vulnerabilidade não aparece no perfil público;
- mensagens não devem revelar conteúdo sensível na tela bloqueada;
- decisões de revisão precisam de autoria e justificativa;
- a complexidade de Bitcoin deve ser traduzida, não transferida;
- ações irreversíveis exigem confirmação compreensível.

## Pontos de pesquisa

O teste da jornada deve observar, sem orientar excessivamente:

1. onde a participante hesita ou pede ajuda;
2. como interpreta “sats”, “carteira”, “badge” e “Pix”;
3. se encontra valor, prazo e critérios antes de reservar;
4. se entende que capacitação não garante renda recorrente;
5. se consegue retomar após uma interrupção;
6. se diferencia aprovação, pagamento e conversão;
7. se sabe localizar o recibo e o valor líquido;
8. se compreende a escolha de publicar ou não o badge.

## Critérios de sucesso do piloto

O fluxo será considerado compreensível quando:

- participantes concluírem as etapas essenciais pelo celular;
- nenhuma participante iniciar sem identificar valor e critério;
- o tempo entre aprovação e pagamento for mensurável e curto;
- falhas recuperáveis não exigirem recriar conta ou tarefa;
- participantes conseguirem explicar, com suas palavras, quanto receberam;
- a publicação do badge ocorrer somente por escolha informada;
- a organização parceira resolver exceções sem acessar chave privada ou controlar a carteira.

A jornada não termina na emissão de um certificado. Ela termina, para o MVP, quando a participante **recebe, compreende e controla o resultado econômico do trabalho realizado**.
