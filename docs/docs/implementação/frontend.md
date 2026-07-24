---
sidebar_position: 3
sidebar_label: Frontend
---

# Frontend

## Visão geral

O cliente é uma SPA responsiva construída com React, TypeScript e Vite. Ele
cobre landing page, autenticação, cadastro, comunidade, oportunidades,
capacitação, trabalho, revisão, pagamentos, recibos e carteira.

Não há biblioteca de roteamento. A aplicação usa `history.pushState`,
`popstate` e uma função central que interpreta o caminho atual. Essa solução
reduziu dependências no MVP, mas concentra rotas e telas em `src/main.tsx`.

## Stack e organização

| Elemento | Implementação |
|---|---|
| UI | React e `lucide-react` |
| Linguagem | TypeScript |
| Build | Vite e `tsc -b` |
| Estilos | CSS próprio, tokens e overrides responsivos |
| Navegação | History API do navegador |
| Sessão | Cookie `HttpOnly` enviado com `credentials: include` |
| Estado local | estado React e `localStorage` para rascunhos |
| Deploy estático | `_redirects` preserva deep links da SPA |

O endereço da API vem de `VITE_API_URL` e usa
`http://localhost:5000` quando a variável não é informada.

## Mapa de rotas

| Rota | Tela |
|---|---|
| `/` | landing pública |
| `/entrar` | autenticação Nostr |
| `/cadastro/*` | acesso, identificação, habilidades e verificação |
| `/app/comunidade` | feed e publicação |
| `/app/oportunidades` | lista de oportunidades |
| `/app/oportunidades/:id` | detalhe, reserva e candidatura |
| `/app/oportunidades/nova/*` | criação administrativa em etapas |
| `/app/capacitacao` | catálogo de cursos |
| `/app/capacitacao/:id` | curso, aula, atividade e quiz |
| `/app/trabalhos/:id` | execução e entrega do trabalho |
| `/app/revisao` | fila administrativa de revisão |
| `/app/pagamentos/:assignmentId` | criação e acompanhamento do pagamento |
| `/app/recibos/:id` | comprovante |
| `/app/carteira` | resumo demonstrativo da carteira |

## Sessão e autenticação

O `SessionGate` consulta `/me` antes de renderizar áreas protegidas. Resposta
`401` redireciona para o login; `403` apresenta acesso proibido.

No login, o navegador:

1. verifica se `window.nostr` está disponível;
2. solicita a pubkey à extensão;
3. obtém um desafio da API;
4. pede à extensão a assinatura de um evento de kind `22242`;
5. envia o evento assinado e recebe o cookie de sessão.

A chave privada permanece na extensão. A proteção completa depende da
verificação criptográfica no backend, ainda pendente.

## Estado e dados locais

O cliente mantém dois rascunhos no `localStorage`:

- `bluejet_registration`: etapas do cadastro;
- `bluejet_opportunity_draft`: criação de oportunidade.

O cadastro atual também guarda senha e confirmação de senha localmente, embora
a autenticação principal seja Nostr e o backend descarte esses campos. Esse dado
deve ser removido do fluxo e apagado para instalações existentes antes de
qualquer uso público.

As chamadas HTTP distinguem carregamento, erro e estado vazio. Falhas da API não
são convertidas silenciosamente em listas vazias, preservando a visibilidade do
problema.

## Interface e acessibilidade

A implementação utiliza tokens próprios de cor, tipografia e espaçamento,
derivados dos frames de referência do Figma. Há ajustes para telas pequenas,
contenção de overflow e navegação mobile.

Formulários possuem rótulos e mensagens com `role="alert"` em fluxos principais.
Ainda falta uma auditoria formal de WCAG, navegação completa por teclado,
contraste, foco e leitores de tela.

## Execução

```powershell
Set-Location apps/web
npm ci
$env:VITE_API_URL = "http://localhost:5000"
npm run dev
```

Build de produção:

```powershell
npm run build
npm run preview
```

O README menciona um proxy `/api`, mas `vite.config.ts` contém apenas o plugin
React. A execução local deve usar `VITE_API_URL` até que o proxy seja
configurado.

## Pendências conhecidas

- dividir `main.tsx` em rotas, páginas, hooks e clientes por domínio;
- adicionar um roteador ou formalizar e testar o roteamento próprio;
- remover senha e outros dados desnecessários do `localStorage`;
- persistir apenas rascunhos não sensíveis e aplicar expiração;
- adicionar testes unitários, de componente e ponta a ponta;
- validar arquivos pelo conteúdo e enviar os bytes para armazenamento privado;
- apresentar os modos `MOCK`, `SANDBOX` e `REAL` em toda tela financeira;
- concluir estados de reconciliação, inclusive `AMBIGUOUS`;
- alinhar a rota de entrega especificada com a rota implementada;
- executar auditoria de acessibilidade e desempenho.
