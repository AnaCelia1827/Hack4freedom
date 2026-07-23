# Gate Decisions

Este diretório recebe decisões imutáveis de aceite ou rejeição. Um Work Item
nunca usa `ACEITO` em seu próprio campo `state`.

- `ACCEPT` exige evidência no mesmo commit e uma run com workspace limpo.
- S2/S3 exige verificador distinto do produtor.
- S3 exige aprovação humana verificável.
- Uma correção posterior cria nova decisão; não edite a decisão histórica.
