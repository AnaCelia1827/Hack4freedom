# Fluxo de execução do Bluejet

## 1. Objetivo

Este documento consolida a sequência de execução do projeto Bluejet a partir do
estado atual do repositório. A prioridade é preservar o trabalho local, fechar o
golden path do MVP e somente depois refinar as superfícies visuais e os fluxos
secundários.

O caminho central do produto é:

```text
Aprender
→ comprovar uma competência
→ desbloquear uma tarefa financiada
→ executar e entregar
→ receber aprovação humana
→ receber em Lightning
→ construir reputação
```

## 2. Sequência geral de desenvolvimento

```text
Preservar código local
→ integrar mudanças da main
→ configurar o ambiente
→ persistir o domínio no PostgreSQL
→ fechar autenticação Nostr
→ fechar capacitação e SkillEvidence
→ fechar tarefa, reserva e entrega
→ fechar revisão e obrigação financeira
→ integrar Lightning real
→ completar frontend e Figma
→ testar o golden path
→ preparar o Demo Day
```

## 3. Etapa 0 — Estabilizar o Git

### Execução

1. Atualizar `.gitignore` para excluir `__pycache__`, `dist`, ambientes virtuais,
   caches e demais arquivos gerados.
2. Revisar os arquivos ainda não rastreados.
3. Separar commits coerentes para:
   - documentação e ADRs;
   - fundação do backend;
   - frontend;
   - OpenAPI e migrations;
   - testes.
4. Publicar a branch `bluejet-development` no repositório remoto.
5. Integrar `origin/main` somente depois de preservar o estado local.
6. Resolver a organização canônica da documentação:
   - Docusaurus na raiz com conteúdo em `docs/`; ou
   - Docusaurus integralmente dentro de `docs/`.

### Gate de saída

- Todo o código do produto está preservado no Git.
- A branch de desenvolvimento possui upstream remoto.
- O workspace não contém artefatos gerados sendo tratados como código-fonte.
- A organização documental foi definida antes da resolução dos conflitos com a
  `main`.

## 4. Etapa 1 — Ambiente funcional

### Execução

1. Criar o ambiente Python da API e instalar as dependências declaradas.
2. Configurar `DATABASE_URL` para o projeto PostgreSQL.
3. Aplicar o mecanismo de migrations existente.
4. Configurar CORS ou um proxy de desenvolvimento entre Vite e Flask.
5. Alinhar as origens configuradas com a porta real do frontend.
6. Validar cookies de sessão, `SameSite`, ambiente de produção e HTTPS.
7. Atualizar o OpenAPI para representar todas as rotas realmente expostas pela
   API.
8. Validar deep links do SPA no ambiente de deploy escolhido.

### Gate de saída

- Frontend, API e PostgreSQL iniciam com comandos documentados.
- O frontend consome a API pelo navegador sem erro de CORS ou cookie.
- Migrations podem ser aplicadas em banco vazio.
- Os contratos OpenAPI correspondem ao runtime Flask.
- Atualizar uma rota profunda não retorna 404 do servidor estático.

## 5. Etapa 2 — Persistência PostgreSQL

Substituir progressivamente os dicionários e listas em memória, nesta ordem:

1. identidade, challenge, sessão e onboarding;
2. cursos, aulas, progresso, quiz e `SkillEvidence`;
3. organizações, tarefas e financiamento;
4. reservas, assignments e submissões;
5. reviews e obrigações de pagamento;
6. payout attempts, provider payments e recibos;
7. comunidade e moderação;
8. ledger, audit log, outbox e inbox.

### Regras

- Operações financeiras usam transações de banco.
- Valores em sats, millisats e centavos são inteiros.
- Ledger e audit log são append-only.
- Correções financeiras usam lançamentos compensatórios.
- Restrições únicas e índices de concorrência devem existir no banco, não apenas
  no código Python.

### Gate de saída

- Reiniciar a API não perde sessão, progresso, tarefa, entrega ou pagamento.
- Concorrência de reserva e payout é protegida por constraints e transações.
- Outbox é persistida na mesma transação da mudança de domínio.

## 6. Etapa 3 — Identidade e cadastro

### Fluxo

```text
Landing
→ cadastro do perfil
→ conexão Nostr
→ assinatura do challenge
→ criação da sessão
→ perfil autenticado
```

### Execução

- Ligar o onboarding à pubkey Nostr autenticada.
- Remover a expectativa de senha caso a autenticação oficial permaneça
  exclusivamente Nostr.
- Verificar criptograficamente o evento assinado.
- Rejeitar challenge expirado, utilizado ou divergente.
- Persistir somente chave pública e dados de sessão; nunca `nsec`, seed ou
  mnemonic.
- Carregar nome, avatar, papéis e status de verificação no `AppShell`.
- Implementar logout e revogação de sessão.
- Preservar e validar `returnTo`.

### Gate de saída

- Uma nova participante conclui o cadastro e entra novamente com a mesma
  identidade Nostr.
- Nenhuma chave privada chega ao backend.
- Sessão inválida ou expirada redireciona corretamente para `/entrar`.

## 7. Etapa 4 — Capacitação, quiz e SkillEvidence

### Fluxo

```text
Catálogo
→ curso
→ módulo
→ aula
→ atividade educacional
→ quiz
→ nota mínima de 80%
→ SkillEvidence
→ consentimento opcional do badge
```

### Execução

- Preservar a hierarquia `Course → Module → Lesson → LearningActivity`.
- Persistir inscrição, progresso, conclusão, anotações e submissões
  educacionais.
- Manter atividade educacional separada de entrega profissional.
- Registrar todas as tentativas de quiz.
- Criar no máximo uma `SkillEvidence` para a mesma competência e versão de
  avaliação.
- Usar a `SkillEvidence` interna como fonte de verdade.
- Solicitar publicação do badge somente após consentimento explícito.
- Publicar badge por outbox, sem bloquear tarefa ou pagamento.

### Gate de saída

- Nota inferior a 80% não cria `SkillEvidence`.
- Nota igual ou superior a 80% cria evidência persistente.
- A evidência desbloqueia a tarefa mesmo se o relay ou o badge falhar.

## 8. Etapa 5 — Tarefa financiada e reserva

### Fluxo administrativo

```text
Criar organização
→ criar PaidTask em DRAFT
→ criar TaskFundingReservation
→ validar cobertura integral
→ publicar PaidTask
```

### Fluxo da participante

```text
Lista de tarefas
→ detalhe
→ verificar elegibilidade
→ reservar uma vaga por 60 minutos
→ criar AssignmentReservation/Assignment
→ iniciar o trabalho
```

### Regras

- Uma `PaidTask` possui uma vaga no MVP.
- Tarefa não financiada não pode ser publicada.
- `OpportunityListing` externa não cria assignment nem pagamento.
- `TaskFundingReservation` representa o dinheiro reservado para a tarefa.
- `AssignmentReservation` representa a exclusividade temporária da vaga.
- Expiração após 60 minutos libera a vaga.
- Expiração não devolve automaticamente o financiamento.
- A tarefa pode ser reservada novamente por outra participante.
- O fluxo de candidatura tradicional deve ser removido do golden path da
  `PaidTask` ou formalizado explicitamente; ele não deve ocorrer depois da
  criação do assignment sem produzir uma decisão real.

### Gate de saída

- Duas participantes concorrentes não reservam a mesma vaga.
- Uma tarefa expirada volta a ficar disponível sem movimentação financeira
  automática.
- A participante sem `SkillEvidence` não inicia a tarefa protegida.

## 9. Etapa 6 — Trabalho, entrega e revisão

### Fluxo

```text
Assignment reservado
→ rascunho privado
→ upload privado
→ envio final
→ revisão humana
   ├─ solicitar uma correção
   ├─ rejeitar com justificativa
   └─ aprovar
```

### Execução

- Criar workspace do assignment separado da tela de entrega.
- Restaurar o rascunho quando a participante retornar.
- Armazenar binários em storage privado.
- Usar URLs temporárias para download e preview.
- Validar MIME, tamanho, propriedade e estado do upload no servidor.
- Impedir acesso horizontal ao assignment e à submissão.
- Tornar o envio final explícito e idempotente.
- Permitir uma correção no MVP.
- Exigir justificativa para correção ou rejeição.
- Impedir IA de aprovar ou rejeitar pagamento.
- Tornar a aprovação irreversível para fins da obrigação financeira.

### Gate de saída

- Uma participante não acessa a entrega de outra.
- Duplo clique não cria submissão duplicada.
- Aprovação duplicada não cria uma segunda obrigação.
- A entrega aprovada deixa de aparecer como pendente de revisão.

## 10. Etapa 7 — Obrigação, ledger e Lightning

### Fluxo

```text
Aprovação humana
→ PaymentObligation OPEN
→ invoice BOLT11 pelo valor exato
→ PayoutAttempt
→ CLEARING/PROCESSING
→ xpay
→ SETTLED ou AMBIGUOUS
→ listpays/reconciliação
→ recibo
```

### Execução

- Criar `PaymentObligation` na mesma transação da aprovação.
- Permitir somente um `PayoutAttempt` pagável por obrigação.
- Fazer transição atômica da obrigação de `OPEN` para
  `CLEARING/PROCESSING`.
- Usar lock pessimista ou compare-and-swap.
- Criar índice único parcial ou mecanismo equivalente para attempts ativos.
- Criar attempt e outbox na mesma transação.
- Validar valor, moeda, expiração, rede e payment hash da invoice.
- Usar Core Lightning/CLNRest somente pela rede privada.
- Usar `xpay` para pagamento e `listpays` para reconciliação.
- Tratar timeout após possível envio como `AMBIGUOUS`.
- Não realizar retry automático de estado `AMBIGUOUS`.
- Permitir retry somente após falha definitiva ou reconciliação.
- Gerar recibo a partir de pagamento liquidado.
- Exibir `REAL`, `SANDBOX` ou `MOCK` em todas as superfícies financeiras.

### Gate de saída

- Apenas um `xpay` pode ser emitido por obrigação ativa.
- Invoice expirada pode ser substituída sem perder a aprovação.
- Retry não produz pagamento duplicado.
- Pagamento real é reconciliado e gera recibo rastreável.

## 11. Etapa 8 — Fluxo completo do frontend

### Árvore funcional

```text
/
/entrar
/cadastro/*
/app/comunidade
/app/capacitacao/*
/app/oportunidades/*
/app/trabalhos/*
/app/revisao
/app/pagamentos/*
/app/recibos/*
/app/carteira
```

### Checklist por tela

Para cada tela:

1. carregar a entidade real pelo contrato OpenAPI;
2. implementar estado de loading;
3. implementar estado vazio;
4. implementar erro recuperável;
5. diferenciar 401, 403 e 404;
6. implementar sucesso e confirmação;
7. preservar IDs e continuidade entre telas;
8. implementar desktop e mobile;
9. validar teclado e foco;
10. comparar com o frame correspondente no Figma.

### Regras visuais

- O Figma define apresentação e interação visual.
- Requisitos, ADRs e OpenAPI definem comportamento e regras de negócio.
- Divergências devem ser registradas antes da decisão.
- Nenhum asset pode depender de URL temporária do plugin.
- Score nunca é apresentado como saldo.
- Capital de liquidez não é apresentado como rendimento da participante.
- Simulação permanece separada de impacto realizado.

### Gate de saída

- Nenhuma tela usa dados de domínio hardcoded.
- Lista, detalhe, assignment, entrega e carteira preservam a mesma entidade.
- O golden path funciona em desktop e mobile.

## 12. Etapa 9 — Comunidade e oportunidades externas

### Comunidade mínima P0

- visualizar feed;
- publicar aprendizado, dúvida ou conquista;
- informar antes da assinatura que a publicação Nostr é pública e difícil de
  remover;
- reagir e comentar conforme os contratos aprovados;
- denunciar conteúdo;
- aplicar moderação local mínima.

### Oportunidades externas P0

- listar separadamente de `PaidTask`;
- identificar visualmente como oportunidade externa;
- abrir a fonte original;
- nunca criar assignment, obrigação ou pagamento.

### Fora do P0

- localização;
- conexão segura;
- premium;
- mensagens privadas;
- feed avançado;
- algoritmos de recomendação.

### Gate de saída

- `OpportunityListing` nunca é confundida com `PaidTask`.
- A interface avisa sobre publicidade antes de publicar no Nostr.
- Falha do relay não bloqueia os fluxos privados do produto.

## 13. Etapa 10 — Hardening e Demo Day

### Execução

1. Executar testes unitários e de integração.
2. Executar testes concorrentes de reserva e payout.
3. Executar E2E do golden path em desktop e mobile.
4. Simular timeout, relay indisponível e falha de reconciliação.
5. Confirmar ausência de tokens, invoices e dados pessoais nos logs.
6. Preparar seed determinístico.
7. Preparar reset seguro da demonstração.
8. Ensaiar o fluxo completo em até cinco minutos.
9. Preparar fallback sem apresentar dados `MOCK` como reais.

### Gate de saída

- Testes, typecheck, lint e build passam.
- O pagamento Lightning real foi ensaiado.
- O reset da demo é reproduzível.
- Jurados conseguem distinguir claramente operação real, sandbox e simulação.

## 14. Fluxo percebido pela participante

```text
Landing
→ entrar com Nostr
→ concluir trilha curta
→ obter SkillEvidence
→ encontrar tarefa desbloqueada
→ reservar por 60 minutos
→ realizar o trabalho
→ enviar entrega privada
→ receber aprovação humana
→ fornecer invoice BOLT11
→ receber Lightning
→ visualizar recibo e carteira
```

O badge é um workflow paralelo:

```text
SkillEvidence
→ consentimento opcional
→ publicação do badge NIP-58

Falha do badge
→ não bloqueia a tarefa
→ não bloqueia o pagamento
```

## 15. Ordem crítica imediata

1. Preservar e publicar a branch de desenvolvimento.
2. Integrar a `main` e resolver a estrutura de documentação.
3. Fazer frontend e API comunicarem-se localmente.
4. Conectar PostgreSQL e substituir o estado em memória.
5. Persistir identidade, onboarding e capacitação.
6. Persistir tarefa, financiamento, assignment e entrega.
7. Implementar revisão, obrigação e ledger.
8. Integrar pagamento Lightning real e reconciliação.
9. Completar e validar visualmente as telas pelo Figma.
10. Executar e ensaiar o golden path completo.

