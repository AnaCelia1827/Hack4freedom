---
sidebar_label: Repositório e Links
---

# Repositório e Links

- **Repositório:** [AnaCelia1827/Hack4freedom](https://github.com/AnaCelia1827/Hack4freedom)
- **Documentação publicada:** [anacelia1827.github.io/Hack4freedom](https://anacelia1827.github.io/Hack4freedom/)
- **Demonstração:** a publicar

## Executar a documentação localmente

Requisito: Node.js 20 ou superior.

```bash
npm install
npm run docs:start
```

A documentação ficará disponível em `http://localhost:3000/Hack4freedom/`.

## Validar a versão de produção

```bash
npm run docs:build
npm run docs:serve
```

O build estático é gerado em `build/`. O workflow `deploy-docs.yml` publica o site no GitHub Pages após um push na branch `main`, desde que **Settings → Pages → Source** esteja configurado como **GitHub Actions**.
