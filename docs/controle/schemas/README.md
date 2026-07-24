# Schemas LARES

Os schemas documentam o contrato serializado dos registros. O validador
executável em `tools/lares/lares.py` aplica também regras cruzadas que JSON
Schema isolado não consegue expressar, como existência de referências,
precedência de risco, vínculo a commit e independência do verificador.

Não altere um schema sem elevar `schema_version` ou documentar compatibilidade.
