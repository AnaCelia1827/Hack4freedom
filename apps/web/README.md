# Cliente web Bluejet

SPA React/Vite da aplicação. O cliente implementa as rotas públicas, cadastro,
shell autenticado, capacitação, oportunidades, trabalho, pagamento, carteira e
comunidade descritos em `docs/phase-9-routes-and-backend.md`.

```bash
npm ci
npm run dev
npm run build
```

O proxy local encaminha `/api` para `http://127.0.0.1:5000` e remove o prefixo
antes de chamar o Flask. `VITE_API_URL` pode substituir `/api` quando o ambiente
de deploy exigir outra base.

Em deploy estático, `public/_redirects` preserva deep links da SPA. O comando de
build verifica se esse fallback foi copiado para o artefato `dist`. O projeto usa
CSS próprio e não introduz Tailwind.
