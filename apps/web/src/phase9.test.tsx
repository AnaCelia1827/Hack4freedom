import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import {
  LearningActivityScreen,
  LearningCatalogScreen,
  LearningCourseScreen,
  LearningLessonScreen,
  LearningQuizScreen,
} from './phase9'

const course = {
  id: 'bluejet-basics',
  version: '1.0',
  title: 'Fundamentos Bluejet',
  objective: 'Aprender o fluxo de trabalho com segurança.',
  duration_minutes: 90,
}

const courseDetail = {
  ...course,
  assessment_version: 'v1',
  module_id: 'module-1',
  modules: [{
    id: 'module-1',
    title: 'Primeiro módulo',
    order: 1,
    lessons: [{ id: 'lesson-1', title: 'Evidências e entrega', order: 1, activity_ids: ['activity-1'] }],
  }],
  questions: [
    { id: 'q1', prompt: 'Qual é o primeiro passo?' },
    { id: 'q2', prompt: 'Como registrar a entrega?' },
    { id: 'q3', prompt: 'Quem aprova o trabalho?' },
    { id: 'q4', prompt: 'Qual é a nota mínima?' },
    { id: 'q5', prompt: 'O que a evidência comprova?' },
  ],
}

const lesson = {
  id: 'lesson-1',
  course_id: course.id,
  module_id: 'module-1',
  title: 'Evidências e entrega',
  status: 'AVAILABLE',
  activity_ids: ['activity-1'],
}

const activity = {
  id: 'activity-1',
  course_id: course.id,
  module_id: 'module-1',
  lesson_id: lesson.id,
  title: 'Atividade prática',
  status: 'AVAILABLE',
}

function courseApi(path: string) {
  if (path === `/courses/${course.id}`) return Promise.resolve(courseDetail)
  if (path === `/courses/${course.id}/enrollments`) return Promise.resolve({ status: 'IN_PROGRESS', progress: 25, attempt_count: 1 })
  if (path === '/skill-evidence') return Promise.resolve({ items: [] })
  return Promise.reject(new Error(`unexpected ${path}`))
}

function catalogApi(enrollments: unknown[] = []) {
  return vi.fn((path: string) => {
    if (path === '/courses') return Promise.resolve({ items: [course] })
    if (path === '/courses/enrollments') return Promise.resolve({ items: enrollments })
    return Promise.reject(new Error(`unexpected ${path}`))
  })
}

describe('Catálogo de capacitação da Fase 9', () => {
  it('renderiza somente os dados entregues pela API', async () => {
    const api = catalogApi()
    render(<LearningCatalogScreen api={api} navigate={vi.fn()} />)
    expect(await screen.findByText(course.title)).toBeInTheDocument()
    expect(screen.getAllByText('1h 30min')).toHaveLength(2)
    expect(screen.getByText('Nenhuma trilha em andamento')).toBeInTheDocument()
    expect(screen.queryByText('64%')).not.toBeInTheDocument()
    expect(screen.queryByText('120h')).not.toBeInTheDocument()
  })

  it('expõe loading e lista vazia textuais', async () => {
    let resolveCatalog!: (value: unknown) => void
    let resolveEnrollments!: (value: unknown) => void
    const api = vi.fn((path: string) => new Promise(value => {
      if (path === '/courses') resolveCatalog = value
      else resolveEnrollments = value
    }))
    render(<LearningCatalogScreen api={api} navigate={vi.fn()} />)
    expect(screen.getByLabelText('Carregando trilhas')).toBeInTheDocument()
    resolveCatalog({ items: [] })
    resolveEnrollments({ items: [] })
    expect(await screen.findByText('Nenhuma trilha disponível agora.')).toBeInTheDocument()
  })

  it('exibe erro e repete a leitura', async () => {
    let catalogAttempts = 0
    const api = vi.fn((path: string) => {
      if (path === '/courses/enrollments') return Promise.resolve({ items: [] })
      catalogAttempts += 1
      return catalogAttempts === 1 ? Promise.reject(new Error('offline')) : Promise.resolve({ items: [course] })
    })
    const user = userEvent.setup()
    render(<LearningCatalogScreen api={api} navigate={vi.fn()} />)
    await user.click(await screen.findByRole('button', { name: 'Tentar novamente' }))
    expect(await screen.findByText(course.title)).toBeInTheDocument()
    expect(api.mock.calls.filter(([path]) => path === '/courses')).toHaveLength(2)
  })

  it('navega para o detalhe preservando o id da API', async () => {
    const navigate = vi.fn()
    const user = userEvent.setup()
    render(<LearningCatalogScreen api={catalogApi()} navigate={navigate} />)
    await user.click(await screen.findByRole('button', { name: 'Ver trilha' }))
    await waitFor(() => expect(navigate).toHaveBeenCalledWith('/app/capacitacao/bluejet-basics'))
  })

  it('exibe uma trilha persistida pela API com progresso de 50 por cento em Em andamento', async () => {
    const enrollment = {
      id: 'enrollment-test',
      course_id: course.id,
      course_version: course.version,
      status: 'IN_PROGRESS',
      progress: 50,
      attempt_count: 1,
    }
    render(<LearningCatalogScreen api={catalogApi([enrollment])} navigate={vi.fn()} />)
    expect(await screen.findByRole('progressbar', { name: `Progresso de ${course.title}` })).toHaveAttribute('aria-valuenow', '50')
    expect(screen.getByRole('button', { name: 'Continuar trilha' })).toBeInTheDocument()
  })
})

describe('Fluxo de capacitação da Fase 9', () => {
  it('mantém o botão Voltar disponível no quiz antes e depois da avaliação', async () => {
    const api = vi.fn((path: string) => {
      if (path === `/courses/${course.id}`) return Promise.resolve(courseDetail)
      if (path.includes('/quiz-attempts')) return Promise.resolve({ attempt: { score: 0, attempt_number: 1 }, passed: false, skill_evidence: null })
      return Promise.reject(new Error(`unexpected ${path}`))
    })
    const navigate = vi.fn()
    const user = userEvent.setup()
    render(<LearningQuizScreen api={api} navigate={navigate} courseId={course.id} />)

    await user.click(await screen.findByRole('button', { name: 'Voltar para a capacitação' }))
    expect(navigate).toHaveBeenCalledWith('/app/capacitacao/bluejet-basics')

    for (const question of courseDetail.questions) {
      const group = screen.getByRole('group', { name: question.prompt })
      await user.click(group.querySelector('input[type="radio"]') as HTMLInputElement)
    }
    await user.click(screen.getByRole('button', { name: 'Enviar respostas' }))
    expect(await screen.findByText(/progresso de 50% foram preservados/)).toBeInTheDocument()
    expect(screen.getAllByRole('button', { name: 'Voltar para a capacitação' })).toHaveLength(2)
  })

  it('renderiza detalhe, progresso e aulas somente com dados da API', async () => {
    const navigate = vi.fn()
    const user = userEvent.setup()
    render(<LearningCourseScreen api={vi.fn(courseApi)} navigate={navigate} courseId={course.id} />)

    expect(await screen.findByRole('heading', { name: course.title })).toBeInTheDocument()
    expect(screen.getByRole('progressbar', { name: 'Progresso da capacitação' })).toHaveAttribute('aria-valuenow', '25')
    expect(screen.getByText('Primeiro módulo')).toBeInTheDocument()
    expect(screen.getAllByText('Evidências e entrega')).toHaveLength(2)
    await user.click(screen.getByRole('button', { name: /Iniciar aula/ }))
    expect(navigate).toHaveBeenCalledWith('/app/capacitacao/bluejet-basics/aulas/lesson-1')
  })

  it('confirma no detalhe o retorno após uma atividade enviada', async () => {
    render(<LearningCourseScreen api={vi.fn(courseApi)} navigate={vi.fn()} courseId={course.id} activitySubmitted />)
    expect(await screen.findByText('Atividade enviada. O progresso disponível foi atualizado.')).toBeInTheDocument()
  })

  it('carrega e salva anotações sem inventar vídeo ou materiais', async () => {
    const api = vi.fn((path: string, options?: RequestInit) => {
      if (path.endsWith('/notes') && options?.method === 'PUT') return Promise.resolve({ content: 'Nova anotação' })
      if (path.endsWith('/notes')) return Promise.resolve({ content: 'Anotação anterior' })
      return Promise.resolve(lesson)
    })
    const user = userEvent.setup()
    render(<LearningLessonScreen api={api} navigate={vi.fn()} courseId={course.id} lessonId={lesson.id} />)

    const notes = await screen.findByLabelText('Anotação da aula')
    expect(notes).toHaveValue('Anotação anterior')
    expect(screen.getByText('Conteúdo multimídia não disponibilizado')).toBeInTheDocument()
    expect(screen.getByText('Não fornecidos pela API.')).toBeInTheDocument()
    await user.clear(notes)
    await user.type(notes, 'Nova anotação')
    await user.click(screen.getByRole('button', { name: 'Salvar anotações' }))
    expect(await screen.findByText('Anotação salva.')).toBeInTheDocument()
    expect(api).toHaveBeenCalledWith(
      '/courses/bluejet-basics/lessons/lesson-1/notes',
      expect.objectContaining({ method: 'PUT', body: JSON.stringify({ content: 'Nova anotação' }) }),
    )
  })

  it('navega da aula para a atividade real do contrato', async () => {
    const navigate = vi.fn()
    const api = vi.fn((path: string) => path.endsWith('/notes') ? Promise.resolve({ content: '' }) : Promise.resolve(lesson))
    const user = userEvent.setup()
    render(<LearningLessonScreen api={api} navigate={navigate} courseId={course.id} lessonId={lesson.id} />)
    await user.click(await screen.findByRole('button', { name: /Fazer atividade/ }))
    expect(navigate).toHaveBeenCalledWith('/app/capacitacao/bluejet-basics/atividades/activity-1')
  })

  it('rejeita atividade vazia antes de chamar a API', async () => {
    const api = vi.fn().mockResolvedValue(activity)
    const user = userEvent.setup()
    render(<LearningActivityScreen api={api} navigate={vi.fn()} courseId={course.id} activityId={activity.id} />)
    await user.click(await screen.findByRole('button', { name: /Enviar atividade/ }))
    expect(screen.getByRole('alert')).toHaveTextContent('Escreva sua atividade antes de enviar.')
    expect(api).toHaveBeenCalledTimes(1)
  })

  it('rejeita mais de 20000 caracteres e não oferece upload', async () => {
    const api = vi.fn().mockResolvedValue(activity)
    render(<LearningActivityScreen api={api} navigate={vi.fn()} courseId={course.id} activityId={activity.id} />)
    const response = await screen.findByLabelText('Resposta')
    fireEvent.change(response, { target: { value: 'a'.repeat(20001) } })
    fireEvent.submit(response.closest('form')!)
    expect(screen.getByRole('alert')).toHaveTextContent('no máximo 20000 caracteres')
    expect(document.querySelector('input[type="file"]')).not.toBeInTheDocument()
    expect(api).toHaveBeenCalledTimes(1)
  })

  it('envia uma vez e retorna ao detalhe com confirmação', async () => {
    let resolveSubmission!: (value: unknown) => void
    const submission = new Promise(value => { resolveSubmission = value })
    const api = vi.fn((path: string) => path.endsWith('/submissions') ? submission : Promise.resolve(activity))
    const navigate = vi.fn()
    const user = userEvent.setup()
    render(<LearningActivityScreen api={api} navigate={navigate} courseId={course.id} activityId={activity.id} />)
    await user.type(await screen.findByLabelText('Resposta'), 'Minha entrega prática')
    const send = screen.getByRole('button', { name: /Enviar atividade/ })
    await user.dblClick(send)
    expect(api.mock.calls.filter(([path]) => String(path).endsWith('/submissions'))).toHaveLength(1)
    resolveSubmission({ id: 'submission-1' })
    await waitFor(() => expect(navigate).toHaveBeenCalledWith('/app/capacitacao/bluejet-basics?atividade=enviada'))
  })

  it('expõe conflito de submissão duplicada sem navegar', async () => {
    const conflict = Object.assign(new Error('Activity already submitted'), { status: 409 })
    const api = vi.fn((path: string) => path.endsWith('/submissions') ? Promise.reject(conflict) : Promise.resolve(activity))
    const navigate = vi.fn()
    const user = userEvent.setup()
    render(<LearningActivityScreen api={api} navigate={navigate} courseId={course.id} activityId={activity.id} />)
    await user.type(await screen.findByLabelText('Resposta'), 'Entrega repetida')
    await user.click(screen.getByRole('button', { name: /Enviar atividade/ }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Esta atividade já foi enviada.')
    expect(navigate).not.toHaveBeenCalled()
  })
})
