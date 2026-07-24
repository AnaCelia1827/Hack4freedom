# Hack4Freedom

> Projeto desenvolvido durante o **Hack4Freedom São Paulo 2026**.

## Visão Geral

O Hack4Freedom conecta microcapacitação, trabalho digital e renda imediata para mulheres em situação de vulnerabilidade econômica. A plataforma permite que uma participante aprenda uma competência em uma trilha curta, execute uma microtarefa real e receba pelo trabalho aprovado em satoshis.

O projeto combina pagamentos pela Lightning Network, carteira integrada e autocustodial com Breez e identidade e reputação portáteis no Nostr. A experiência abstrai a complexidade técnica: a participante não precisa compreender canais, roteamento ou invoices para concluir uma tarefa e receber.

## Problema

Mulheres em situação de vulnerabilidade econômica muitas vezes precisam escolher entre dedicar tempo à capacitação e gerar renda para necessidades imediatas. Programas tradicionais podem exigir semanas ou meses de estudo antes de oferecer uma oportunidade remunerada.

Ao mesmo tempo:

- empresas e organizações possuem pequenas tarefas digitais verificáveis, mas nem sempre têm um processo acessível para capacitar, contratar e remunerar novos talentos;
- ONGs e fundos de impacto precisam acompanhar resultados e demonstrar como os recursos geram renda e desenvolvimento;
- acesso formal a uma conta bancária não garante controle privado e contínuo sobre o próprio dinheiro;
- qualificações obtidas em uma plataforma centralizada nem sempre são portáteis ou verificáveis.

## Solução

A plataforma reúne aprendizagem, trabalho e pagamento em um único fluxo:

1. A participante entra com sua identidade Nostr.
2. Conclui uma trilha curta de capacitação.
3. Recebe um badge de competência assinado no Nostr.
4. Desbloqueia e executa uma microtarefa financiada por uma empresa, organização ou patrocinador.
5. Após a aprovação da entrega, recebe o pagamento pela Lightning Network em uma carteira integrada com Breez.
6. Pode manter os satoshis ou, quando o fluxo estiver disponível, solicitar a conversão para Pix com as taxas apresentadas antes da confirmação.

O pagamento de uma tarefa pode combinar o valor-base pago por quem recebe a entrega, matching de impacto oferecido por patrocinadores e um bônus proveniente de receita líquida já realizada pela infraestrutura Lightning. Essas fontes são contabilizadas separadamente, e o valor-base prometido à participante não depende de receitas futuras de roteamento.

## Stack de Tecnologia

| Camada | Tecnologia | Uso no projeto |
| --- | --- | --- |
| Interface | React, Vite e PWA | Aplicação web instalável e otimizada para celular |
| Documentação | Docusaurus | Site de documentação do projeto |
| Backend | Python e Flask | APIs, regras de negócio, tarefas, aprovações e pagamentos |
| Dados | SQLite | Conteúdo, progresso, tarefas e registros privados do MVP |
| Identidade e reputação | Nostr, NIP-07 e NIP-58 | Login por assinatura e badges verificáveis |
| Pagamentos | Bitcoin e Lightning Network | Micropagamentos instantâneos em satoshis |
| Carteira | Breez SDK — Spark | Recebimento e controle dos satoshis pela participante |
| Infraestrutura Lightning | Core Lightning e CLNRest | Nó, canais, liquidez e métricas para patrocinadores |
| Conversão | Hodle | Ponte opcional entre Bitcoin e Pix |

Dados pessoais, entregas privadas e informações antifraude permanecem no backend protegido e não são publicados no Nostr por padrão. As chaves privadas da participante também não são enviadas ao backend.

## Equipe

Os nomes, papéis e contatos da equipe ainda serão adicionados.

| Integrante | Papel | Contato |
| --- | --- | --- |
| A definir | A definir | A definir |

## Repositório e Links

- **Repositório:** [AnaCelia1827/Hack4freedom](https://github.com/AnaCelia1827/Hack4freedom)
- **Documentação:** [anacelia1827.github.io/Hack4freedom](https://anacelia1827.github.io/Hack4freedom/)
- **Demo:** a publicar

### Executar a documentação localmente

Requisito: Node.js 20 ou superior.

```bash
npm install
npm run docs:start
```

A documentação ficará disponível em `http://localhost:3000/Hack4freedom/`.

Para validar a versão de produção:

```bash
npm run docs:build
npm run docs:serve
```

O build estático é gerado em `build/`. O workflow `deploy-docs.yml` publica o site no GitHub Pages após um push na branch `main`, desde que **Settings → Pages → Source** esteja configurado como **GitHub Actions**.

## Status

**Em desenvolvimento — fase de definição e implementação do MVP para o Demo Day de 25 de julho de 2026.**

O MVP pretende demonstrar o fluxo completo, do login com Nostr ao primeiro pagamento Lightning real. A documentação de problema, regras de negócio, fluxos, requisitos e arquitetura financeira já está em elaboração. As integrações funcionais e a demonstração ponta a ponta ainda precisam ser concluídas e validadas.

Critérios de sucesso do MVP:

- uma participante conclui o fluxo sem precisar entender a infraestrutura de Bitcoin;
- a tarefa executada produz valor verificável;
- a origem dos recursos do pagamento fica clara;
- o pagamento chega a uma carteira Breez;
- o badge fica associado à identidade Nostr da participante;
- capital, receita e impacto aparecem contabilizados separadamente.

## Próximos Passos

- definir o nome final e a identidade visual do projeto;
- preencher os nomes, papéis e contatos da equipe;
- implementar o login Nostr sem exposição da chave privada;
- desenvolver a trilha curta, o marketplace e o fluxo de aprovação de tarefas;
- emitir e verificar badges NIP-58;
- integrar a carteira Breez e realizar um pagamento Lightning real;
- implementar o painel de transparência para patrocinadores;
- validar privacidade, segurança e usabilidade com o público-alvo;
- publicar o link da demonstração;
- executar e ensaiar o fluxo completo para o Demo Day.
