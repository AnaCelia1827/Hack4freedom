# ADR-001 — Reservas de tarefa e de atribuição

- Status: aprovado
- Data: 2026-07-22

## Contexto

Os requisitos anteriores usavam `Reservation` tanto para a exclusividade temporária da participante quanto para os fundos reservados antes da publicação da tarefa. Também havia conflito entre duração de um dia, duração de 60 minutos e devolução automática dos recursos.

## Decisão

O domínio possui duas entidades distintas:

- `AssignmentReservation`: exclusividade temporária da única vaga da `PaidTask` para uma participante;
- `TaskFundingReservation`: fundos previamente separados para garantir o pagamento da tarefa.

No MVP:

1. a `AssignmentReservation` expira em 60 minutos;
2. a expiração muda a atribuição para `EXPIRED` e libera a vaga;
3. a `TaskFundingReservation` permanece vinculada à tarefa;
4. outra participante elegível pode reservar a tarefa;
5. devolução ou realocação financeira exige operação contábil explícita e lançamento compensatório;
6. expiração nunca modifica silenciosamente o ledger.

Esta decisão prevalece sobre as referências anteriores a um dia ou à devolução automática dos recursos.

## Consequências

- O worker de expiração altera somente a atribuição e sua reserva de vaga.
- O funding só é alterado por serviço financeiro autorizado.
- API, banco, frontend, testes e observabilidade devem usar os dois nomes canônicos.
- O teste de expiração precisa provar que a vaga é liberada e o funding permanece reservado.

