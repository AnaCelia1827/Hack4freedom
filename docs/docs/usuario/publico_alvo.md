---
sidebar_position: 1
sidebar_label: Público-alvo
---

# Público-alvo

## Definição

A usuária principal é a **mulher adulta em vulnerabilidade econômica que possui acesso a um celular, precisa gerar renda em curto prazo e encontra dificuldade para transformar capacitação em uma primeira oportunidade remunerada**.

O público não é homogêneo. A vulnerabilidade pode decorrer de desemprego, informalidade, retorno ao mercado após período de cuidado, baixa renda, violência patrimonial ou doméstica, migração, restrições territoriais e acesso digital limitado. Essas condições podem se sobrepor, mas nenhuma delas deve ser presumida durante o cadastro.

> O recorte do MVP não é “toda mulher vulnerável”, mas mulheres para quem uma trilha curta, uma tarefa digital real e um pagamento de pequeno valor podem representar um primeiro passo viável de geração de renda.

## Por que esse recorte

As evidências brasileiras indicam que:

- mulheres participam menos do mercado de trabalho e dedicam quase o dobro de horas ao cuidado não remunerado;
- 39,0% da população ocupada estava na informalidade em 2024;
- entre usuárias de Internet, 32% acessavam somente pelo celular em 2024;
- trabalho, gravidez e cuidado estão entre os principais motivos de interrupção escolar declarados por mulheres jovens;
- violência doméstica pode afetar rotina, trabalho remunerado e estudos;
- acesso a uma conta não significa, necessariamente, renda disponível, privacidade ou controle sobre os recursos.

Esses dados estão detalhados em [Contexto brasileiro](../problema/evidencias.md) e sustentam uma experiência curta, mobile-first, transparente e compatível com interrupções.

## Segmento prioritário do piloto

Para validar o fluxo com segurança, o piloto deve recrutar participantes que atendam aos seguintes critérios:

| Critério | Recorte inicial |
|---|---|
| Idade | 18 anos ou mais |
| Situação econômica | Sem renda estável, em ocupação informal ou buscando reinserção |
| Dispositivo | Acesso regular a smartphone próprio ou seguro |
| Conectividade | Internet móvel suficiente para uma jornada leve |
| Disponibilidade | Blocos curtos de aproximadamente 5 a 30 minutos |
| Competência inicial | Leitura funcional e uso básico de aplicativos |
| Interesse | Disposição para aprender e executar uma tarefa digital remunerada |
| Entrada | Preferencialmente indicada ou acompanhada por organização parceira |

Esses critérios são decisões operacionais do MVP, não uma definição universal de quem merece atendimento. Pessoas com menor alfabetização digital, deficiência, ausência de aparelho próprio ou idade inferior a 18 anos não são menos relevantes; exigem fluxos de acessibilidade, proteção e suporte que devem ser desenvolvidos depois de o caminho principal ser validado.

## Usuários e partes interessadas

| Grupo | Papel | Necessidade principal | Relação com o produto |
|---|---|---|---|
| Participante | Aprende, executa e recebe | Gerar renda com clareza, segurança e baixo custo de entrada | Usuária principal |
| Organização parceira | Recruta, orienta e acompanha | Ampliar oportunidades e observar resultados sem aumentar muito a carga operacional | Usuária operacional |
| Revisor | Avalia a entrega | Aplicar critérios objetivos e justificar decisões | Usuário operacional |
| Empresa contratante | Fornece e financia tarefas reais | Receber entregas úteis, verificáveis e com qualidade | Cliente |
| Patrocinador ou doador | Financia matching ou liquidez | Acompanhar a destinação dos recursos e o impacto realizado | Financiador |
| Administrador | Configura trilhas, tarefas e recursos | Manter estados, pagamentos e evidências consistentes | Operação interna |

No MVP, uma mesma pessoa pode exercer os papéis de organização parceira, revisor e administrador. As permissões e responsabilidades, porém, devem continuar separadas.

## Necessidades da participante

### Funcionais

- compreender o que fará, quanto poderá receber e como será avaliada;
- concluir a capacitação sem computador;
- interromper e retomar a jornada sem perder progresso;
- executar uma tarefa compatível com a competência praticada;
- receber explicação e oportunidade de correção;
- confirmar o pagamento e visualizar o valor líquido;
- manter satoshis ou solicitar saída para Pix;
- decidir se deseja publicar a conquista em seu perfil.

### Emocionais e de confiança

- perceber que a tarefa é real e está financiada;
- não ser tratada como beneficiária passiva;
- não precisar revelar uma situação de violência para participar;
- não ser exposta publicamente como “vulnerável”;
- entender termos financeiros sem conhecer Bitcoin;
- saber quem revisou sua entrega e como contestar uma decisão;
- sentir que erros de uso não provocarão perda definitiva do pagamento.

### Segurança e privacidade

A plataforma deve considerar aparelho compartilhado, vigilância digital, invasão de contas e controle de localização como riscos possíveis. A campanha [O Digital é Nosso Lugar](https://www.gov.br/mulheres/pt-br/central-de-conteudos/campanhas/2026/o-digital-e-nosso-lugar), do Ministério das Mulheres, inclui essas práticas entre as formas de violência digital.

Por isso, a experiência deve:

- coletar somente os dados necessários;
- evitar notificações com conteúdo sensível por padrão;
- permitir encerramento rápido da sessão;
- não publicar situação econômica, localização ou histórico de violência no Nostr;
- solicitar consentimento específico antes de tornar badges públicos;
- explicar backup e recuperação sem solicitar a chave privada;
- permitir que a participante procure apoio humano.

## Trabalhos que a usuária busca realizar

Sob a perspectiva de *jobs to be done*, a participante procura:

1. **Quando preciso gerar renda e não consigo assumir uma formação longa**, quero aprender apenas o necessário para realizar uma tarefa, para receber em menor tempo.
2. **Quando ainda não tenho experiência formal**, quero produzir uma evidência verificável de competência, para disputar novas oportunidades.
3. **Quando aceito uma tarefa**, quero conhecer previamente valor, prazo e critérios, para decidir se vale meu tempo.
4. **Quando meu trabalho é aprovado**, quero receber sem demora e entender taxas e opções, para usar o dinheiro com autonomia.
5. **Quando minha privacidade é importante**, quero controlar o que fica público, para não transformar uma oportunidade em risco.

## Quem a solução não substitui

A plataforma:

- não é canal de emergência ou denúncia;
- não substitui acolhimento psicossocial, jurídico, de saúde ou moradia;
- não garante emprego, renda recorrente ou rompimento de violência;
- não deve incentivar a participante a confrontar um agressor;
- não deve condicionar acesso a relato ou comprovação de violência;
- não deve apresentar Bitcoin como investimento ou promessa de valorização.

Quando organizações parceiras identificarem risco, o encaminhamento deve seguir seus protocolos próprios. A plataforma deve limitar-se à sua função: conectar aprendizagem, trabalho verificável e pagamento.

## Hipóteses a validar

1. O celular disponível é privado o suficiente para cadastro, tarefa e carteira.
2. Blocos de 5 a 30 minutos cabem na rotina das participantes.
3. A participante aceita receber inicialmente em satoshis quando existe saída clara para reais.
4. O login Nostr e o backup da carteira podem ser explicados sem aumentar abandono.
5. Uma tarefa de teste de usabilidade é compreensível e produz valor real.
6. A organização parceira consegue oferecer suporte sem operar toda a jornada pela participante.
7. O badge é percebido como útil e não como exposição indesejada.

Essas hipóteses devem ser verificadas com entrevistas, teste de usabilidade e observação do piloto, e não apenas por métricas de cadastro.
