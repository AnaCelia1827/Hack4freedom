# Cliente web Bluejet

SPA React/Vite da aplicação. O cliente implementa as rotas públicas, cadastro,
shell autenticado, capacitação, oportunidades, trabalho, pagamento, carteira e
comunidade descritos em `docs/phase-9-routes-and-backend.md`.

```bash
npm ci
npm run dev
npm run build
```

O proxy local encaminha `/api` para `http://localhost:5000`. Em deploy estático,
`public/_redirects` preserva deep links da SPA. O projeto usa CSS próprio e não
introduz Tailwind.
