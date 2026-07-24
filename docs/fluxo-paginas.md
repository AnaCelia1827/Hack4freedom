Link MCP: https://www.figma.com/design/TyhhDZgTJ4jqqKfnq1jdNZ/hack4frredom?node-id=186-890&t=fLHfIalxDatSsJmy-0

Fluxo de Navegação das Telas
1. Fluxo inicial
Landing Page
A Landing Page possui três botões:

Empower Now → direciona para a tela de Login.

Começar minha jornada → direciona para a tela de Login.

Ver como funciona → abre um pop-up com o vídeo explicativo.

No pop-up:

O usuário pode assistir ao vídeo.

Ao fechar o pop-up, permanece na Landing Page.

Landing Page
├── Empower Now → Login
├── Começar minha jornada → Login
└── Ver como funciona → Pop-up com vídeo
                           └── Fechar → Landing Page
2. Tela de Login
Na tela de Login, o usuário escolhe como deseja entrar:

Entrar como participante

Entrar como contratante

Login
├── Entrar como participante → Fluxo da participante
└── Entrar como contratante → Fluxo do contratante/doador
3. Fluxo da participante
3.1 Participante que já possui conta
Login
→ Entrar como participante
→ Preencher dados de login
→ Clicar em Entrar
→ Comunidade
3.2 Participante que ainda não possui conta
Na tela de Login:

Criar conta
→ Cadastro: Etapa 1
→ Cadastro: Etapa 2
→ Cadastro: Etapa 3
→ Cadastro: Etapa 4
→ Comunidade
O fluxo do cadastro acontece da esquerda para a direita:

1. Dados pessoais
→ Continuar

2. Identificação
→ Continuar

3. Habilidades
→ Continuar

4. Verificação
→ Finalizar cadastro

→ Comunidade
Em todas as etapas:

Continuar → avança para a próxima tela.

Voltar → retorna para a etapa anterior.

4. Navegação principal da participante
Depois do login ou da finalização do cadastro, a participante entra na tela de Comunidade.

A partir da navegação principal, ela pode acessar:

Comunidade
├── Oportunidades
├── Capacitação
└── Foto de perfil → Minha Carteira
5. Fluxo da Comunidade
Tela de Comunidade
Na tela de Comunidade, a participante pode:

Visualizar as publicações.

Rolar a tela para ver mais publicações.

Criar uma nova publicação.

Navegar para outras áreas da aplicação.

Comunidade
├── Rolar para baixo → Ver mais publicações
├── Criar publicação → Tela de criação de post
├── Oportunidades → Tela de Oportunidades
├── Capacitação → Tela de Capacitação
└── Foto de perfil → Minha Carteira
Criar uma publicação
Comunidade
→ Criar publicação
→ Escrever publicação
→ Publicar
→ Voltar para Comunidade
Caso a participante cancele:

Criar publicação
→ Cancelar
→ Comunidade
6. Fluxo de Oportunidades
Tela de Oportunidades
A tela de Oportunidades possui três fluxos semanticamente distintos, sem alterar o desenho das telas existentes:

Publicar uma oportunidade comunitária não remunerada como participante.

Abrir uma oportunidade comunitária e seguir para sua origem externa.

Participar de uma oportunidade remunerada publicada por organização/contratante.

Oportunidades
├── Publicar oportunidade → Criar OpportunityListing comunitária
├── Clicar em oportunidade comunitária → Detalhes → Origem externa
└── Clicar em oportunidade remunerada → Detalhes da PaidTask
7. Publicar uma oportunidade comunitária

Este wizard pertence à participante e cria uma `OpportunityListing` não remunerada. A participante atua somente como divulgadora. Exemplos: hackathons, cursos gratuitos, eventos, palestras, encontros, mentorias e programas educacionais.

O wizard não cria `PaidTask`, funding, assignment, entrega, revisão, obrigação ou pagamento. A criação de `PaidTask` pertence ao perfil de organização/contratante e não deve reutilizar este fluxo.
O fluxo de criação acontece da esquerda para a direita e possui quatro telas.

Oportunidades
→ Publicar oportunidade
→ Criar divulgação: Tela 1
→ Criar divulgação: Tela 2
→ Criar divulgação: Tela 3
→ Revisar divulgação: Tela 4
→ Publicar
→ Feed de Oportunidades, na seção comunitária/não remunerada
Navegação detalhada
Tela 1
→ Continuar
→ Tela 2

Tela 2
→ Continuar
→ Tela 3

Tela 3
→ Continuar
→ Tela 4: Revisão

Tela 4
→ Publicar
→ Feed de Oportunidades, na seção comunitária/não remunerada
Na última tela, a participante deve revisar as informações e a origem externa antes de publicar a divulgação.

Botões de retorno
Voltar → retorna para a etapa anterior.

Editar → retorna para a tela correspondente à informação que será alterada.

Publicar → publica a oportunidade e retorna ao feed.

Revisão da oportunidade
├── Voltar → Etapa anterior
├── Editar → Etapa selecionada
└── Publicar → Feed de Oportunidades, seção comunitária
8. Abrir ou participar de uma oportunidade
Na tela de Oportunidades, a participante pode selecionar um item. O destino depende do tipo discriminado pela API.

Oportunidade comunitária não remunerada:

Oportunidades
→ Clicar em OpportunityListing
→ Detalhes da divulgação
→ Acessar origem externa

Esse caminho termina fora do workflow de trabalho do Bluejet e não cria candidatura ou atividade.

Oportunidade remunerada:

Oportunidades
→ Clicar em uma PaidTask
→ Detalhes da oportunidade remunerada
Na tela de detalhes:

Detalhes da oportunidade remunerada
→ Candidatar-se ou Participar
→ Área da atividade
Caso seja necessário confirmar a candidatura:

Detalhes da oportunidade remunerada
→ Candidatar-se
→ Confirmar candidatura
→ Área da atividade
9. Área de atividade e submissão
Depois de participar de uma `PaidTask` remunerada, a usuária acessa a área da atividade. `OpportunityListing` nunca entra neste fluxo.

Área da atividade
→ Fazer atividade
→ Área de submissão
Na área de submissão, a participante pode escrever a resposta, escolher um arquivo ou adicionar o material solicitado.

Área de submissão
├── Salvar → Permanecer na atividade
└── Enviar atividade → Atividade enviada
Depois do envio:

Enviar atividade
→ Exibir atividade como enviada
→ Voltar para a Área da atividade
A participante também poderá visualizar essa oportunidade na área de atividades em andamento da carteira.

10. Fluxo de Capacitação
Na tela de Capacitação, a participante visualiza os estudos e trilhas disponíveis ou em andamento.

Capacitação
→ Selecionar uma capacitação
→ Detalhes da capacitação
Na tela de detalhes, ela visualiza os conteúdos da trilha.

Detalhes da capacitação
→ Selecionar uma aula
→ Conteúdo da aula
Depois de estudar o conteúdo:

Conteúdo da aula
→ Fazer atividade
→ Task da capacitação
Na tela da task:

Task da capacitação
→ Escrever ou anexar a atividade
→ Enviar
→ Atualizar progresso da capacitação
→ Voltar para Detalhes da capacitação
O fluxo completo fica:

Capacitação
→ Capacitação selecionada
→ Detalhes da capacitação
→ Conteúdo da aula
→ Fazer atividade
→ Task
→ Enviar atividade
→ Atualizar progresso
→ Detalhes da capacitação
Quando a participante concluir todas as aulas e tasks:

Última atividade enviada
→ Capacitação concluída
11. Fluxo da Carteira
A participante acessa a carteira clicando na sua foto de perfil ou logo de usuário.

Foto de perfil
→ Minha Carteira
Na tela Minha Carteira, ela pode visualizar:

Saldo disponível.

Valor recebido durante o mês.

Estudos em andamento.

Oportunidades em andamento.

Atividades em andamento ou enviadas.

Navegação pela carteira
Minha Carteira
├── Clicar em estudo em andamento → Detalhes da capacitação
├── Clicar em oportunidade em andamento → Área da atividade
└── Resgatar → Tela de saque
12. Fluxo de saque
Minha Carteira
→ Resgatar
→ Tela de saque
→ Confirmar saque
→ Saque realizado
Depois da confirmação:

Saque realizado
→ Voltar para Minha Carteira
Caso a participante cancele:

Tela de saque
→ Cancelar
→ Minha Carteira
Esse é o final do fluxo principal da participante.

13. Fluxo do contratante/doador
O segundo tipo de usuário entra pela opção Entrar como contratante.

Login
→ Entrar como contratante
→ Fluxo de aporte
O fluxo do contratante possui quatro etapas:

1. Aporte
→ 2. Condições
→ 3. Pagamento
→ 4. Comprovante
14. Etapa de aporte
Na primeira tela, o contratante escolhe o valor que deseja aportar.

Aporte
→ Escolher valor
→ Continuar
→ Condições
Caso clique em voltar:

Aporte
→ Voltar
→ Login
15. Etapa de condições
Na tela de Condições, o contratante lê as regras e condições do aporte.

Condições
→ Aceitar condições
→ Continuar
→ Pagamento
Caso clique em voltar:

Condições
→ Voltar
→ Aporte
16. Etapa de pagamento
Na tela de Pagamento, o aporte é realizado utilizando a tecnologia Lightning.

Pagamento
→ Realizar pagamento pela Lightning
→ Pagamento confirmado
→ Comprovante
Caso clique em voltar antes de realizar o pagamento:

Pagamento
→ Voltar
→ Condições
17. Tela de comprovante
Depois que o pagamento for confirmado, o contratante é direcionado para a tela de Comprovante.

Comprovante
├── Baixar comprovante → Baixar arquivo e permanecer na tela
└── Voltar ao início → Landing Page
O fluxo completo do contratante fica:

Landing Page
→ Login
→ Entrar como contratante
→ Aporte
→ Condições
→ Pagamento com Lightning
→ Comprovante
→ Baixar comprovante ou voltar ao início
18. Resumo completo dos dois fluxos
Fluxo da participante
Landing Page
→ Login
→ Entrar como participante
→ Login ou Cadastro
→ Comunidade
├── Criar publicação
├── Oportunidades
│   ├── Publicar divulgação comunitária não remunerada
│   ├── Acessar origem externa de divulgação comunitária
│   └── Participar de PaidTask remunerada
│       → Detalhes
│       → Candidatar-se
│       → Área da atividade
│       → Submissão
├── Capacitação
│   → Detalhes da capacitação
│   → Conteúdo da aula
│   → Task
│   → Enviar atividade
└── Foto de perfil
    → Minha Carteira
    → Resgatar
    → Saque
Fluxo visual atualmente rotulado “contratante/doador”

Este fluxo existente representa aporte. Ele não concede, por si só, permissão de organização para criar `PaidTask`. A entrada específica da organização/contratante permanece condicionada à identificação de telas canônicas no Figma e à resolução de `DIV-IDENTITY-001`; nenhuma tela nova deve ser inventada.

Landing Page
→ Login
→ Entrar como contratante
→ Aporte
→ Condições
→ Pagamento com Lightning
→ Comprovante
→ Baixar comprovante ou voltar ao início
Instrução para a IA
Utilize as telas já existentes no projeto. Não crie novas telas e não altere o design visual.

Conecte os botões e componentes clicáveis conforme o fluxo descrito neste documento. Os fluxos de cadastro, criação de oportunidade e aporte devem avançar da esquerda para a direita. Os botões “Voltar” devem retornar sempre para a tela imediatamente anterior.

Após a conclusão de cada fluxo:

Cadastro concluído → Comunidade.

Publicação criada → Comunidade.

Oportunidade publicada → Feed de Oportunidades.

Candidatura realizada → Área da atividade.

Atividade enviada → Área da atividade com status atualizado.

Task da capacitação enviada → Detalhes da capacitação com progresso atualizado.

Saque realizado → Minha Carteira.

Aporte realizado → Comprovante.

Voltar ao início no comprovante → Landing Page.
