# Documentação Hack4Freedom

Site de documentação em Docusaurus, organizado a partir dos documentos Markdown do projeto.

## Desenvolvimento local

Requisitos: Node.js 20 ou superior.

```bash
npm install
npm run docs:start
```

O servidor local abre a documentação em `http://localhost:3000/Hack4freedom/`.

## Validação de produção

```bash
npm run docs:build
npm run docs:serve
```

O build estático é gerado em `build/`.

## Publicação

O workflow `deploy-docs.yml` publica automaticamente no GitHub Pages quando houver um push na branch `main`. No GitHub, configure **Settings → Pages → Source** como **GitHub Actions**.

Endereço esperado: `https://anacelia1827.github.io/Hack4freedom/`.

## Estrutura

- `contexto.md`: visão geral;
- `docs/`: conteúdo da documentação;
- `sidebars.js`: ordem e categorias do menu lateral;
- `docusaurus.config.js`: domínio, navegação, rodapé e tema;
- `src/css/custom.css`: identidade visual;
- `static/img/`: logo, favicon e cartão social.
