# Auditoria técnica, visual e funcional — Frontend × Figma

Data da revisão: 2026-07-22  
Escopo: `apps/web` e contratos/documentação relacionados. Nenhum arquivo funcional foi alterado.

## 1. Resumo executivo

O repositório ainda não contém um frontend de produto completo: `apps/web` é um SPA React/Vite de demonstração, concentrado em `src/main.tsx`, enquanto o Figma descreve 17 experiências, incluindo onboarding, comunidade, oportunidades, trabalho, carteira, capacitação e wizard. A landing é a única tela com composição próxima da referência; as telas autenticadas são shells mínimos e vários caminhos do Figma não têm rota ou têm navegação quebrada.

Foram registrados 15 achados: **2 P0, 9 P1, 3 P2 e 1 P3**. Os maiores riscos são: cadastro impossível de concluir, aula/atividade sem rota, login com assinatura demo, detalhe de oportunidade sem carregar a entidade, ausência de submission/upload e uso de assets temporários do Figma. A ordem recomendada é corrigir primeiro rotas e fluxos críticos, depois continuidade de dados, layouts/responsividade e, por fim, design system e refinamento visual.

Marca canônica encontrada no código: **RESILIENCE**. `EMPOWERHER` não aparece no código. O Figma mistura as duas marcas; portanto, não recomendo introduzir `EMPOWERHER` sem uma decisão de produto.

### Evidência Figma consultada

Usei `get_design_context` (com screenshot incluído) para `66:2337`, `111:311`, `51:1072`, `101:9`, `48:117`, `48:631`, `48:374`, `51:1739`, `51:714`, `51:1960`, `101:119`, `133:480` e `133:378`. Também usei `get_screenshot` para `66:2337`, `111:311`, `101:9`, `51:1072`, `48:117` e `133:378`. Entre as medidas observáveis: landing com container de aproximadamente 1200 px, hero 544 + 544 px, título 48/52,8 px, cards de 373 px e seção de privacidade 1152 px; oportunidades em cards horizontais; revisão com stepper, resumo, recompensa, duração, requisitos e consentimentos.

## 2. Stack identificado

| Área | Encontrado |
|---|---|
| Framework | React 19 + TypeScript |
| Build/dev | Vite 8.1.5 (`apps/web`) |
| Roteamento | Parser manual de `location.pathname`, `history.pushState` e `popstate`; nenhuma biblioteca |
| Estilos | CSS global em `src/styles.css` e `src/app.css`; Inter via Google Fonts |
| Componentes | Componentes locais dentro de `main.tsx`; `lucide-react` instalado, mas não usado |
| Estado | `useState`/`useEffect`; sem store/form library |
| Dados | `fetch` direto para Flask em `VITE_API_URL` ou `http://localhost:5000`; backend atual in-memory |
| Autenticação | Sessão por cookie no backend, porém login frontend envia `demo-pubkey`/`demo-signature` |
| Testes | Sem scripts/testes frontend; pytest somente no backend |
| Qualidade | Sem lint/formatter/typecheck script; `tsc -b` roda dentro do build frontend |
| Documentação | Docusaurus na raiz e ADR-003 sobre inspeção Figma |

## 3. Mapa de rotas e Figma

| Rota atual | Componente/página | Arquivo | Figma node | Status |
|---|---|---|---:|---|
| `/` | `Landing` | `apps/web/src/main.tsx:21` | 66:2337 | Implementada, visualmente divergente em conteúdo/ícones/privacidade |
| `/entrar` | `AuthPage` | `main.tsx:23` | 111:311 | Implementada, funcionalmente incompleta |
| `/cadastro/acesso` | `RegistrationPage` | `main.tsx:24` | 111:240 | Implementada, mas incompleta |
| `/cadastro/identificacao` | `RegistrationPage` | `main.tsx:24` | 111:170 | Implementada com estrutura incorreta |
| `/cadastro/habilidades` | `RegistrationPage` | `main.tsx:24` | 111:86 | Implementada com conteúdo genérico e avanço incorreto |
| `/cadastro/verificacao` | `RegistrationPage` | `main.tsx:24` | 111:6 | Implementada com conteúdo genérico e avanço incorreto |
| `/app/comunidade` | `Community` | `main.tsx:27` | 51:1072 | Implementada, visualmente/funcionalmente divergente |
| `/app/oportunidades` | `Opportunities` | `main.tsx:28` | 101:9 | Implementada, sem filtros/cards canônicos |
| `/app/oportunidades/:opportunityId` | `OpportunityDetail` | `main.tsx:29` | 48:117 | Implementada, mas detalhe hardcoded |
| `/app/oportunidades/:opportunityId/candidatura` | `Application` | `main.tsx:33` | — | Implementada, sem contrato/estado de candidatura |
| `/app/trabalhos/:assignmentId/entrega` | `Work` | `main.tsx:35` | 48:631 | Rota cai no componente, mas entrega/upload não implementados |
| `/app/carteira` | `Wallet` | `main.tsx:34` | 48:374 | Implementada como placeholder |
| `/app/capacitacao` | `Learning` | `main.tsx:30` | 51:1739 | Implementada, mas sem catálogo canônico |
| `/app/capacitacao/:courseId` | `Course` | `main.tsx:31` | — | Implementada, sem módulos/aulas |
| `/app/capacitacao/:courseId/aulas/:lessonId` | — | `main.tsx:26` | 51:714 | Não implementada; cai em 404 |
| `/app/capacitacao/:courseId/atividades/:activityId` | — | `main.tsx:26` | 51:1960 | Não implementada; cai em 404 |
| `/app/oportunidades/nova/basico` | `OpportunityWizard` | `main.tsx:32` | 101:119 | Implementada como formulário único mínimo |
| `/app/oportunidades/nova/requisitos` | `OpportunityWizard` | `main.tsx:32` | 133:480 | Implementada, sem requisitos/recompensa |
| `/app/oportunidades/nova/midia` | `OpportunityWizard` | `main.tsx:32` | — | Implementada nominalmente, sem uploader |
| `/app/oportunidades/nova/revisao` | `OpportunityWizard` | `main.tsx:32` | 133:378 / 101:183 | Implementada, publica sem validação/termos |

## 4. Score por página

| Página | Visual | Responsivo | Funcional | A11y | Código |
|---|---:|---:|---:|---:|---:|
| Landing | 68 | 60 | 55 | 55 | 52 |
| Login | 25 | 55 | 20 | 35 | 45 |
| Cadastro | 18 | 50 | 10 | 30 | 30 |
| Comunidade | 20 | 35 | 35 | 35 | 42 |
| Oportunidades | 25 | 45 | 35 | 35 | 42 |
| Detalhe | 8 | 50 | 15 | 35 | 35 |
| Entrega profissional | 10 | 45 | 10 | 30 | 32 |
| Carteira | 8 | 50 | 5 | 30 | 35 |
| Capacitação | 18 | 45 | 30 | 32 | 40 |
| Aula/atividade | 0 | 0 | 0 | 0 | 20 |
| Wizard | 15 | 45 | 10 | 25 | 35 |

Os scores são relativos à estrutura e intenção visual dos nós consultados, não uma afirmação de pixel-perfect. As notas baixas nas telas autenticadas refletem principalmente ausência de estrutura, dados e estados, não apenas diferenças de CSS.

## 5. Achados prioritários

| ID | Prioridade | Página | Resumo | Arquivo | Figma |
|---|---|---|---|---|---:|
| FE-FIGMA-001 | P0 | Cadastro | O fluxo não implementa quatro etapas nem persiste/valida dados | `main.tsx:24` | 111:240, 111:170, 111:86, 111:6 |
| FE-FIGMA-002 | P0 | Capacitação | A navegação para aula e atividade termina em 404 | `main.tsx:26,31` | 51:714, 51:1960 |
| FE-FIGMA-003 | P1 | Login | Login envia credenciais/signature demo e não oferece o formulário do Figma | `main.tsx:23` | 111:311 |
| FE-FIGMA-004 | P1 | Oportunidade | O detalhe ignora `opportunityId` como entidade e exibe conteúdo fixo | `main.tsx:29` | 48:117 |
| FE-FIGMA-005 | P1 | Trabalho | Entrega, upload, rascunho e submissão não estão ligados ao assignment | `main.tsx:35` | 48:631 |
| FE-FIGMA-006 | P1 | AppShell | Rotas `/app` não têm guarda de sessão/autorização nem 403 | `main.tsx:18,25` | 51:1072 |
| FE-FIGMA-007 | P1 | Oportunidades/Wizard | Tabs, filtros e draft não têm estado de URL/persistência confiável | `main.tsx:28,32` | 101:9, 101:119, 133:480, 133:378 |
| FE-FIGMA-008 | P1 | Landing | Ícones dependem de URLs temporárias do MCP do Figma | `main.tsx:8` | 66:2337 |
| FE-FIGMA-009 | P1 | Comunidade | O layout canônico de três colunas, composer, mídia e reações não existe | `main.tsx:27` | 51:1072 |
| FE-FIGMA-010 | P1 | Formulários | Erros de fetch viram estado vazio e não há loading/retry/submitting | `main.tsx:27-31` | 51:1072, 101:9, 51:1739 |
| FE-FIGMA-011 | P1 | Rotas profundas | O build é SPA sem configuração documentada de fallback do servidor | `vite.config.ts:1` | todos os nós com rota profunda |
| FE-FIGMA-012 | P2 | Carteira | Carteira é placeholder e não apresenta score, gráficos ou extrato | `main.tsx:34` | 48:374 |
| FE-FIGMA-013 | P2 | Capacitação | Cards e curso não preservam a hierarquia Course → Module → Lesson | `main.tsx:30-31` | 51:1739, 51:714 |
| FE-FIGMA-014 | P2 | Design system | Tokens são valores hex repetidos e componentes de interface estão inline | `styles.css:1`, `main.tsx:21-38` | 66:2337, 101:9 |
| FE-FIGMA-015 | P3 | Acessibilidade | Labels, foco, `aria-current`, tabs e estados de erro são insuficientes | `main.tsx:23-32`, `styles.css:1` | 111:311, 101:9 |

## 6. Detalhamento dos achados

### FE-FIGMA-001 — Torne o cadastro um fluxo realmente concluível

Prioridade: P0  
Rota: `/cadastro/*`  
Figma: `111:240`, `111:170`, `111:86`, `111:6`  
Arquivo: `apps/web/src/main.tsx:24`

**Esperado:** stepper de quatro etapas, validação por etapa, seleção de habilidades, verificação, termos e persistência ao voltar/atualizar. **Atual:** qualquer etapa diferente de `acesso` renderiza a mesma textarea, exibe “Passo 02” e vai diretamente para a comunidade; não há estado compartilhado nem submit. O usuário não consegue completar o cadastro especificado pelo Figma.

Recomendação: modelar o draft por etapa, validar antes de avançar e manter a etapa atual no path sem perder os dados.

### FE-FIGMA-002 — Adicione as rotas de aula e atividade

Prioridade: P0  
Rota: `/app/capacitacao/:courseId/aulas/:lessonId` e `/atividades/:activityId`  
Figma: `51:714`, `51:1960`  
Arquivo: `apps/web/src/main.tsx:26,31`

**Esperado:** o curso abre aulas, sidebar, progresso, notas e atividades práticas. **Atual:** `Course` navega para `/aulas/${course.module_id}`, mas `AppRoute` só reconhece a lista e o detalhe exato do curso; ambos os caminhos profundos caem em `NotFound`. O fluxo de capacitação quebra imediatamente após iniciar uma aula.

Recomendação: registrar as duas rotas antes do fallback, usar separadamente `courseId`, `lessonId` e `activityId`, e buscar as entidades correspondentes.

### FE-FIGMA-003 — Remova o login demo do caminho de produção

Prioridade: P1  
Rota: `/entrar`  
Figma: `111:311`  
Arquivo: `apps/web/src/main.tsx:23`

Quando o usuário submete o único botão disponível, o cliente envia `pubkey: 'demo-pubkey'` e `signature: 'demo-signature'`, sem email/senha, seletor Participante/Contratante, loading ou mecanismo NIP-07. Isso não representa a autenticação real exposta pelo backend e faz o caminho crítico falhar ou tentar uma identidade fixa. Recomendação: conectar o adapter de assinatura real ou explicitar o modo sandbox na interface, com estados de erro/loading e retorno seguro à rota original.

### FE-FIGMA-004 — Carregue o detalhe pela entidade da rota

Prioridade: P1  
Rota: `/app/oportunidades/:opportunityId`  
Figma: `48:117`  
Arquivo: `apps/web/src/main.tsx:29`

**Esperado:** hero, organização, logo, título, score, tags, prazo, recompensa, requisitos e descrição da oportunidade selecionada. **Atual:** o componente não faz fetch; mostra “Opportunity ID: {id}”, o título genérico “Oportunidade” e uma mensagem fixa. Ao abrir qualquer card, não há continuidade de título, organização, recompensa ou imagem. Recomendação: buscar pelo ID e compartilhar o mesmo contrato/asset usado no card da lista, com 404 e loading distintos.

### FE-FIGMA-005 — Implemente a entrega ligada ao assignment

Prioridade: P1  
Rota: `/app/trabalhos/:assignmentId/entrega`  
Figma: `48:631`  
Arquivo: `apps/web/src/main.tsx:35`

**Esperado:** requisitos, texto, links, anexos, upload, salvar rascunho, envio final, confirmação e autorização. **Atual:** existe apenas uma textarea e um botão “Salvar rascunho” sem handler; o frontend não chama `/assignments/:assignmentId/submissions` nem `/uploads`. O trabalho não pode ser entregue nem produzir a submissão esperada pelo fluxo backend.

### FE-FIGMA-006 — Proteja o AppShell e trate 403

Prioridade: P1  
Rota: `/app/*`  
Figma: `51:1072`  
Arquivo: `apps/web/src/main.tsx:18,25`

Qualquer path iniciado por `/app` renderiza `AppShell` antes de qualquer verificação de sessão, e o cliente não tem estado de usuário/permissão nem tela 403. Mesmo que o backend rejeite chamadas, o usuário não autenticado consegue abrir shells e a aplicação mistura erro de autorização com vazio. Recomendação: centralizar uma guarda de sessão, preservar `returnTo` validado e diferenciar `401`, `403` e `404`.

### FE-FIGMA-007 — Faça filtros, tabs e draft persistirem

Prioridade: P1  
Rotas: `/app/oportunidades`, `/app/oportunidades/nova/*`  
Figma: `101:9`, `101:119`, `133:480`, `133:378`  
Arquivo: `apps/web/src/main.tsx:28,32`

A lista lê a query, mas ambos os tabs são botões sem ação e nenhum filtro visual existe; o wizard usa inputs não controlados que são desmontados a cada navegação e não há draft. Portanto voltar, atualizar ou compartilhar a URL perde o contexto e a revisão pode publicar um formulário vazio. Recomendação: estado de filtro sincronizado na URL e draft controlado por um contrato único entre etapas, com publicação bloqueada até os consentimentos/validações.

### FE-FIGMA-008 — Substitua assets temporários do MCP

Prioridade: P1  
Rota: `/`  
Figma: `66:2337`  
Arquivo: `apps/web/src/main.tsx:8`

`spark` e `play` apontam diretamente para `www.figma.com/api/mcp/asset/...`. Esses URLs são temporários por definição do MCP; após expirar, os ícones da landing quebram. Recomendação: exportar assets controlados para o repositório/CDN do produto, ou usar ícones já existentes quando forem visualmente equivalentes.

### FE-FIGMA-009 — Reproduza o shell de comunidade de três colunas

Prioridade: P1  
Rota: `/app/comunidade`  
Figma: `51:1072`  
Arquivo: `apps/web/src/main.tsx:27`

O frame mostra sidebar esquerda, feed central, sidebar direita, compositor, mídia, reações, comentários e estados de lista. A implementação renderiza apenas um painel de textarea e artigos com `category/content`, sem avatar, mídia, paginação, skeleton, erro ou layout responsivo equivalente. Recomendação: extrair o shell compartilhado e implementar estados do feed sem trocar o stack.

### FE-FIGMA-010 — Diferencie loading, vazio e erro

Prioridade: P1  
Rotas: comunidade, oportunidades, capacitação e curso  
Figma: `51:1072`, `101:9`, `51:1739`  
Arquivo: `apps/web/src/main.tsx:27-31`

Cada `catch` converte falha de rede/servidor em `[]` ou `null`; a UI então mostra “Nenhuma...” ou “Curso não encontrado”. Um backend indisponível fica indistinguível de ausência legítima de dados, não há loading, retry, disabled ou feedback de submissão. Recomendação: manter estados discriminados `loading/empty/error/notFound/forbidden` e oferecer retry.

### FE-FIGMA-011 — Documente e configure fallback para rotas profundas

Prioridade: P1  
Rotas: todos os paths profundos  
Figma: todos os frames roteados  
Arquivo: `apps/web/vite.config.ts:1`

O build gera somente `dist/index.html` e assets; não há configuração de hospedagem ou rewrite no repositório para que `/app/oportunidades/abc` e `/app/capacitacao/x/aulas/y` retornem o SPA após refresh. O dev server costuma fazer fallback, mas uma hospedagem estática pode responder 404 diretamente. Recomendação: adicionar o fallback na plataforma de deploy documentada e cobrir refresh em teste E2E.

### FE-FIGMA-012 — Substitua a carteira placeholder por dados derivados

Prioridade: P2  
Rota: `/app/carteira`  
Figma: `48:374`  
Arquivo: `apps/web/src/main.tsx:34`

O frame exige resumo, score, arrecadação, gráficos, distribuição, extrato e trabalhos em andamento; a tela atual só informa que pagamentos aparecerão depois e não faz requisição. Recomendação: consumir a carteira/ledger quando o contrato existir e incluir estados vazios, gráficos acessíveis e formatação de moeda.

### FE-FIGMA-013 — Preserve a hierarquia de capacitação

Prioridade: P2  
Rotas: `/app/capacitacao/*`  
Figma: `51:1739`, `51:714`, `51:1960`  
Arquivo: `apps/web/src/main.tsx:30-31`

O catálogo só exibe `title/objective` e o curso usa `module_id` como `lessonId`, além de contar `questions` como atividades. Isso não representa Course → Module → Lesson → LearningActivity e explica a navegação quebrada. Recomendação: tipar os contratos e encaminhar cada ID real para a tela correspondente.

### FE-FIGMA-014 — Centralize os tokens e padrões recorrentes

Prioridade: P2  
Área: design system  
Figma: `66:2337`, `101:9`  
Arquivo: `apps/web/src/styles.css:1`, `apps/web/src/main.tsx:21-38`

Os mesmos hexadecimais (`#121212`, `#1a1a1a`, `#5c3f46`, `#ff007f`, `#e5bcc5`) são repetidos em CSS e a maior parte de cards, inputs, estados e layouts está inline no arquivo de 39 linhas. Recomendação: criar tokens CSS e extrair apenas padrões recorrentes como `AppShell`, `Page`, `FormField`, `OpportunityCard`, `EmptyState` e `ErrorState`, sem abstrair cada elemento.

### FE-FIGMA-015 — Complete semântica de formulários, tabs e foco

Prioridade: P3  
Área: acessibilidade  
Figma: `111:311`, `101:9`, `133:378`  
Arquivo: `apps/web/src/main.tsx:23-32`, `apps/web/src/styles.css:1`

Inputs usam placeholder como texto principal, não há labels visíveis/associados para a maioria dos campos, tabs não têm semântica nem `aria-current`, não há estados de foco definidos e erros não são anunciados. Recomendação: usar `label`/`htmlFor`, headings e landmarks, roving focus/semântica de tabs quando aplicável, `aria-describedby` para erros e foco visível.

## 7. Revisão página por página

- **Landing (`66:2337`)**: CSS reproduz bem os números principais do hero, mas não implementa corretamente o card visual de ganhos, vários ícones/itens de privacidade e os assets são temporários. Há mistura de português/inglês no texto. No mobile a ordem é aceitável, mas a navegação e a arte são aproximações.
- **Login (`111:311`)**: falta card com email/senha, alternância de papel, senha visível, recuperação e estados de formulário.
- **Cadastro (`111:240`, `111:170`, `111:86`, `111:6`)**: um componente genérico substitui quatro telas e não conserva draft.
- **Comunidade (`51:1072`)**: ausência do shell de três colunas e das entidades visuais do feed.
- **Oportunidades (`101:9`; `48:223`)**: há lista API, mas faltam filtros, tabs funcionais, thumbnail, recompensa, tags e CTA canônico.
- **Detalhe (`48:117`)**: é placeholder e não mantém continuidade com a lista.
- **Entrega (`48:631`)**: não há upload, anexos, critérios, autosave ou submit.
- **Carteira (`48:374`)**: placeholder sem dados/visualizações.
- **Capacitação (`51:1739`)**: lista mínima; ausência de progresso, imagens, categoria, nível, carga horária e módulos.
- **Aula/atividade (`51:714`, `51:1960`)**: não implementadas e não roteadas.
- **Wizard (`101:119`, `133:480`, `133:378`, `101:183`)**: somente o nome da etapa muda; mídia, chips, moeda, resumo, termos e publicação segura estão ausentes. As duas revisões Figma foram consolidadas como uma experiência, conforme solicitado.

## 8. Componentes e design system

`Page`, `AppShell` e `Empty` são os únicos padrões compartilhados reais. Há oportunidade concreta de extrair `TopNavigation`, `TransactionalLayout`, `FormField`, `OpportunityCard`, `ProgressStepper`, `TagChip`, `MediaUploader`, `FileUploader`, `Breadcrumbs`, `ErrorState` e `ScoreBadge` depois que os contratos existirem. Não há tokens CSS nomeados; os valores do Figma aparecem como literais.

## 9. Responsividade

Há somente um breakpoint em 760 px. A landing troca colunas por bloco e cards por grid, mas não há validação renderizada em 1280/1024/768/390 nesta execução porque não havia ferramenta de browser/screenshot local disponível. O AppShell reduz fonte e padding sem menu alternativo; nav com quatro botões mais marca/avatar pode ficar comprimida em 390 px. Comunidade, filtros, tabelas/extratos, wizard e player não têm regras específicas. Trate como P1 qualquer caso confirmado de conteúdo inacessível no mobile antes de refinamentos menores.

## 10. Status pós-correções P0/P1

| Achado | Status | Evidência |
|---|---|---|
| FE-FIGMA-001 | Resolvido | Cadastro possui quatro etapas, validação e draft em `localStorage`. |
| FE-FIGMA-002 | Resolvido | Rotas de aula e atividade registradas e navegáveis. |
| FE-FIGMA-003 | Resolvido parcialmente | Login usa NIP-07 quando disponível e backend exige evento correspondente ao challenge/pubkey; validação criptográfica completa continua no adapter Nostr. |
| FE-FIGMA-004 | Resolvido | Detalhe chama `GET /paid-tasks/:id`. |
| FE-FIGMA-005 | Resolvido parcialmente | Entrega chama `/uploads` e submission, valida MIME/tamanho, bloqueia duplicidade e mostra erro; storage binário persistente ainda depende do adapter. |
| FE-FIGMA-006 | Resolvido | `SessionGate` consulta `/me` e preserva `returnTo`. |
| FE-FIGMA-007 | Resolvido | Tabs/filtros ficam na URL; wizard usa `localStorage` como retomada e sincroniza o mesmo draft com `POST /admin/paid-tasks/drafts`, `PATCH /admin/paid-tasks/drafts/:id` e publicação idempotente por draft. |
| FE-FIGMA-008 | Resolvido | Landing usa ícones locais em `apps/web/icons`. |
| FE-FIGMA-009 | Resolvido parcialmente | Shell de três colunas, compositor conectado a `POST /community/posts`, feed, reação, comentário e paginação offset foram conectados; mídia persistente ainda depende do backend/storage. |
| FE-FIGMA-010 | Resolvido parcialmente | Comunidade, lista, detalhe, catálogo, curso, aula e atividade distinguem loading/erro/vazio; `SessionGate` agora diferencia 401, 403 e erro de sessão; cancelamento de requests e estados específicos por endpoint continuam pendentes. |
| FE-FIGMA-011 | Resolvido | `public/_redirects` adiciona fallback SPA para deploys compatíveis. |
| FE-FIGMA-012 | Resolvido parcialmente | Carteira consome `GET /wallet/summary`; gráficos e ledger persistente continuam pendentes. |
| FE-FIGMA-013 | Resolvido parcialmente | Aula e atividade possuem rotas e submissão educacional separada; API agora expõe Course → Module → Lesson → Activity explicitamente, mas persistência completa ainda depende do banco. |
| FE-FIGMA-014 | Resolvido parcialmente | O curso agora oferece rota de quiz, envia respostas para `/modules/:moduleId/quiz-attempts`, exibe nota/SkillEvidence e permite consentimento de badge; resultado visual dedicado ainda não existe no Figma. |
| FE-FIGMA-015 | Resolvido | O catálogo de oportunidades consome `PaidTask` e `OpportunityListing` em coleções separadas, identifica `PAID_TASK`/`EXTERNAL_OPPORTUNITY` e só oferece detalhe/candidatura para tarefa remunerada. |
| FE-FIGMA-016 | Resolvido parcialmente | O detalhe de `PaidTask` agora reserva a vaga por 60 minutos antes da candidatura; aceite administrativo e transição completa para assignment ainda dependem do workflow de revisão. |
| FE-FIGMA-017 | Resolvido parcialmente | Frontend agora possui acompanhamento de obrigação, invoice BOLT11, idempotency key, modo `MOCK`, consulta de status e recibo; reconciliação administrativa, pagamento real, estados `AMBIGUOUS` e revisão administrativa visual completa continuam dependentes dos adapters/serviços financeiros. |
| FE-FIGMA-018 | Resolvido parcialmente | O compositor da comunidade agora aceita mídia opcional, valida o upload via `/uploads` e vincula `media_asset_id` ao post; armazenamento binário persistente e renderização completa da mídia no feed continuam pendentes. |
| FE-FIGMA-019 | Resolvido parcialmente | Rota `/app/revisao` consome a fila humana, exige justificativa para correção/rejeição e aprovações exibem a regra de criação da obrigação; autenticação administrativa separada e tela visual dedicada ainda dependem do backend/ADR de administração. |
| FE-FIGMA-020 | Resolvido | Carteira agora exibe o modo da integração (`MOCK` no backend atual), separa score de saldo e mostra transações e trabalhos em andamento quando retornados pelo contrato. |
| FE-FIGMA-021 | Resolvido parcialmente | Anotações da aula agora usam `GET/PUT /courses/:courseId/lessons/:lessonId/notes`, vinculadas à participante e à aula; persistência PostgreSQL ainda é pendência do backend. |
| FE-FIGMA-022 | Resolvido parcialmente | Cadastro possui quatro telas distintas, validação por etapa, retomada local e sincronização com `POST/PATCH/complete /onboarding/drafts`; persistência definitiva e criação da conta autenticada ainda dependem do banco/fluxo de identidade. |
| FE-FIGMA-023 | Resolvido parcialmente | Rotas administrativas de criação/publicação e revisão agora exigem sessão cujo pubkey esteja em `BLUEJET_ADMIN_PUBKEYS`; a interface ainda precisa de uma conta administrativa configurada para validação end-to-end. |
| FE-FIGMA-024 | Resolvido | A candidatura lê `assignmentId` da URL, envia `assignment_id` e o backend valida a associação entre reserva, tarefa e participante. |
| FE-FIGMA-025 | Resolvido parcialmente | O workspace profissional agora carrega o assignment por ID, exibe a tarefa vinculada e trata `403/404`; persistência binária dos anexos continua dependente do storage. |
| FE-FIGMA-026 | Resolvido parcialmente | Entrega profissional agora oferece `Salvar rascunho` via `PUT /assignments/:id/submissions/draft` e envio final separado; recuperação automática do rascunho ainda depende de persistência definitiva. |

## 11. Acessibilidade

> As descrições históricas dos achados nas seções anteriores registram o estado
> no momento da auditoria. A tabela de status pós-correções acima é a fonte
> atual para o que já foi resolvido ou permanece parcial.

Há alguns `aria-label` em avatar e inputs de cadastro, mas faltam labels associados, foco, semântica de tabs, `aria-current`, mensagens anunciadas e estados de erro. Imagens decorativas têm `alt=""`, o que é correto para os ícones decorativos atuais; imagens informativas de cards ainda não existem. Botões são elementos `button`, não `div`, mas navegação/estado ativo não são comunicados a tecnologias assistivas.

## 11. Performance

O bundle frontend construído foi 202,76 kB (63,49 kB gzip), sem sinal de problema de bundle nesta amostra. Problemas observados: fonte externa via `@import` pode bloquear/variar a renderização; assets do MCP não têm controle de cache/expiração; imagens de domínio externo não têm dimensões/fallback; chamadas de lista não têm paginação/cancelamento. Não há evidência suficiente para recomendar virtualização ou otimizações mais amplas.

## 12. Testes executados

| Comando | Resultado | Tempo aproximado |
|---|---|---:|
| `npm run build` em `apps/web` | PASSOU: `tsc -b` + Vite, 16 módulos, 202,76 kB JS gzip 63,49 kB | 0,17 s |
| `npm run build` na raiz | FALHOU: `sh: docusaurus: command not found` | 0,03 s |
| formatter/lint/typecheck/test frontend | NÃO CONFIGURADOS como scripts/arquivos no frontend | — |
| E2E/browser | NÃO EXECUTADO: nenhuma ferramenta de browser disponível nesta execução | — |
| `git status --short` | Alterações locais preexistentes preservadas; somente este relatório foi criado nesta execução | — |

Não afirmo cobertura de rotas, refresh, upload ou responsividade porque não existem testes frontend configurados e não foram inventados resultados.

## 13. Plano de correção

### Lote 1 — bloqueadores e rotas

- **Arquivos:** `apps/web/src/main.tsx`, `vite.config.ts`, configuração de deploy.
- **Dependências:** definir contratos de sessão, Course/Module/Lesson/Activity e estratégia SPA fallback.
- **Risco:** alto; altera navegação central.
- **Estimativa:** grande.
- **Conclusão:** cadastro e aula/atividade completam o fluxo; refresh de toda rota profunda funciona; 401/403/404 são distintos.

### Lote 2 — continuidade dos dados

- **Arquivos:** `main.tsx`, módulos de API a criar somente seguindo convenções existentes.
- **Dependências:** contratos OpenAPI/Flask para opportunity, application, assignment, submission e wallet.
- **Risco:** alto; envolve autenticação e submissão.
- **Estimativa:** grande.
- **Conclusão:** card → detalhe → candidatura → assignment → submission mantém IDs e dados; draft/upload são estados idempotentes.

### Lote 3 — layouts e responsividade

- **Arquivos:** `styles.css`, `app.css`, componentes extraídos de `main.tsx`.
- **Dependências:** Lotes 1–2.
- **Risco:** médio.
- **Estimativa:** grande.
- **Conclusão:** comparar screenshots em 1280, 1024, 768 e 390 px; sem overflow e com CTAs acessíveis.

### Lote 4 — design system

- **Arquivos:** tokens CSS e componentes compartilhados em `src/`.
- **Dependências:** padrões estabilizados no lote 3.
- **Risco:** médio.
- **Estimativa:** médio.
- **Conclusão:** cores/spacing/raios centralizados e cards/inputs/estados sem cópias divergentes; assets deixam de depender do MCP.

### Lote 5 — acessibilidade

- **Arquivos:** componentes de formulário, navegação, modal/upload e estilos de foco.
- **Dependências:** componentes dos lotes 2–4.
- **Risco:** médio.
- **Estimativa:** médio.
- **Conclusão:** teclado, foco visível, labels, headings, tabs, erros e uploads validados em leitor de tela/axe.

### Lote 6 — refinamento visual

- **Arquivos:** CSS, assets controlados e componentes visuais.
- **Dependências:** todos os lotes anteriores.
- **Risco:** baixo.
- **Estimativa:** médio.
- **Conclusão:** screenshots comparativas evidenciam alinhamento, tipografia, cores, cards, imagens, estados ativos e densidade com os nodes Figma consolidados.
