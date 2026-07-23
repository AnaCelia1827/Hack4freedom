module.exports = {
  docsSidebar: [
    {type: 'doc', id: 'contexto', label: 'Visão geral'},
    {type: 'doc', id: 'docs/ideia', label: 'Introdução'},
    {
      type: 'category',
      label: 'Produto e experiência',
      link: {type: 'generated-index', title: 'Produto e experiência'},
      items: [
        {type: 'doc', id: 'docs/requisitos', label: 'Requisitos do MVP'},
        {type: 'doc', id: 'docs/fluxos', label: 'Fluxos do MVP'},
        {type: 'doc', id: 'docs/validacao', label: 'Validação da ideia'},
      ],
    },
    {
      type: 'category',
      label: 'Arquitetura técnica',
      link: {type: 'generated-index', title: 'Arquitetura técnica'},
      items: [
        {type: 'doc', id: 'docs/tecnologias', label: 'Tecnologias por feature'},
        {type: 'doc', id: 'docs/lightning', label: 'Lightning Network'},
      ],
    },
    {
      type: 'category',
      label: 'Modelo e sustentabilidade',
      link: {type: 'generated-index', title: 'Modelo e sustentabilidade'},
      items: [
        {type: 'doc', id: 'docs/financeiro', label: 'Arquitetura financeira'},
      ],
    },
  ],
};
