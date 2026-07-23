# Runs

Runs são registros append-only de execuções. Uma falha permanece no histórico;
uma execução posterior referencia a anterior, sem reescrevê-la.

Aceite reproduzível exige checkout limpo. Runs locais em workspace sujo podem
orientar desenvolvimento, mas recebem `PASS_WITH_LIMITATIONS`.
