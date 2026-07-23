---
sidebar_position: 5
sidebar_label: Tecnologias por feature
---

# Arquitetura de Tecnologias por Feature

Este documento define quais tecnologias devem ser utilizadas em cada funcionalidade do projeto, o papel de cada componente e o que deve ser implementado ou simulado no MVP do Hack4Freedom Brasil 2026.

As decisões que orientam a arquitetura estão em [Fluxos Fechados do MVP](fluxos.md) e [Requisitos do Produto](requisitos.md).

## 1. Arquitetura recomendada

O projeto utiliza uma arquitetura híbrida:

- Nostr para identidade, comunidade e reputação portátil;
- Breez para a carteira da trabalhadora;
- Core Lightning para a tesouraria e o nó da plataforma;
- Hodle para entrada e saída via Pix;
- Flask e SQLite para regras de negócio e dados privados.

```text
Frontend React/PWA
   |
   +-- Nostr -> identidade, comunidade e badges
   |
   +-- Breez -> carteira da trabalhadora
   |
   +-- Flask -> cursos, tarefas, aprovação e financeiro
                    |
                    +-- Core Lightning -> pagamentos e nó
                    +-- Hodle -> entrada e saída via Pix
                    +-- SQLite -> dados operacionais e ledger
```

## 2. Matriz de features e tecnologias

| Feature | Tecnologia | Uso no projeto | Prioridade |
|---|---|---|---|
| Interface web/mobile | React + Vite + PWA | Aplicação instalável no celular | Essencial |
| Estilização | Tailwind CSS | Construção rápida e consistente das telas | Essencial |
| Backend | Python + Flask | APIs, regras de negócio, tarefas e pagamentos | Essencial |
| Persistência do MVP | SQLite + SQLAlchemy | Dados operacionais e ledger financeiro | Essencial |
| Login descentralizado | Nostr + NIP-07 | Login por assinatura, sem senha | Essencial |
| Login sem extensão | NIP-46 | Assinatura remota por aplicativo Nostr | Posterior |
| Perfil portátil | Nostr, evento `kind 0` | Nome, foto, descrição e chave pública | Essencial |
| Comunidade | NIP-72 | Comunidade moderada de capacitação | Recomendado |
| Mensagens privadas | NIP-17 + NIP-44 | Comunicação privada e criptografada | Posterior |
| Badge de capacitação | NIP-58 | Certificado assinado e portátil | Essencial |
| Trilhas educacionais | Flask + SQLite | Conteúdo, progresso e desbloqueios | Essencial |
| Marketplace de tarefas | Flask + SQLite | Publicação, reserva, entrega e aprovação | Essencial |
| Evidência da entrega | Backend + armazenamento privado | Arquivos e respostas protegidos | Essencial |
| Carteira da usuária | Breez SDK — Spark | Receber e controlar satoshis | Essencial |
| Identificador de pagamento | Lightning Address/LNURL-Pay | Endereço legível para recebimento | Recomendado |
| Notificação de pagamento | Webhook do Breez | Atualizar recibos e avisar a usuária | Recomendado |
| Tesouraria pagadora | Core Lightning | Origem dos pagamentos das tarefas | Recomendado |
| API do nó | CLNRest | Pagamentos, consultas e métricas | Recomendado |
| Canais e roteamento | Core Lightning + Bitcoin Core | Infraestrutura patrocinada | Experimental |
| Tesouraria on-chain | `bdk_wallet` | Descriptors, PSBT e possível multisig | Futuro |
| Entrada e saída em reais | Hodle API + webhooks | Conversões entre Pix e Bitcoin | Essencial se disponível |
| Contabilidade | Ledger no backend | Separação de tarefa, matching, bônus e taxas | Essencial |
| Painel do patrocinador | Flask + CLNRest | Capital, canais, receitas e custos | Essencial |
| Revisão por IA | Modelo de IA + revisão humana | Triagem inicial de entregas | Opcional |
| eCash privado | Cashu + NIP-60/NIP-61 | Pagamentos internos privados | Futuro |

## 3. Frontend

### Tecnologias

- React;
- Vite;
- Tailwind CSS;
- Progressive Web App;
- `nostr-tools`;
- Breez SDK Spark com bindings compatíveis.

### Responsabilidades

O frontend deve:

- apresentar trilhas e microtarefas;
- solicitar assinaturas Nostr;
- exibir badges e perfil;
- integrar a carteira Breez;
- mostrar recibos e composição dos pagamentos;
- ocultar a complexidade de canais, invoices e roteamento.

A PWA permite uma experiência instalável no celular sem exigir a construção de aplicativos Android e iOS separados durante o hackathon.

## 4. Login e identidade com Nostr

### MVP: NIP-07

O frontend utiliza uma extensão ou signer compatível para solicitar uma assinatura:

```text
Usuária seleciona “Entrar com Nostr”
           |
           v
Signer assina um desafio
           |
           v
Backend verifica a assinatura
           |
           v
Sessão da plataforma é criada
```

O backend armazena somente a chave pública e os dados da sessão. A chave privada nunca deve ser enviada ao Flask ou salva no SQLite.

### Evolução: NIP-46

O NIP-46 permite assinatura remota por um aplicativo Nostr e reduz a dependência de extensões do navegador. Deve ser considerado depois que o happy path estiver funcionando.

## 5. Perfil, comunidade e mensagens

Use:

- evento `kind 0` para perfil;
- NIP-72 para comunidade moderada;
- NIP-17 com NIP-44 para mensagens privadas;
- dois ou três relays públicos para redundância.

O antigo NIP-04 não deve ser usado em código novo, pois foi substituído pelo fluxo de mensagens privadas do NIP-17.

Não é necessário operar um relay próprio no MVP. Essa infraestrutura aumenta o esforço sem melhorar o fluxo principal da demonstração.

## 6. Capacitação e progresso

Cursos, progresso e desbloqueios permanecem no backend tradicional.

Entidades sugeridas:

```text
courses
modules
lessons
enrollments
module_completions
```

Nostr não deve controlar:

- respostas privadas;
- número de tentativas;
- dados pessoais;
- progresso interno;
- regras de desbloqueio;
- mecanismos antifraude.

Quando uma trilha for concluída, o backend inicia a emissão do badge Nostr.

## 7. Badges com NIP-58

O NIP-58 é utilizado para:

1. publicar a definição do badge;
2. conceder o badge à chave pública da participante.

Exemplo conceitual:

```text
Badge: Introdução a Testes de Usabilidade
Emissor: chave pública oficial do projeto
Destinatária: chave pública da participante
Evidência: identificador interno ou hash não sensível
```

A chave de emissão deve ficar protegida no backend ou em um signer separado. Ela não pode ser incluída no código do frontend.

O badge é uma evidência assinada e portátil, mas não deve ser anunciado automaticamente como uma credencial W3C completa.

## 8. Microtarefas e aprovação

O marketplace e o workflow de tarefas devem ser implementados em Flask e SQLite:

```text
Criada
  |
  v
Financiada
  |
  v
Reservada
  |
  v
Em execução
  |
  v
Em análise
  |
  v
Aprovada
  |
  v
Paga
```

Tabelas sugeridas:

```text
users
tasks
task_assignments
task_submissions
task_reviews
funding_sources
payment_reservations
payments
ledger_entries
```

Entregas, documentos e informações pessoais ficam em armazenamento privado. Apenas um identificador ou hash não sensível pode ser associado a um evento público.

O NIP-90 não é necessário no MVP. Ele é mais adequado para serviços computacionais e Data Vending Machines do que para o workflow humano central do projeto.

## 9. Carteira da trabalhadora com Breez

O Breez SDK — Spark é utilizado dentro da aplicação da usuária para:

- criar ou restaurar a carteira;
- mostrar saldo;
- gerar invoices;
- receber por Lightning Address;
- manter histórico;
- enviar ou manter satoshis.

### Recebimento

```text
Backend aprova a tarefa
          |
          v
Carteira gera invoice ou Lightning Address
          |
          v
Tesouraria realiza o pagamento
          |
          v
Breez confirma o recebimento
          |
          v
Webhook atualiza o backend
```

Cada instância do SDK precisa de armazenamento próprio. Em uma aplicação WebAssembly, esse estado pode ser persistido no IndexedDB.

## 10. Tesouraria pagadora com Core Lightning

O Core Lightning controla a carteira operacional da plataforma:

```text
Flask
  |
  | CLNRest com credencial restrita
  v
Core Lightning
  |
  +-- paga invoices
  +-- consulta confirmações
  +-- acompanha canais
  +-- coleta métricas de roteamento
```

O backend pode integrar por CLNRest. A autenticação utiliza runes com permissões restritas.

Devem existir credenciais diferentes:

- rune somente de leitura para o painel;
- rune limitada a pagamentos para a tesouraria;
- acesso administrativo fora da aplicação.

O CLNRest não pode ser exposto diretamente ao frontend ou à internet sem controles adequados.

## 11. Nó Lightning

Para a infraestrutura patrocinada:

- Bitcoin Core fornece acesso à rede Bitcoin;
- Core Lightning gerencia canais e pagamentos;
- CLNRest conecta o backend ao nó;
- plugins podem futuramente automatizar políticas e métricas.

O funcionamento econômico e operacional está detalhado em [Canais Lightning, Roteamento e Receita do Nó](lightning.md).

### Parte real no Demo Day

- pagamento Lightning mainnet de poucos sats;
- consulta real do status;
- carteira Breez recebendo;
- badge Nostr publicado.

### Parte simulada e identificada

- aporte de 0,05 BTC;
- abertura de vários canais;
- histórico mensal de roteamento;
- custos e lucro líquido;
- projeção de bônus.

Construir um nó de roteamento competitivo durante o hackathon não é realista. A simulação precisa ser claramente identificada no painel e na apresentação.

## 12. BDK

O Bitcoin Dev Kit é útil para uma carteira Bitcoin on-chain customizada:

- geração de endereços;
- controle de UTXOs;
- descriptors;
- PSBTs;
- multisig;
- segregação da tesouraria do patrocinador.

BDK não substitui o Core Lightning nem o Breez.

Para código novo, deve-se usar o pacote `bdk_wallet`. O antigo crate `bdk` está depreciado.

Não é recomendado implementar BDK no primeiro MVP, a menos que seu uso seja explicitamente valorizado pela banca ou por uma categoria de premiação. A feature aumenta a complexidade e não melhora o momento principal da demonstração.

## 13. Pix e Hodle

A integração com Hodle deve ser isolada por uma interface interna:

```python
class FiatGateway:
    def create_deposit(self): ...
    def get_quote(self): ...
    def buy_bitcoin(self): ...
    def sell_bitcoin(self): ...
    def create_pix_withdrawal(self): ...
    def get_transaction_status(self): ...
```

Essa abstração permite utilizar um adaptador simulado se a API real, as credenciais ou os requisitos de compliance não estiverem disponíveis no Demo Day.

O fluxo deve mostrar taxas e cotações antes da confirmação e permitir saldo acumulado para evitar que os custos consumam micropagamentos.

## 14. Ledger financeiro

O SQLite deve manter um ledger append-only com eventos como:

```text
TASK_FUNDED
MATCHING_RESERVED
TASK_APPROVED
LIGHTNING_PAYMENT_SENT
LIGHTNING_PAYMENT_SETTLED
MATCHING_RELEASED
ROUTING_FEE_RECEIVED
REBALANCE_COST
BONUS_DISTRIBUTED
```

Cada lançamento contém:

- valor em sats;
- valor de referência em BRL;
- origem do recurso;
- tarefa associada;
- participante;
- timestamp;
- identificador da transação;
- status.

O saldo não deve existir somente como um número mutável. O painel precisa reconstruir a origem e o destino de cada valor a partir do ledger.

As regras completas estão em [Arquitetura Financeira e Fluxo de Pagamentos](financeiro.md).

## 15. Inteligência artificial

Um agente de IA pode ajudar na triagem inicial de tarefas com critérios objetivos, por exemplo:

- verificar se todos os campos foram preenchidos;
- detectar respostas duplicadas;
- classificar a entrega para revisão;
- explicar por que um critério pode não ter sido atendido.

No MVP, a decisão final deve permanecer com revisão humana. Isso reduz falsos negativos, vieses e disputas sobre pagamentos.

## 16. Cashu e eCash

Cashu e os NIPs 60 e 61 podem futuramente oferecer pagamentos internos com maior privacidade. Eles não são necessários no MVP porque acrescentam:

- uma mint e seu modelo de confiança;
- novas rotinas de backup;
- riscos de custódia;
- reconciliação adicional;
- mais uma experiência de carteira.

A prioridade deve permanecer no pagamento Lightning real para uma carteira controlada pela participante.

## 17. Stack consolidada

```text
Frontend
- React
- Vite
- Tailwind CSS
- PWA
- nostr-tools
- Breez SDK Spark

Backend
- Python
- Flask
- SQLAlchemy
- SQLite
- Webhooks
- jobs assíncronos simples

Freedom Tech
- Nostr: NIP-07, NIP-58 e NIP-72
- Breez SDK Spark
- Lightning Address/LNURL-Pay
- Core Lightning
- CLNRest
- Bitcoin Core

Integrações
- Hodle API
- dois ou três relays Nostr

Futuro
- PostgreSQL
- bdk_wallet
- multisig
- Cashu
- relay próprio
```

## 18. Ordem de implementação

1. Flask, SQLite, trilha e microtarefa.
2. Login Nostr.
3. Aprovação da tarefa.
4. Carteira Breez e geração da invoice.
5. Pagamento Lightning real.
6. Badge NIP-58.
7. Ledger e recibo detalhado.
8. Painel do patrocinador.
9. Hodle e Pix.
10. Métricas ou simulação do nó.

Se o tempo ficar curto, a prioridade é demonstrar:

```text
Tarefa aprovada -> pagamento Lightning real -> badge Nostr
```

Esse fluxo combina resolução do problema, impacto social e uso concreto das tecnologias do hackathon.

## 19. Referências técnicas

- [Nostr Protocol — NIPs](https://github.com/nostr-protocol/nips)
- [Breez SDK Spark](https://sdk-doc-spark.breez.technology/)
- [Breez — Lightning Address e LNURL-Pay](https://sdk-doc-spark.breez.technology/guide/receive_lnurl_pay.html)
- [Breez — Webhooks](https://sdk-doc-spark.breez.technology/guide/lnurl_webhooks.html)
- [Core Lightning — desenvolvimento de aplicações](https://docs.corelightning.org/docs/app-development)
- [Core Lightning — CLNRest](https://docs.corelightning.org/docs/rest)
- [Core Lightning — plugins](https://docs.corelightning.org/docs/plugin-development)
- [`bdk_wallet`](https://docs.rs/bdk_wallet/latest/bdk_wallet/)
- [Hodle](https://hodle.com.br/)
