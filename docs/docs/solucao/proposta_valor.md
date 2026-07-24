---
sidebar_position: 1
sidebar_label: Proposta de Valor
---

# Proposta de valor

## Entrega de valor

A proposta de valor da plataforma é entregue por meio de um conjunto integrado de produtos e serviços que conecta **microcapacitação, trabalho digital, reputação portátil e pagamento rápido**.

As funcionalidades abaixo formam o núcleo da solução e demonstram como a plataforma reduz a distância entre aprender uma competência, aplicá-la em uma tarefa real e receber pelo trabalho aprovado. A experiência foi concebida para funcionar pelo celular e ocultar a complexidade de Nostr, Bitcoin e Lightning.

> **A participante aprende o necessário, demonstra sua competência em uma entrega real e recebe no mesmo fluxo, com critérios, valores e origem dos recursos apresentados de forma transparente.**

## Produtos e serviços

| Produto/serviço | Detalhe/função | Benefício |
|---|---|---|
| **Plataforma digital unificada** | Reúne participantes, organizações parceiras, revisores, empresas contratantes e patrocinadores em jornadas e áreas de acesso próprias. | Centraliza capacitação, trabalho, revisão, pagamento e acompanhamento de impacto sem misturar as responsabilidades dos diferentes atores. |
| **Identidade portátil com Nostr (RF-001 a RF-003)** | Permite autenticação por assinatura criptográfica e associa a sessão à chave pública da participante. A chave privada permanece no signer e nunca é enviada ao backend. | Reduz dependência de credenciais controladas exclusivamente pela plataforma e permite que a participante mantenha sua identidade digital. |
| **Microcapacitação vinculada à prática (RF-004 a RF-008)** | Oferece trilhas curtas, avaliações objetivas, registro de progresso e desbloqueio de tarefas após a nota mínima. | Reduz o tempo entre formação e oportunidade e permite que a participante aprenda em blocos compatíveis com sua rotina. |
| **Badge de competência verificável (RF-009 a RF-011)** | Define e concede badges assinados no Nostr por meio do NIP-58. A publicação individual ocorre somente após consentimento da participante. | Produz uma evidência portátil da competência sem publicar dados pessoais, entregas ou situação de vulnerabilidade. |
| **Mercado de microtarefas financiadas (RF-012 a RF-016)** | Lista tarefas elegíveis com empresa, instruções, prazo, vagas, remuneração e critérios de aprovação. A tarefa só é publicada quando possui recursos reservados. | Permite que a participante avalie se a oportunidade compensa seu tempo e impede a oferta de trabalho sem cobertura financeira. |
| **Entrega e revisão humana (RF-048 a RF-053)** | Registra a submissão, preserva a evidência e permite aprovação ou solicitação justificada de correção. | Reduz rejeições opacas e cria um processo auditável antes da geração da obrigação de pagamento. |
| **Pagamento Lightning (RF-054 a RF-061)** | Após a aprovação, valida uma cobrança pelo valor devido e realiza o pagamento com controle de idempotência, expiração e novas tentativas. | Encurta o tempo até o recebimento e evita que falhas técnicas ou uma invoice expirada façam a participante perder o valor aprovado. |
| **Recibo e ledger rastreável (RF-062 a RF-064)** | Registra a origem de cada parcela — empresa, matching e bônus — e apresenta total, status, horário, identificador e referência em reais. | Permite que participante, empresa e patrocinador compreendam a composição do pagamento e auditem a destinação dos recursos. |
| **Painel do patrocinador (RF-017 a RF-041 e RF-065)** | Reúne aportes e resultados, mantendo fundo de impacto e capital de liquidez separados no ledger. Dados simulados são identificados como `MOCK`. | Demonstra impacto realizado sem confundir doação consumível, capital em BTC, receita bruta, custos e resultado líquido. |
| **Conversão opcional para Pix** | Solicita cotação, apresenta taxa e valor líquido antes da confirmação e permite acumular saldo quando a conversão imediata não compensa. A operação real depende da integração habilitada. | Preserva a utilidade do recebimento para despesas em reais sem esconder custos nem obrigar a participante a vender seus satoshis. |

## Criadores de ganhos

| Criador de ganho | Descrição e vantagem competitiva |
|---|---|
| **Menor tempo até a primeira renda** | A capacitação está ligada a uma oportunidade concreta, reduzindo o intervalo entre aprender e receber pelo primeiro trabalho. |
| **Experiência profissional demonstrável** | A participante não recebe apenas um certificado: produz uma entrega real, passa por revisão e constrói histórico de trabalho aprovado. |
| **Reputação portátil e verificável** | Badges assinados permitem verificar a conquista e o emissor fora da plataforma, sem criar uma pontuação universal ou opaca. |
| **Pagamento rápido e de alcance global** | Lightning permite liquidar pequenos pagamentos e ampliar a origem potencial das oportunidades além do mercado brasileiro. |
| **Autonomia sobre o recebimento** | A participante pode manter o saldo em satoshis ou avaliar uma conversão para Pix conhecendo previamente as taxas e o valor líquido. |
| **Transparência financeira** | O recibo identifica quem financiou cada parcela e o ledger permite reconstruir a origem e o destino dos recursos. |
| **Impacto verificável** | Organizações e patrocinadores conseguem acompanhar capacitações concluídas, tarefas aprovadas e valores efetivamente pagos. |
| **Continuidade além da plataforma** | A identidade e as conquistas consentidas podem acompanhar a participante, reduzindo o aprisionamento de sua reputação em um único sistema. |

## Analgésicos

| Analgésico | Descrição da dor eliminada ou reduzida |
|---|---|
| **Capacitação conectada à renda** | Reduz a frustração de concluir cursos sem saber como acessar uma primeira oportunidade remunerada. |
| **Processo curto e mobile-first** | Diminui a barreira de formações longas ou dependentes de computador e permite interrupção e retomada da jornada. |
| **Tarefa com condições conhecidas** | Elimina parte da incerteza ao apresentar escopo, valor, prazo e critérios antes de a participante reservar a oportunidade. |
| **Correção antes da rejeição final** | Reduz decisões arbitrárias ao exigir justificativa humana e permitir uma nova submissão no MVP. |
| **Pagamento protegido contra falhas técnicas** | A aprovação cria uma obrigação financeira que permanece válida mesmo quando a cobrança expira ou uma tentativa de pagamento falha. |
| **Complexidade financeira abstraída** | A participante não precisa compreender canais, roteamento ou infraestrutura de nó para concluir a tarefa e receber. |
| **Privacidade por padrão** | Dados pessoais, situação de vulnerabilidade e conteúdo das entregas permanecem fora do Nostr; a concessão pública do badge depende de consentimento. |
| **Taxas e conversões visíveis** | Reduz a perda inesperada de valor ao mostrar cotação, taxa e resultado líquido antes de qualquer saída para Pix. |
| **Financiamento previamente reservado** | Evita que uma tarefa seja oferecida sem recursos suficientes para remunerar a entrega aprovada. |
| **Prestação de contas automatizável** | Reduz o esforço de organizações e patrocinadores para relacionar capacitação, trabalho, pagamento e origem do recurso. |

## Síntese da proposta

```text
Para a participante:
aprender → praticar → comprovar → trabalhar → receber → progredir

Para empresas e organizações:
financiar demanda real → revisar → pagar → acompanhar resultado

Para patrocinadores:
alocar recurso → rastrear uso → verificar impacto
```

A proposta não é prometer emprego, renda recorrente ou valorização de Bitcoin. O valor inicial está em comprovar que a plataforma consegue **encurtar, com segurança e transparência, o caminho entre capacitação e primeira renda por trabalho aprovado**.
