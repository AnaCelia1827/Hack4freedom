const {themes: prismThemes} = require('prism-react-renderer');

const config = {
  title: 'Hack4Freedom',
  tagline: 'Aprender, trabalhar e receber com liberdade',
  favicon: 'img/icon.png',
  url: 'https://anacelia1827.github.io',
  baseUrl: '/Hack4freedom/',
  organizationName: 'AnaCelia1827',
  projectName: 'Hack4freedom',
  trailingSlash: false,
  onBrokenLinks: 'throw',
  markdown: {
    format: 'detect',
    hooks: {onBrokenMarkdownLinks: 'throw'},
  },
  i18n: {
    defaultLocale: 'pt-BR',
    locales: ['pt-BR'],
  },
  presets: [
    [
      'classic',
      {
        docs: {
          path: 'docs',
          routeBasePath: '/',
          sidebarPath: require.resolve('./sidebars.js'),
          editUrl: 'https://github.com/AnaCelia1827/Hack4freedom/edit/main/docs/docs/',
        },
        blog: false,
        theme: {customCss: require.resolve('./src/css/custom.css')},
      },
    ],
  ],
  themeConfig: {
    image: 'img/social-card.svg',
    metadata: [
      {name: 'description', content: 'Documentação do projeto Hack4Freedom Brasil 2026.'},
    ],
    navbar: {
      title: 'Documentação',
      logo: {alt: 'Hack4Freedom', src: 'img/logo.png'},
      items: [
        {
          href: 'https://github.com/AnaCelia1827/Hack4freedom',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Documentação',
          items: [
            {label: 'Visão geral', to: '/'},
            {label: 'Arquitetura da solução', to: '/solucao/arquitetura'},
          ],
        },
        {
          title: 'Arquitetura',
          items: [
            {label: 'Tecnologias', to: '/implementação/arquitetura_tecnica'},
            {label: 'Lightning', to: '/implementação/bitcoin'},
          ],
        },
        {
          title: 'Projeto',
          items: [
            {
              label: 'Repositório no GitHub',
              href: 'https://github.com/AnaCelia1827/Hack4freedom',
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Hack4Freedom. Construído com Docusaurus.`,
    },
    colorMode: {defaultMode: 'dark', respectPrefersColorScheme: true},
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['bash', 'json', 'python'],
    },
  },
};

module.exports = config;
