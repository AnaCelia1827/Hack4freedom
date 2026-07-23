# Fase 9 — Rotas e integração frontend/backend

## Arquitetura encontrada

- Frontend: React, Vite e TypeScript em `apps/web`; não havia roteador instalado.
- Backend: Flask modular em `apps/api/bluejet_api`; autenticação por cookie de sessão.
- Persistência: fronteira Alembic/PostgreSQL criada, mas os serviços atuais ainda usam armazenamento em memória.
- Upload: endpoint de metadados privado em `/uploads`; armazenamento persistente ainda pendente.
- Testes: pytest no backend; build Vite no frontend.

## Rotas consolidadas

```text
/                             landing
/entrar                       login Nostr
/cadastro/acesso              onboarding inicial
/cadastro/identificacao       onboarding
/cadastro/habilidades         onboarding
/cadastro/verificacao         onboarding
/app/comunidade               feed
/app/oportunidades             lista com query params
/app/oportunidades/:id         detalhe
/app/capacitacao               catálogo
/app/capacitacao/:id           curso
/app/capacitacao/:id/aulas/:lessonId
/app/capacitacao/:id/atividades/:activityId
/app/carteira                 carteira
/app/trabalhos/:id             assignment
/app/trabalhos/:id/entrega     submissão profissional
/app/oportunidades/nova/*      wizard persistente de publicação
```

O roteamento preserva query parameters no histórico e usa `history.pushState`
para evitar introduzir uma biblioteca de rotas paralela.

## Layouts

- Marketing: landing pública.
- Auth: login e cadastro.
- AppShell: comunidade, oportunidades, capacitação e carteira.
- Transactional: base preparada para trabalhos e wizards.

## Integrações reutilizadas

O cliente chama `/auth/nostr/challenges`, `/auth/nostr/sessions`, `/courses`,
`/paid-tasks`, `/community/feed`, `/community/posts`, `/uploads` e os contratos
de submissão, carteira e drafts de oportunidade. Erros são mantidos como erro,
sem convertê-los silenciosamente em entidades vazias.

## Estado atual e pendências reais

- Os serviços Flask são in-memory e precisam ser ligados às migrações antes de produção.
- O login usa NIP-07 e sessão por cookie; a verificação criptográfica completa
  continua delegada ao adapter Nostr.
- Assignment, candidatura, mídia persistente, carteira derivada do ledger e
  persistência PostgreSQL ainda precisam substituir os serviços in-memory.
- A comparação visual por screenshot do app não foi executada porque o workspace
  não possui Playwright/Chromium configurado; o plugin Figma foi usado como fonte
  estrutural primária e o build foi validado.

## Registro de execução visual — foundations e AppShell

- Frames consultados pelo plugin: `66:2337`, `51:1739`, `101:9` e `51:1072`.
- Tokens adicionados em `apps/web/src/tokens.css`, usando os valores observados
  no Figma (`#000`, `#121212`, `#1A1A1A`, `#5C3F46`, `#FF007F`, `#FFB1C4`,
  `#C3F400` e `#E5BCC5`).
- O header mobile recebeu contenção de overflow para preservar marca e CTA.
- Screenshot de validação gerado em `/tmp/bluejet-landing.png` e
  `/tmp/bluejet-mobile-v2.png`.
- Divergência corrigida: o card visual da landing não exibe mais `0.05 BTC`
  como earnings; agora informa `Capital de liquidez — MOCK`, conforme as regras
  financeiras do produto.
- Build executado após a fatia: `cd apps/web && npm run build` — aprovado.
- Os assets do Figma são usados apenas como referência de implementação; URLs temporárias não são persistidas.
