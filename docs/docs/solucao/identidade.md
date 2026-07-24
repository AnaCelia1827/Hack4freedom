---
sidebar_position: 5
sidebar_label: Identidade e Reputação
---

# Identidade e reputação

## Objetivo

A solução usa Nostr para oferecer uma identidade portátil e permitir que competências sejam verificadas fora da plataforma. A participante deve controlar a chave e decidir quais conquistas associa publicamente ao perfil.

```text
identidade = chave pública controlada pela participante
autenticação = prova de controle dessa chave
reputação = evidências assinadas por emissores identificáveis
```

Identidade, perfil, autenticação e reputação são conceitos diferentes. Conhecer a chave pública de alguém não comprova competência; um badge só tem valor quando a conquista e o emissor são confiáveis.

## Princípios

- a chave privada nunca chega ao backend;
- a chave pública é um identificador, não um cadastro civil;
- a plataforma não exige relato de vulnerabilidade;
- reputação é composta por evidências, não por uma nota opaca;
- a participante escolhe se publica e exibe uma conquista;
- dados privados permanecem fora dos relays;
- perder acesso à chave é um risco explicado antes de ações importantes;
- portabilidade não significa permanência garantida em todos os relays.

## Identidade Nostr

Cada usuário é associado a uma chave pública Nostr.

| Elemento | Papel |
|---|---|
| Chave privada | Assinar eventos; permanece com a usuária |
| Chave pública | Identificar e verificar assinaturas |
| `npub` | Representação legível da chave pública |
| Signer | Aplicativo ou extensão que protege a chave e assina |
| Relay | Servidor que recebe e distribui eventos |
| Backend | Mantém sessão e dados privados da aplicação |

Nostr não substitui o banco operacional. Progresso, entregas, revisões, pagamentos e informações antifraude permanecem no backend.

## Autenticação

### MVP com NIP-07

O [NIP-07](https://github.com/nostr-protocol/nips/blob/master/07.md) define uma interface de navegador pela qual a aplicação solicita a chave pública e a assinatura de um evento.

```text
1. backend cria nonce aleatório e expiração curta
2. PWA monta evento de autenticação com nonce e audiência
3. signer mostra a solicitação e assina
4. backend verifica id, assinatura, pubkey, audiência e prazo
5. nonce é invalidado
6. sessão segura é criada
```

Controles:

- desafio de uso único;
- validade curta;
- vinculação ao domínio da aplicação;
- limite de tentativas;
- cookie seguro e `HttpOnly`, quando aplicável;
- logout e revogação da sessão;
- nenhuma assinatura silenciosa de evento desconhecido.

O evento de autenticação não precisa ser publicado em relay.

### Evolução com NIP-46

O [NIP-46](https://github.com/nostr-protocol/nips/blob/master/46.md) permite assinatura remota e pode reduzir a dependência de extensões. Sua adoção é posterior ao caminho principal e exige uma experiência clara de conexão, autorização e revogação.

No Android, signers compatíveis também podem ser avaliados. A escolha final deve priorizar recuperação, compreensão e segurança no dispositivo real das participantes.

### Modo demonstração

Uma conta pré-autenticada pode existir apenas como fallback do Demo Day. Ela deve:

- ser rotulada como `Modo demonstração`;
- usar dados fictícios;
- não aparentar uma assinatura ao vivo;
- não possuir acesso a segredos ou recursos de produção.

## Perfil

O perfil pode incluir nome de exibição, foto e descrição escolhidos pela usuária. O backend guarda preferências da aplicação e pode consultar metadados públicos quando necessário.

Não devem ser publicados:

- situação de vulnerabilidade;
- relato ou indicador de violência;
- localização precisa;
- documentos;
- conteúdo de tarefas;
- valores recebidos;
- histórico de correções;
- dados de ONG ou atendimento sem consentimento.

O nome público pode ser pseudônimo. A plataforma não deve equiparar `npub` a identidade civil verificada.

## Badge de competência

O [NIP-58](https://github.com/nostr-protocol/nips/blob/master/58.md) está marcado como opcional e em rascunho no repositório oficial. No protocolo:

| Evento | `kind` | Responsável | Função |
|---|---:|---|---|
| Badge Definition | `30009` | Emissor | Define nome, descrição e imagem |
| Badge Award | `8` | Emissor | Concede o badge a uma ou mais chaves |
| Profile Badges | `10008` | Participante | Escolhe badges exibidos e sua ordem |

O badge concedido é imutável e não transferível. A confiança depende da chave do emissor, da definição e do motivo da concessão.

## Fluxo de emissão

```text
conclusão registrada no backend
          ↓
regra de elegibilidade validada
          ↓
BadgeAward interno: PENDING_CONSENT
          ↓
participante escolhe publicar
          ↓
emissor assina evento kind 8
          ↓
publicação em relays configurados
          ↓
IDs e confirmações registrados
```

A definição do badge pode ser publicada antecipadamente. A concessão individual só é assinada e enviada após consentimento.

### Falha de publicação

```text
PUBLISH_PENDING → PUBLISHED
       └────────→ PUBLISH_FAILED → retry
```

Falha de relay:

- não remove a conclusão interna;
- não bloqueia tarefas;
- não bloqueia pagamentos;
- mantém o evento pronto para nova tentativa;
- informa claramente que a publicação ainda está pendente.

## Privacidade por padrão

Um evento Nostr enviado a relay deve ser tratado como público e potencialmente replicável. Portanto, “badge privado por padrão” significa:

> **a plataforma registra a conquista internamente, mas não cria nem publica a concessão NIP-58 até que a participante escolha torná-la pública.**

Depois da publicação, não é possível garantir remoção global. Solicitações de exclusão podem não eliminar cópias mantidas por terceiros. Esse efeito precisa ser explicado antes do consentimento.

## Reputação

A plataforma não utiliza uma pontuação universal. A reputação é formada por sinais verificáveis:

| Sinal | Evidência | Limite |
|---|---|---|
| Capacitação concluída | Badge assinado pelo projeto | Não prova desempenho contínuo |
| Tarefa aprovada | Registro interno de entrega e revisão | Conteúdo pode ser confidencial |
| Recorrência | Quantidade de tarefas aprovadas | Não deve incentivar volume sem qualidade |
| Qualidade | Critérios atendidos e correções | Depende da consistência dos revisores |
| Emissor | Chave pública conhecida | Chave conhecida não elimina fraude operacional |

Empresas podem verificar o badge e reconhecer o emissor, mas não recebem automaticamente dados pessoais ou entregas anteriores.

### Badge de curso e badge de trabalho

São conquistas distintas:

- **badge de capacitação:** comprova conclusão conforme regra do módulo;
- **badge de trabalho:** pode comprovar uma tarefa ou marco profissional, quando existir regra e consentimento próprios.

O MVP deve começar com o badge de capacitação. Adicionar badges para qualquer ação reduz seu significado.

## Confiança no emissor

A chave oficial que define e concede badges deve:

- ficar fora do frontend;
- ser protegida em secret manager ou signer dedicado;
- ter acesso limitado à assinatura de eventos permitidos;
- possuir backup e procedimento de recuperação;
- ser divulgada em canal oficial;
- ter rotação documentada.

Se a chave for comprometida, novas emissões devem ser suspensas. Como concessões são imutáveis, a plataforma precisa manter uma lista interna de incidentes e comunicar a migração para uma nova chave; não deve prometer revogação interoperável que o NIP-58 não define.

## Recuperação e perda de acesso

O produto deve explicar, em linguagem simples, que quem controla a chave controla a identidade.

### No MVP

- o signer é responsável por guardar a chave;
- a plataforma fornece instruções de backup compatíveis com o signer;
- a equipe nunca pede a chave privada ou frase de recuperação;
- suporte pode orientar, mas não recuperar secretamente a conta;
- troca de chave exige processo explícito e não transfere eventos antigos.

### Evolução

- signers remotos com NIP-46;
- recuperação social ou assistida oferecida pelo signer;
- múltiplos dispositivos;
- vínculo interno entre conta anterior e nova após verificação adequada.

Essas alternativas precisam ser testadas com participantes; facilidade de recuperação não pode introduzir custódia silenciosa.

## Autorização interna

Autenticar uma chave não concede acesso administrativo. Papéis internos são atribuídos no backend:

| Papel | Permissões principais |
|---|---|
| Participante | Curso, tarefa própria, pagamento e consentimento de badge |
| Revisor | Submissões atribuídas e decisão justificada |
| Organização | Acompanhamento consentido e indicadores agregados |
| Doador | Aportes e painel próprio |
| Administrador | Configuração, conciliação e suporte |

Toda ação privilegiada registra ator, horário, objeto e resultado. Revisores não acessam dados pessoais desnecessários, e organizações não controlam chaves ou carteiras das participantes.

## Ameaças e controles

| Ameaça | Controle |
|---|---|
| Site falso solicitando assinatura | Domínio visível e descrição clara no signer |
| Reutilização de evento | Nonce e expiração |
| Chave privada em log | Nunca transmitir ao backend |
| Roubo de sessão | Cookies seguros, expiração e revogação |
| Emissão indevida | Chave do emissor isolada e regra de elegibilidade |
| Correlação de dados | Separar identificadores públicos e dados sensíveis |
| Exposição involuntária | Consentimento antes de publicar |
| Relay indisponível | Publicação redundante e retry |
| Badge de emissor falso | Divulgar chave oficial e verificar assinatura |

## Critérios de aceite

1. Login válido cria sessão vinculada à chave pública.
2. Assinatura inválida, expirada ou reutilizada é rejeitada.
3. Nenhuma chave privada aparece em banco, logs ou rede do backend.
4. Conclusão cria concessão interna sem publicação automática.
5. Publicação exige consentimento explícito e versionado.
6. Evento `kind 8` referencia uma definição `kind 30009` válida.
7. O sistema registra ID do evento e confirmação por relay.
8. Falha de publicação não bloqueia tarefa ou pagamento.
9. A participante consegue encerrar a sessão.
10. Reputação é exibida como evidência e emissor, não como promessa de emprego.

## Referências

- [Nostr Implementation Possibilities](https://github.com/nostr-protocol/nips)
- [NIP-07 — capacidade de assinatura no navegador](https://github.com/nostr-protocol/nips/blob/master/07.md)
- [NIP-46 — assinatura remota](https://github.com/nostr-protocol/nips/blob/master/46.md)
- [NIP-58 — badges](https://github.com/nostr-protocol/nips/blob/master/58.md)
