# Ferramentas LARES

O CLI não possui dependências externas e deve ser executado a partir de qualquer
diretório dentro do repositório:

```bash
python tools/lares/lares.py doctor
python tools/lares/lares.py validate
python tools/lares/lares.py status --check
python tools/lares/lares.py meta-test
python tools/lares/lares.py fingerprint AGENTS.md docs/requisitos.md
python tools/lares/lares.py workspace-fingerprint --exclude docs/controle/runs --exclude docs/controle/evidence --exclude docs/controle/status.md
python -m unittest discover -s tools/lares -p 'test_*.py'
```

Use `status --write` somente depois de alterar registros em `docs/controle`.
`status.md` é uma projeção e não uma fonte editável.

O comando `doctor --strict` falha quando o workspace está sujo. O CI utiliza
esse modo para impedir que evidências reproduzíveis dependam de arquivos locais
não rastreados.
