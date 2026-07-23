export const screenSpecs = {
  landing: { route: '/', figmaNodeId: '66:2337' },
  login: { route: '/entrar', figmaNodeId: '111:311' },
  community: { route: '/app/comunidade', figmaNodeId: '51:1072' },
  opportunities: { route: '/app/oportunidades', figmaNodeId: '101:9' },
  opportunityDetails: { route: '/app/oportunidades/:opportunityId', figmaNodeId: '48:117' },
  assignmentSubmission: { route: '/app/trabalhos/:assignmentId/entrega', figmaNodeId: '48:631' },
  wallet: { route: '/app/carteira', figmaNodeId: '48:374' },
  learningCatalog: { route: '/app/capacitacao', figmaNodeId: '51:1739' },
  lesson: { route: '/app/capacitacao/:courseId/aulas/:lessonId', figmaNodeId: '51:714' },
  learningActivity: { route: '/app/capacitacao/:courseId/atividades/:activityId', figmaNodeId: '51:1960' },
  opportunityDraftBasic: { route: '/app/oportunidades/nova/basico', figmaNodeId: '101:119' },
} as const
