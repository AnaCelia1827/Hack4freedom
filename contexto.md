# Contexto do Projeto e Arquitetura de Negócios

Este documento define a visão do produto, a arquitetura financeira e as regras de negócio do nosso projeto para o **Hack4Freedom Brasil (Julho de 2026 - São Paulo)**.

## 1. O Cenário (Hack4Freedom)
Estamos construindo no cruzamento entre **impacto social no Brasil** e a **fronteira do dinheiro descentralizado**. O foco do hackathon é utilizar Freedom Tech (Bitcoin, Lightning Network, Nostr) para criar soluções de liberdade financeira, fugindo do modelo tradicional de caridade para modelos de autossustentabilidade.

## 2. A Dor (O Problema Duplo)
1. **O lado da Usuária:** Mulheres em situação de vulnerabilidade que desejam se inserir no mercado de trabalho e financeiro não têm o "luxo" do tempo. Elas não podem passar 6 meses estudando sem remuneração, pois precisam de renda para a subsistência diária ("comida na mesa hoje").
2. **O lado do Patrocinador:** ONGs, fundos ESG e empresas de impacto dependem de "doações a fundo perdido" (lossy donations). O capital doado é gasto e não retorna, o que limita o volume de investimento e torna o modelo dependente de captação contínua.

## 3. A Solução: Learn-to-Earn financiado por Infraestrutura (LSP)
Nossa solução é uma plataforma de capacitação e microtrabalho que se retroalimenta financeiramente, operando em duas frentes:

*   **O Motor Econômico (Lossless Donation via LSP):** 
    Empresas e anjos depositam capital (via Pix). Esse principal **nunca é gasto**. Ele é convertido em Bitcoin e alocado em canais da Lightning Network, tornando a plataforma um Nó de Roteamento (Lightning Service Provider - LSP). Toda vez que pagamentos globais passam pelos nossos canais, arrecadamos microtaxas (*routing fees*). Esse rendimento contínuo e infinito é o que forma nossa **Pool de Recompensas**.
*   **O Funil de Transformação (Capacitação + Microtasks):**
    As mulheres acessam trilhas de conhecimento e, ao concluí-las, destravam microtarefas digitais. Ao completarem o trabalho, recebem instantaneamente os satoshis (gerados pelo lucro do nó LSP) diretamente em suas carteiras, podendo sacar para Pix imediatamente. 

## 4. Arquitetura Tecnológica e Stack do MVP
Para conectar o mundo tradicional (TradFi) à descentralização, utilizamos o seguinte ecossistema:

*   **Hodle API (On-ramp / Off-ramp):** A ponte com a realidade brasileira. Permite que o Fundo/Patrocinador deposite grandes volumes em BRL (Pix) para prover liquidez, e permite que a mulher saque seus satoshis ganhos instantaneamente para sua conta bancária via Pix.
*   **Nostr (Identidade e Comunidade):** Em vez de um banco de dados centralizado e frágil, usamos o protocolo Nostr. As usuárias são donas de seus perfis e conexões. Suas conquistas geram *Verifiable Credentials*, formando um currículo imutável que pertence a elas.
*   **Breez SDK (Motor de Pagamentos):** Gerencia o envio *non-custodial* e instantâneo dos satoshis da nossa Pool de Recompensas diretamente para a carteira da usuária final no momento em que a tarefa é aprovada.
*   **Backend (Python/Flask + SQLite):** O cérebro do MVP. Gerencia a simulação matemática do *yield* (taxas de roteamento geradas), a validação das microtasks e o acionamento dos webhooks de pagamento.

## 5. Objetivo para o Demo Day (25 de Julho de 2026)
O escopo de entrega para a banca avaliadora foca no **Happy Path** da geração de renda:
1. Simulação visual do painel do patrocinador (Fundo bloqueado x Rendimento gerado).
2. Interface da usuária (Comunidade, Trilha de Capacitação e Microtask disponível).
3. **Mágica ao vivo:** A usuária (nossa equipe apresentando) conclui a microtask, o backend aprova, e os juízes veem o disparo instantâneo via Lightning Network caindo na carteira no celular.