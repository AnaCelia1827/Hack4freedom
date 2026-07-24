---
sidebar_position: 5
sidebar_label: Segurança e privacidade
---

# Segurança e privacidade

## Escopo da análise

Esta avaliação considera o código da branch `bluejet-development` no commit
`9d08c4c`. Ela registra controles existentes e lacunas observáveis; não equivale
a pentest nem autoriza o uso de dinheiro real.

Os ativos mais sensíveis são:

- identidade Nostr e sessões;
- situação de vulnerabilidade e dados de cadastro;
- entregas privadas e evidências profissionais;
- decisões de revisão;
- obrigações, reservas, ledger e recibos;
- credenciais de banco, relays e provedores de pagamento.

## Controles já implementados

| Área | Controle |
|---|---|
| Login | desafio aleatório, expiração e proteção contra replay |
| Chaves | backend não solicita nem armazena `nsec` |
| Sessão | cookie `HttpOnly`, `SameSite=Lax` e `Secure` em produção |
| Administração | allowlist de pubkeys e bloqueio padrão quando vazia |
| Tarefas | funding integral antes da publicação e reserva exclusiva |
| Entregas | verificação de propriedade nas rotas principais |
| Pagamentos | chave idempotente, lock de obrigação e uma tentativa ativa |
| Banco | constraints, transações, ledger append-only e outbox atômico |
| Privilégios | usuário de runtime sem ownership, DDL, delete ou truncate |
| Operação | health checks e modos `MOCK`, `SANDBOX` e `REAL` |

Esses controles são uma boa base de domínio, mas parte deles cobre apenas o
caminho financeiro persistido.

## Achados prioritários

### P0 — bloqueiam piloto público ou dinheiro real

| Achado | Impacto | Correção necessária |
|---|---|---|
| Assinatura Nostr não é verificada criptograficamente | falsificação de identidade e sessão | validar ID e assinatura do evento com biblioteca auditada |
| Rotas financeiras sem autenticação ou ownership completo | consulta ou criação indevida de pagamentos | aplicar sessão, papel e propriedade em toda obrigação, tentativa e recibo |
| Reconciliação administrativa sem `require_admin` | liquidação indevida no modo em memória | proteger rota e registrar decisão auditável |
| Oportunidade administrativa sem `require_admin` | publicação não autorizada | exigir papel administrativo |
| Senha guardada no `localStorage` | exposição por XSS, extensão ou dispositivo compartilhado | remover os campos e limpar dados existentes |
| Ausência de gateway e reconciliação persistente | pagamento duplicado, perdido ou inconclusivo | implementar worker, estado `AMBIGUOUS` e consulta ao provedor |

Rotas que exigem revisão imediata incluem:
`POST /admin/opportunities`,
`POST /admin/payout-attempts/:id/reconcile`,
`GET /assignments/:id/payment-obligation`,
`POST /payment-obligations/:id/payout-attempts`,
`GET /payment-obligations/:id/payout-status` e
`GET /receipts/:id`.

### P1 — antes de dados pessoais reais

- persistir sessões com revogação, rotação e expiração no servidor;
- adicionar proteção CSRF aos comandos autenticados por cookie;
- ligar a allowlist CORS e rejeitar origens não configuradas;
- validar todos os payloads, limites, tipos e identificadores;
- usar armazenamento de objetos privado com URLs temporárias;
- inspecionar MIME pelo conteúdo e executar análise antimalware;
- criptografar tráfego e armazenamento, com gestão e rotação de secrets;
- aplicar limitação de requisições ao login, uploads e publicação;
- criar trilha de auditoria para acesso administrativo e financeiro;
- definir retenção, exclusão e atendimento aos direitos da titular.

### P2 — endurecimento e operação

- cabeçalhos CSP, HSTS, `X-Content-Type-Options` e política de referência;
- observabilidade sem registrar invoice completa, token ou dado pessoal;
- varredura de dependências, SAST e detecção de secrets no CI;
- testes automatizados de autorização por matriz de papéis;
- alertas para outbox parada, locks, tentativas ambíguas e divergência de saldo;
- plano de backup, restauração e continuidade testado.

## Modelo de autorização

A política deve ser negada por padrão e combinar papel com propriedade:

| Recurso | Participante | Revisor/admin |
|---|---|---|
| Perfil e onboarding | somente o próprio | acesso mínimo e justificado |
| Reserva e entrega | somente a própria atribuição | leitura para revisão |
| Review queue | sem acesso | autorizado |
| Obrigação e tentativa | somente a própria | conciliação autorizada |
| Recibo | somente titular | suporte auditado |
| Funding e publicação | leitura pública limitada | escrita autorizada |

Não basta haver uma sessão válida: cada rota deve confirmar que a pubkey da
sessão possui relação com o recurso solicitado.

## Privacidade desde a concepção

A plataforma atende pessoas em situação potencialmente vulnerável. Portanto, a
coleta deve ser mínima e o risco de exposição deve prevalecer sobre conveniência
analítica.

Diretrizes:

- não publicar vulnerabilidade, localização, contatos ou entregas em Nostr;
- separar identidade pública de cadastro privado;
- tornar badge público opcional, específico e revogável no sistema;
- explicar que eventos já enviados a relays podem ser difíceis de remover;
- não usar produção como ambiente de demonstração;
- agregar indicadores de impacto para evitar reidentificação;
- estabelecer finalidade, base legal, retenção e responsáveis conforme a LGPD.

Referência: [Lei nº 13.709/2018 — LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm).

## Segurança financeira

Toda transição monetária deve preservar quatro propriedades:

1. **unicidade:** uma obrigação não pode liquidar duas vezes;
2. **rastreabilidade:** tentativa, evento externo, ledger e recibo têm
   referências correlacionáveis;
3. **recuperação:** timeout produz estado conciliável, não retry cego;
4. **segregação:** migração, aplicação, worker e operação humana usam
   credenciais e permissões distintas.

O ledger implementado já rejeita desequilíbrio e mutação posterior. Ainda falta
ligá-lo a todas as transições financeiras e reconciliá-lo contra a fonte externa
de pagamento.

## Validação antes de lançamento

Checklist mínimo:

- [ ] corrigir todos os achados P0;
- [ ] executar testes de autenticação, autorização e concorrência;
- [ ] provar recuperação após reinício durante um pagamento;
- [ ] executar pentest focado em sessão, IDOR, upload e administração;
- [ ] revisar dependências e eliminar secrets do histórico;
- [ ] validar backup e restauração do PostgreSQL;
- [ ] testar limites de tesouraria e procedimento de emergência;
- [ ] publicar aviso de privacidade e termos de consentimento;
- [ ] documentar responsável por incidentes e canal de comunicação;
- [ ] manter o modo financeiro visível em todas as evidências e telas.

Somente após a aprovação desse checklist o modo `REAL` deve ficar disponível por
configuração separada e com liberação operacional explícita.
