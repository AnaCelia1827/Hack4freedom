# [Nome do Projeto]

> **Hack4Freedom Brasil 2026** 
> Transformando a infraestrutura da Lightning Network em renda imediata e capacitação para mulheres brasileiras, sem perda de capital para o doador.

## 1. O Problema

Mulheres em situação de vulnerabilidade econômica precisam de **renda imediata**. A capacitação tradicional exige um tempo que elas não possuem, pois a prioridade é a subsistência diária. 

Por outro lado, ONGs e fundos de impacto dependem de doações a fundo perdido (dinheiro que é gasto e não volta). Esse modelo cria um gargalo financeiro constante, limitando a escala da ajuda e afastando potenciais patrocinadores que não podem abrir mão de seu capital principal.

## 2. A Solução: Lossless Donation + Learn-to-Earn

Criamos uma plataforma que resolve os dois lados do problema através de uma economia circular financiada pela própria infraestrutura do Bitcoin.

* **Para o Patrocinador (Lossless Donation):** Empresas e anjos depositam capital que é convertido em liquidez para a Lightning Network. **O principal nunca é gasto.**
* **Para a Usuária (Learn-to-Earn):** Mulheres acessam trilhas curtas de capacitação e destravam *microtasks* remuneradas. O pagamento pelo trabalho delas é financiado 100% pelo rendimento gerado pelo capital do patrocinador.

## 3. O Motor Econômico: Lightning Service Provider (LSP)

O projeto se diferencia por atuar como uma peça ativa da rede Bitcoin. O capital depositado via Pix pelos patrocinadores é utilizado para abrir canais de pagamento, transformando a plataforma em um nó de roteamento (LSP).

Sempre que a rede global utiliza nossos canais para transacionar, arrecadamos microtaxas (*routing fees*), calculadas pela fórmula padrão da rede:

$$TotalFee = BaseFee + \left( Amount \times \frac{FeeRate}{1.000.000} \right)$$

O acúmulo contínuo dessas taxas forma a **Pool de Recompensas**. É esse lucro nativo do protocolo que financia as mulheres da plataforma, criando um sistema de impacto social financeiramente autossustentável.

## 4. Stack Tecnológico e Arquitetura

Nossa arquitetura conecta o sistema financeiro tradicional (TradFi) à fronteira do dinheiro descentralizado.

* **Nostr (Identidade e Comunidade):**
  * Substitui bancos de dados fechados. As usuárias criam perfis descentralizados.
  * O histórico de capacitação e execução de microtasks gera uma reputação inconfundível (Verifiable Credentials) que pertence à mulher, não à plataforma.
* **Breez SDK (Motor de Pagamentos):**
  * Responsável por gerenciar o envio instantâneo dos satoshis da nossa Pool de Recompensas diretamente para a carteira *non-custodial* da usuária final.
* **API Hodle (On-Ramp / Off-Ramp via Pix):**
  * Resolve o atrito do mundo físico. Permite que patrocinadores depositem grandes volumes em Reais (BRL) e que as mulheres saquem seus satoshis ganhos instantaneamente via Pix para pagar despesas básicas.
* **Backend (Python/Flask + SQLite):**
  * Gerencia as regras de negócio, a validação das etapas de capacitação e a simulação da distribuição do *yield* (rendimento) da rede para as microtasks ativas.

## 5. Jornada do Usuário (Fluxo Principal)

1. **Aporte de Liquidez:** Um fundo ESG deposita R$ 50.000 via Pix. O dinheiro provê liquidez para a rede e começa a gerar satoshis contínuos em taxas de roteamento.
2. **Capacitação Educacional:** A usuária entra via Nostr, acessa a comunidade e conclui um módulo de educação financeira ou tecnológica.
3. **Destravamento de Valor:** A conclusão do módulo atesta sua aptidão e ela ganha acesso a uma *microtask* (ex: teste de QA, anotação de dados, curadoria).
4. **Liquidação Instantânea:** Ao concluir a tarefa, o backend libera os satoshis acumulados na Pool de Recompensas via Lightning Network.
5. **Saque:** A mulher recebe na hora, com autocustódia, e pode converter para Pix via Hodle em segundos, comprando o alimento do dia.

## 6. Escopo do MVP (Demo Day)

Para comprovar a viabilidade técnica e de negócios no curto prazo do hackathon, o MVP entregue foca no *Happy Path* da geração de renda:

- [x] Interface da comunidade e login.
- [x] Backend simulando a separação entre o capital "Principal" do patrocinador e o "Rendimento" gerado.
- [x] Validador simples de *microtask* vinculada a uma trilha de conhecimento.
- [x] Integração real de pagamento: Disparo de satoshis (Lightning) assim que a tarefa é aprovada.

## 7. Diferenciais Competitivos (Por que importa)

* **Impacto Imediato:** Foco em colocar renda no bolso de quem tem pressa.
* **Uso Real do Bitcoin:** O Bitcoin não é apenas especulação; aqui ele atua como infraestrutura de roteamento e trilho de micropagamentos (inviável no Pix).
* **Escalabilidade:** O modelo não depende de doações de caridade exaustivas, mas sim da própria demanda orgânica de roteamento da Lightning Network.

---
*Construído com propósito para o Hack4Freedom Brasil 2026.*