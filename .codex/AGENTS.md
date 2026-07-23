# Bluejet Engineering Invariants

- Nenhuma tarefa não financiada pode ser publicada.
- Nenhuma aprovação pode deixar de criar uma obrigação financeira.
- Nenhuma obrigação pode ser paga mais de uma vez.
- Nunca usar float para valores financeiros.
- Nunca publicar dados privados ou financeiros no Nostr.
- Nunca armazenar nsec, seed, mnemonic ou rune no código ou logs.
- Toda integração externa fica atrás de uma interface.
- Todo modo MOCK ou SANDBOX deve aparecer na interface.
- Todo PR deve citar RF, RN e CA.
- Não introduzir requisito que não esteja documentado.