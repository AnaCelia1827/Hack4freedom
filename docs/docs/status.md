---
sidebar_label: Status
---

# Status do projeto

**MVP integrado — autenticação Nostr segura de ponta a ponta e pagamento
Lightning real implementados; preparação para piloto controlado.**

Atualização: **24 de julho de 2026**.

## Resumo executivo

A solução possui frontend React, API Flask, fluxo de capacitação, tarefas,
revisão e núcleo financeiro em PostgreSQL. A jornada principal já conecta a
identidade Nostr da participante a uma sessão verificada e conclui o pagamento
de uma tarefa aprovada pela Lightning Network.

O projeto deixou de ser apenas uma demonstração financeira em `MOCK`. O fluxo
crítico já pode ser apresentado com pagamento real em ambiente controlado. Isso
não significa que a plataforma esteja pronta para operação pública: parte dos
domínios ainda precisa de persistência durável, e os controles operacionais,
jurídicos e de privacidade precisam ser validados antes de ampliar usuários ou
valores.

Este status considera a versão funcional atual informada pela equipe, posterior
ao snapshot técnico `9d08c4c`. Antes de uma liberação externa, essa versão deve
receber tag, evidências de CI e registro dos testes ponta a ponta.

## Classificação atual

| Dimensão | Estado | Avaliação |
|---|---|---|
| Descoberta e definição do problema | **Estruturada** | problema, público e contexto brasileiro documentados |
| Proposta e modelo de negócio | **Em evolução** | hipóteses de adoção e sustentabilidade ainda precisam de validação |
| Experiência web | **Implementada** | SPA responsiva com as jornadas principais |
| API de negócio | **Parcial** | rotas e regras existem, mas alguns domínios ainda dependem de memória |
| Persistência financeira | **Implementada** | obrigações, tentativas, ledger e outbox usam PostgreSQL |
| Autenticação Nostr | **Implementada** | desafio, assinatura, verificação criptográfica e sessão segura de ponta a ponta |
| Badges e comunidade Nostr | **Parcial** | não fazem parte do caminho crítico já validado |
| Pagamento Lightning | **Implementado** | invoice BOLT11 validada, pagamento real, confirmação e reconciliação |
| Conversão Pix | **Não implementada** | integração Hodle permanece opcional e planejada |
| Segurança para produção | **Em validação** | caminho crítico protegido; operação pública ainda exige revisão independente |
| Qualidade automatizada | **Parcial** | CI cobre documentação, backend/PostgreSQL e build web; cobertura ponta a ponta deve crescer |

## O que funciona hoje

- autenticação por evento Nostr assinado e verificado criptograficamente;
- proteção contra desafio expirado, replay e divergência de pubkey;
- sessão segura sem transmissão ou armazenamento da chave privada;
- navegação pelas telas públicas e autenticadas;
- capacitação, quiz e geração de evidência;
- cadastro, funding e publicação de tarefas;
- reserva exclusiva de uma vaga por 60 minutos;
- candidatura, entrega e revisão humana;
- criação da obrigação depois da aprovação;
- validação de invoice BOLT11;
- criação idempotente da tentativa de pagamento;
- pagamento Lightning real e acompanhamento do resultado;
- reconciliação entre tentativa, obrigação, ledger e recibo;
- ledger de partidas dobradas protegido contra alteração;
- health checks e pipeline de build e testes.

## Jornada validada

```text
login Nostr verificado
  → capacitação
  → tarefa financiada
  → reserva e entrega
  → revisão humana
  → obrigação de pagamento
  → invoice BOLT11
  → pagamento Lightning real
  → confirmação, ledger e recibo
```

A participante não precisa compartilhar chave privada nem compreender canais,
roteamento ou infraestrutura do nó para concluir a jornada.

## O que permanece parcial ou simulado

- alguns fluxos de aprendizagem, trabalho, revisão ou comunidade ainda podem
  perder estado após reinício;
- uploads privados ainda precisam de armazenamento de objetos e inspeção do
  arquivo real;
- publicação e confirmação de badges NIP-58 precisam de validação separada;
- métricas de impacto ainda precisam distinguir dados realizados de projeções;
- capital de liquidez, canais, taxas e rendimentos permanecem `MOCK`;
- conversão para reais via Hodle/Pix não está integrada;
- painel completo de doadores e empresas permanece fora do MVP atual.

Esses elementos não devem ser apresentados como concluídos durante a
demonstração.

## Riscos que ainda bloqueiam produção pública

1. **Persistência:** todos os estados necessários para retomar capacitação,
   tarefa, revisão e suporte precisam sobreviver a reinícios.
2. **Autorização:** a matriz de papel e propriedade deve ser testada em todas as
   rotas privadas, administrativas e financeiras.
3. **Privacidade:** dados desnecessários ou sensíveis não podem permanecer em
   `localStorage`, logs, relays ou ambientes de demonstração.
4. **Tesouraria:** pagamentos reais exigem limites por transação e período,
   segregação de credenciais e procedimento de emergência.
5. **Operação:** faltam comprovação de backup e restauração, observabilidade,
   alertas, suporte e resposta a incidentes.
6. **Qualidade:** o fluxo ponta a ponta precisa cobrir timeout, estado ambíguo,
   reinício e indisponibilidade do provedor.
7. **Conformidade:** responsabilidades, consentimentos, retenção e tratamento de
   dados devem ser validados antes do piloto.

A avaliação anterior em
[Segurança e privacidade](implementação/seguranca.md) foi produzida antes da
integração Nostr e Lightning atual e deve ser reexecutada contra a versão
marcada para o piloto.

## Escopo responsável para a demonstração

Para o Demo Day de 25 de julho de 2026, a apresentação pode demonstrar:

```text
entrada segura → capacitação → tarefa → entrega → revisão
               → pagamento Lightning real → recibo
```

A demonstração deve:

- utilizar valores baixos e saldo previamente limitado;
- usar identidade e dados preparados exclusivamente para o evento;
- mostrar a verificação da assinatura sem expor chave ou token;
- apresentar status, `payment_hash`, ledger e recibo conciliados;
- diferenciar o pagamento real das métricas e funcionalidades ainda em `MOCK`;
- possuir plano de contingência caso rede ou provedor fiquem indisponíveis;
- nunca executar retry manual quando o estado do pagamento for ambíguo.

## Critério para iniciar piloto controlado

O piloto pode começar quando:

- a versão integrada estiver marcada e reproduzível;
- autenticação Nostr e pagamento Lightning possuírem testes ponta a ponta;
- toda rota privada validar papel e propriedade;
- estados essenciais sobreviverem ao reinício da aplicação;
- timeout de pagamento for reconciliado sem duplicidade;
- tesouraria possuir saldo e limites isolados para o piloto;
- monitoramento alertar pagamentos `AMBIGUOUS` e divergências;
- backup e restauração estiverem testados;
- não houver achado crítico aberto na revisão de segurança;
- organização parceira, suporte e tratamento de dados estiverem definidos.

O aumento de coorte ou valor deve ocorrer somente após uma decisão formal de
`go/no-go` baseada nos resultados do piloto.
