import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import {
  ArrowLeft,
  ArrowRight,
  BookOpen,
  CheckCircle2,
  Clock3,
  FileText,
  Layers3,
  NotebookPen,
  Paperclip,
  Play,
  RotateCcw,
  Sparkles,
} from 'lucide-react'
import type { ApiClient } from './phase8'

type CourseCatalogItem = {
  id: string
  version: string
  title: string
  objective: string
  duration_minutes: number
}

type CatalogState =
  | { status: 'loading' }
  | { status: 'error' }
  | { status: 'ready'; items: CourseCatalogItem[]; enrollments: Enrollment[] }

type CourseLesson = {
  id: string
  title: string
  order?: number
  activity_ids?: string[]
}

type CourseModule = {
  id: string
  title: string
  order?: number
  lessons?: CourseLesson[]
}

type CourseDetail = CourseCatalogItem & {
  assessment_version: string
  module_id: string
  modules?: CourseModule[]
  questions?: { id: string; prompt: string }[]
}

type Enrollment = {
  id?: string
  course_id?: string
  course_version?: string
  status: 'IN_PROGRESS' | 'COMPLETED'
  progress: number
  attempt_count: number
}

type LessonDetail = {
  id: string
  course_id: string
  module_id: string
  title: string
  status: string
  activity_ids?: string[]
}

type ActivityDetail = {
  id: string
  course_id: string
  module_id: string
  lesson_id: string
  title: string
  status: string
}

type LoadState<T> =
  | { status: 'loading' }
  | { status: 'error'; code?: number }
  | { status: 'ready'; data: T }

type QuizResult = {
  attempt: { score: number; attempt_number: number }
  passed: boolean
  skill_evidence?: { id: string } | null
  badge?: { id?: string; status?: string }
}

const QUIZ_ANSWER_OPTIONS = ['planejar', 'evidencia', 'revisor', '80', 'competencia']

function errorStatus(error: unknown) {
  return (error as Error & { status?: number })?.status
}

function routeSegment(value: string) {
  return encodeURIComponent(value)
}

function LearningLoadError({ code, retry }: { code?: number; retry: () => void }) {
  const title = code === 401
    ? 'Sua sessão expirou.'
    : code === 403
      ? 'Você não tem permissão para acessar este conteúdo.'
      : code === 404
        ? 'Conteúdo não encontrado.'
        : 'Não foi possível carregar este conteúdo.'
  return (
    <div className="learning-state" role="alert">
      <strong>{title}</strong>
      <p>{code === 401 ? 'Entre novamente para continuar.' : 'Tente novamente em alguns instantes.'}</p>
      <button type="button" onClick={retry}>Tentar novamente</button>
    </div>
  )
}

function durationLabel(minutes: number) {
  if (minutes < 60) return `${minutes} min`
  const hours = Math.floor(minutes / 60)
  const remainder = minutes % 60
  return remainder ? `${hours}h ${remainder}min` : `${hours}h`
}

export function LearningCatalogScreen({ api, navigate }: { api: ApiClient; navigate: (path: string) => void }) {
  const [state, setState] = useState<CatalogState>({ status: 'loading' })

  const load = useCallback(async () => {
    setState({ status: 'loading' })
    try {
      const [catalogResponse, enrollmentResponse] = await Promise.all([
        api('/courses'),
        api('/courses/enrollments'),
      ])
      setState({
        status: 'ready',
        items: Array.isArray(catalogResponse.items) ? catalogResponse.items : [],
        enrollments: Array.isArray(enrollmentResponse.items) ? enrollmentResponse.items : [],
      })
    } catch {
      setState({ status: 'error' })
    }
  }, [api])

  useEffect(() => {
    void load()
  }, [load])

  const items = state.status === 'ready' ? state.items : []
  const currentCourses = state.status === 'ready'
    ? state.enrollments.flatMap(enrollment => {
      if (enrollment.status !== 'IN_PROGRESS') return []
      const course = state.items.find(item => (
        item.id === enrollment.course_id && item.version === enrollment.course_version
      ))
      return course ? [{ course, enrollment }] : []
    })
    : []
  const totalMinutes = items.reduce((total, course) => total + Number(course.duration_minutes || 0), 0)

  return (
    <main className="learning-catalog" aria-labelledby="learning-title">
      <section className="learning-summary">
        <div>
          <h1 id="learning-title">Trilhas de Capacitação</h1>
          <p>Desenvolva novas habilidades e prepare-se para o mercado com cursos e desafios focados em tecnologia e liderança.</p>
        </div>
        {state.status === 'ready' && items.length > 0 && (
          <dl className="learning-metrics" aria-label="Resumo do catálogo">
            <div>
              <dt>Trilhas disponíveis</dt>
              <dd>{items.length}</dd>
            </div>
            <div>
              <dt>Carga disponível</dt>
              <dd>{durationLabel(totalMinutes)}</dd>
            </div>
          </dl>
        )}
      </section>

      <div className="learning-filters" role="tablist" aria-label="Filtros de capacitação">
        <button type="button" role="tab" aria-selected="true">Todas as trilhas</button>
      </div>

      <section className="learning-section" aria-labelledby="learning-current-title">
        <h2 id="learning-current-title"><Play aria-hidden="true" /> Em andamento</h2>
        {state.status === 'ready' && currentCourses.length > 0 ? (
          <div className="learning-current-grid">
            {currentCourses.map(({ course, enrollment }) => (
              <article className="learning-current-card" key={enrollment.id ?? `${course.id}-${course.version}`}>
                <div>
                  <span className="learning-kicker">Em andamento</span>
                  <h3>{course.title}</h3>
                  <p>{course.objective}</p>
                </div>
                <div className="learning-current-progress">
                  <strong>{enrollment.progress}%</strong>
                  <div className="learning-progress-track" role="progressbar" aria-label={`Progresso de ${course.title}`} aria-valuemin={0} aria-valuemax={100} aria-valuenow={enrollment.progress}>
                    <span style={{ width: `${Math.min(100, Math.max(0, enrollment.progress))}%` }} />
                  </div>
                  <button type="button" onClick={() => navigate(`/app/capacitacao/${routeSegment(course.id)}`)}>Continuar trilha</button>
                </div>
              </article>
            ))}
          </div>
        ) : state.status === 'ready' ? (
          <div className="learning-current-empty">
            <Sparkles aria-hidden="true" />
            <div>
              <strong>Nenhuma trilha em andamento</strong>
              <p>Abra uma trilha disponível para começar seus estudos.</p>
            </div>
          </div>
        ) : null}
      </section>

      <section className="learning-section" aria-labelledby="learning-all-title" aria-busy={state.status === 'loading'}>
        <h2 id="learning-all-title"><Layers3 aria-hidden="true" /> Todas as trilhas</h2>

        {state.status === 'loading' && (
          <div className="learning-grid" role="status" aria-label="Carregando trilhas">
            <div className="learning-skeleton" />
            <div className="learning-skeleton" />
            <div className="learning-skeleton" />
          </div>
        )}

        {state.status === 'error' && (
          <div className="learning-state" role="alert">
            <strong>Não foi possível carregar as trilhas.</strong>
            <p>Verifique sua conexão e tente novamente.</p>
            <button type="button" onClick={() => void load()}>Tentar novamente</button>
          </div>
        )}

        {state.status === 'ready' && items.length === 0 && (
          <div className="learning-state">
            <BookOpen aria-hidden="true" />
            <strong>Nenhuma trilha disponível agora.</strong>
            <p>Novas capacitações aparecerão aqui quando forem publicadas.</p>
          </div>
        )}

        {state.status === 'ready' && items.length > 0 && (
          <div className="learning-grid">
            {items.map(course => (
              <article className="learning-card" key={course.id}>
                <div className="learning-card-visual" aria-hidden="true">
                  <BookOpen />
                </div>
                <div className="learning-card-content">
                  <div className="learning-card-meta">
                    <span>Capacitação</span>
                    <span>Versão {course.version}</span>
                  </div>
                  <h3>{course.title}</h3>
                  <p>{course.objective}</p>
                  <div className="learning-card-footer">
                    <span><Clock3 aria-hidden="true" /> {durationLabel(course.duration_minutes)}</span>
                    <button type="button" onClick={() => navigate(`/app/capacitacao/${encodeURIComponent(course.id)}`)}>
                      Ver trilha
                    </button>
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  )
}

export function LearningCourseScreen({
  api,
  navigate,
  courseId,
  activitySubmitted = false,
}: {
  api: ApiClient
  navigate: (path: string) => void
  courseId: string
  activitySubmitted?: boolean
}) {
  const [state, setState] = useState<LoadState<{ course: CourseDetail; enrollment: Enrollment; badge?: { status?: string } }>>({ status: 'loading' })

  const load = useCallback(async () => {
    setState({ status: 'loading' })
    try {
      const [course, enrollment, evidenceResponse] = await Promise.all([
        api(`/courses/${routeSegment(courseId)}`),
        api(`/courses/${routeSegment(courseId)}/enrollments`, { method: 'POST' }),
        api('/skill-evidence'),
      ])
      const evidence = (evidenceResponse.items ?? []).find((item: { module_id?: string; assessment_version?: string }) => (
        item.module_id === course.module_id && item.assessment_version === course.assessment_version
      ))
      let badge
      if (evidence) {
        try {
          badge = await api(`/skill-evidence/${routeSegment(evidence.id)}/badge-publication`)
        } catch (error) {
          if (errorStatus(error) !== 404) throw error
        }
      }
      setState({ status: 'ready', data: { course, enrollment, badge } })
    } catch (error) {
      setState({ status: 'error', code: errorStatus(error) })
    }
  }, [api, courseId])

  useEffect(() => {
    void load()
  }, [load])

  if (state.status === 'loading') {
    return <main className="learning-flow"><div className="learning-detail-skeleton" role="status">Carregando capacitação...</div></main>
  }
  if (state.status === 'error') {
    return <main className="learning-flow"><LearningLoadError code={state.code} retry={() => void load()} /></main>
  }

  const { course, enrollment, badge } = state.data
  const modules = course.modules ?? []
  const firstLesson = modules.flatMap(module => module.lessons ?? [])[0]
  const completed = enrollment.status === 'COMPLETED'

  return (
    <main className="learning-flow" aria-labelledby="course-title">
      <button className="learning-breadcrumb" type="button" onClick={() => navigate('/app/capacitacao')}>
        <ArrowLeft aria-hidden="true" /> Capacitação
      </button>

      {activitySubmitted && (
        <div className="learning-success-banner" role="status">
          <CheckCircle2 aria-hidden="true" />
          <span>Atividade enviada. O progresso disponível foi atualizado.</span>
        </div>
      )}

      <section className="learning-course-hero">
        <div>
          <span className="learning-kicker">Trilha · Versão {course.version}</span>
          <h1 id="course-title">{course.title}</h1>
          <p>{course.objective}</p>
          <div className="learning-course-facts">
            <span><Clock3 aria-hidden="true" /> {durationLabel(course.duration_minutes)}</span>
            <span><Layers3 aria-hidden="true" /> {modules.length} módulo{modules.length === 1 ? '' : 's'}</span>
          </div>
        </div>
        <div className="learning-progress-card">
          <span>Seu progresso</span>
          <strong>{enrollment.progress}%</strong>
          <div className="learning-progress-track" role="progressbar" aria-label="Progresso da capacitação" aria-valuemin={0} aria-valuemax={100} aria-valuenow={enrollment.progress}>
            <span style={{ width: `${Math.min(100, Math.max(0, enrollment.progress))}%` }} />
          </div>
          <small>{enrollment.attempt_count} tentativa{enrollment.attempt_count === 1 ? '' : 's'} de avaliação</small>
        </div>
      </section>

      {completed && <p className="learning-complete" role="status"><CheckCircle2 aria-hidden="true" /> Capacitação concluída. Sua evidência foi registrada.</p>}
      {badge && <p className="learning-sandbox-notice" role="status">Badge {badge.status ?? 'registrado'} · ambiente SANDBOX, sem publicação Nostr.</p>}

      <section className="learning-course-layout">
        <div className="learning-module-list" aria-labelledby="course-content-title">
          <h2 id="course-content-title">Conteúdo da capacitação</h2>
          {modules.length === 0 ? (
            <div className="learning-state"><strong>Nenhum módulo disponível.</strong></div>
          ) : modules.map((module, moduleIndex) => (
            <article className="learning-module-card" key={module.id}>
              <header>
                <span>Módulo {module.order ?? moduleIndex + 1}</span>
                <h3>{module.title}</h3>
              </header>
              {(module.lessons ?? []).map((lesson, lessonIndex) => (
                <button
                  type="button"
                  className="learning-lesson-row"
                  key={lesson.id}
                  onClick={() => navigate(`/app/capacitacao/${routeSegment(course.id)}/aulas/${routeSegment(lesson.id)}`)}
                >
                  <span className="learning-lesson-number">{String(lesson.order ?? lessonIndex + 1).padStart(2, '0')}</span>
                  <span><strong>{lesson.title}</strong><small>{lesson.activity_ids?.length ? 'Inclui atividade prática' : 'Aula disponível'}</small></span>
                  <ArrowRight aria-hidden="true" />
                </button>
              ))}
            </article>
          ))}
        </div>

        <aside className="learning-course-actions" aria-label="Ações da capacitação">
          <span className="learning-kicker">Próximo passo</span>
          <h2>{firstLesson?.title ?? 'Conteúdo em preparação'}</h2>
          <p>{firstLesson ? 'Continue pela aula disponível e conclua a atividade.' : 'Esta capacitação ainda não possui aulas publicadas.'}</p>
          <button
            className="learning-primary-action"
            type="button"
            disabled={!firstLesson}
            onClick={() => firstLesson && navigate(`/app/capacitacao/${routeSegment(course.id)}/aulas/${routeSegment(firstLesson.id)}`)}
          >
            <Play aria-hidden="true" /> {completed ? 'Rever aula' : 'Iniciar aula'}
          </button>
          <button className="learning-secondary-action" type="button" onClick={() => navigate(`/app/capacitacao/${routeSegment(course.id)}/quiz`)}>
            {completed ? 'Refazer avaliação' : 'Fazer avaliação da trilha'}
          </button>
        </aside>
      </section>
    </main>
  )
}

export function LearningQuizScreen({
  api,
  navigate,
  courseId,
}: {
  api: ApiClient
  navigate: (path: string) => void
  courseId: string
}) {
  const [state, setState] = useState<LoadState<CourseDetail>>({ status: 'loading' })
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [result, setResult] = useState<QuizResult | null>(null)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const load = useCallback(async () => {
    setState({ status: 'loading' })
    try {
      setState({ status: 'ready', data: await api(`/courses/${routeSegment(courseId)}`) })
    } catch (caught) {
      setState({ status: 'error', code: errorStatus(caught) })
    }
  }, [api, courseId])

  useEffect(() => {
    void load()
  }, [load])

  const back = () => navigate(`/app/capacitacao/${routeSegment(courseId)}`)

  async function submit(event: FormEvent) {
    event.preventDefault()
    if (state.status !== 'ready') return
    const questions = state.data.questions ?? []
    if (questions.length === 0 || !questions.every(question => answers[question.id])) {
      setError('Responda todas as perguntas antes de enviar.')
      return
    }
    if (submitting) return
    setError('')
    setSubmitting(true)
    try {
      setResult(await api(`/modules/${routeSegment(state.data.module_id)}/quiz-attempts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answers }),
      }))
    } catch (caught) {
      const status = errorStatus(caught)
      setError(status === 401 ? 'Sua sessão expirou. Entre novamente para enviar.' : status === 403 ? 'Você não tem permissão para enviar esta avaliação.' : 'Não foi possível registrar a tentativa.')
    } finally {
      setSubmitting(false)
    }
  }

  async function requestBadge() {
    if (!result?.skill_evidence || result.badge) return
    setError('')
    try {
      const badge = await api(`/skill-evidence/${routeSegment(result.skill_evidence.id)}/badge-consent`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ consent: true }),
      })
      setResult(current => current ? { ...current, badge } : current)
    } catch {
      setError('Não foi possível registrar o consentimento agora.')
    }
  }

  function retry() {
    setAnswers({})
    setResult(null)
    setError('')
  }

  return (
    <main className="learning-flow learning-quiz" aria-labelledby="learning-quiz-title">
      <button className="learning-breadcrumb" type="button" onClick={back}>
        <ArrowLeft aria-hidden="true" /> Voltar para a capacitação
      </button>

      {state.status === 'loading' && <div className="learning-detail-skeleton" role="status">Carregando quiz...</div>}
      {state.status === 'error' && <LearningLoadError code={state.code} retry={() => void load()} />}
      {state.status === 'ready' && (
        <section className="learning-quiz-card">
          <span className="learning-kicker">Avaliação {state.data.assessment_version}</span>
          <h1 id="learning-quiz-title">Quiz da trilha</h1>
          <p className="learning-lead">Nota mínima para comprovar a competência: 80%.</p>

          {!result ? (
            <form onSubmit={submit}>
              {(state.data.questions ?? []).map(question => (
                <fieldset className="learning-quiz-question" key={question.id}>
                  <legend>{question.prompt}</legend>
                  <div className="learning-quiz-choices">
                    {QUIZ_ANSWER_OPTIONS.map(answer => (
                      <label className="choice" key={answer}>
                        <input
                          type="radio"
                          name={question.id}
                          checked={answers[question.id] === answer}
                          onChange={() => setAnswers(current => ({ ...current, [question.id]: answer }))}
                        />
                        {answer}
                      </label>
                    ))}
                  </div>
                </fieldset>
              ))}
              {error && <div className="learning-inline-error" role="alert">{error}</div>}
              <div className="learning-quiz-actions">
                <button type="button" className="learning-secondary-action" onClick={back}>Voltar</button>
                <button type="submit" className="learning-primary-action" disabled={submitting}>{submitting ? 'Enviando...' : 'Enviar respostas'}</button>
              </div>
            </form>
          ) : (
            <div className="learning-quiz-result" role="status">
              <strong>Resultado: {result.attempt.score}% · tentativa {result.attempt.attempt_number}</strong>
              <p>{result.passed ? 'SkillEvidence criada. A elegibilidade usa esta evidência interna.' : 'A nota mínima não foi atingida; seu histórico e o progresso de 50% foram preservados.'}</p>
              {error && <div className="learning-inline-error" role="alert">{error}</div>}
              <div className="learning-quiz-actions">
                {!result.passed && <button type="button" className="learning-secondary-action" onClick={retry}>Tentar novamente</button>}
                {result.passed && result.skill_evidence && (
                  <button type="button" className="learning-secondary-action" onClick={() => void requestBadge()} disabled={Boolean(result.badge)}>
                    {result.badge ? 'Solicitação SANDBOX registrada' : 'Consentir solicitação de badge'}
                  </button>
                )}
                <button type="button" className="learning-primary-action" onClick={back}>Voltar para a capacitação</button>
              </div>
              {result.badge && <p className="learning-sandbox-notice">SANDBOX — consentimento persistido; nenhuma publicação foi enviada ao Nostr.</p>}
            </div>
          )}
        </section>
      )}
    </main>
  )
}

export function LearningLessonScreen({
  api,
  navigate,
  courseId,
  lessonId,
}: {
  api: ApiClient
  navigate: (path: string) => void
  courseId: string
  lessonId: string
}) {
  const [state, setState] = useState<LoadState<{ lesson: LessonDetail; notes: string }>>({ status: 'loading' })
  const [notes, setNotes] = useState('')
  const [noteStatus, setNoteStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle')

  const load = useCallback(async () => {
    setState({ status: 'loading' })
    try {
      const [lesson, note] = await Promise.all([
        api(`/courses/${routeSegment(courseId)}/lessons/${routeSegment(lessonId)}`),
        api(`/courses/${routeSegment(courseId)}/lessons/${routeSegment(lessonId)}/notes`),
      ])
      const content = typeof note.content === 'string' ? note.content : ''
      setNotes(content)
      setState({ status: 'ready', data: { lesson, notes: content } })
    } catch (error) {
      setState({ status: 'error', code: errorStatus(error) })
    }
  }, [api, courseId, lessonId])

  useEffect(() => {
    void load()
  }, [load])

  async function saveNote() {
    if (noteStatus === 'saving' || notes.length > 10000) return
    setNoteStatus('saving')
    try {
      await api(`/courses/${routeSegment(courseId)}/lessons/${routeSegment(lessonId)}/notes`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: notes }),
      })
      setNoteStatus('saved')
    } catch {
      setNoteStatus('error')
    }
  }

  if (state.status === 'loading') {
    return <main className="learning-flow"><div className="learning-detail-skeleton" role="status">Carregando aula...</div></main>
  }
  if (state.status === 'error') {
    return <main className="learning-flow"><LearningLoadError code={state.code} retry={() => void load()} /></main>
  }

  const lesson = state.data.lesson
  const activityId = lesson.activity_ids?.[0]

  return (
    <main className="learning-flow learning-lesson" aria-labelledby="lesson-title">
      <button className="learning-breadcrumb" type="button" onClick={() => navigate(`/app/capacitacao/${routeSegment(courseId)}`)}>
        <ArrowLeft aria-hidden="true" /> Voltar para a capacitação
      </button>
      <div className="learning-lesson-grid">
        <div>
          <span className="learning-kicker">{lesson.module_id} · Aula</span>
          <h1 id="lesson-title">{lesson.title}</h1>
          <p className="learning-lead">Estude o conteúdo disponível, registre suas anotações e siga para a atividade.</p>

          <section className="learning-media-empty" aria-labelledby="lesson-content-status">
            <BookOpen aria-hidden="true" />
            <div>
              <h2 id="lesson-content-status">Conteúdo multimídia não disponibilizado</h2>
              <p>A API atual ainda não fornece vídeo, texto da aula ou materiais de apoio. Nenhum conteúdo fictício foi exibido.</p>
            </div>
          </section>

          <div className="learning-lesson-actions">
            <button type="button" onClick={() => navigate(`/app/capacitacao/${routeSegment(courseId)}`)}><ArrowLeft aria-hidden="true" /> Trilha</button>
            <button
              type="button"
              className="is-primary"
              disabled={!activityId}
              onClick={() => activityId && navigate(`/app/capacitacao/${routeSegment(courseId)}/atividades/${routeSegment(activityId)}`)}
            >
              Fazer atividade <ArrowRight aria-hidden="true" />
            </button>
          </div>

          <section className="learning-notes" aria-labelledby="lesson-notes-title">
            <div>
              <NotebookPen aria-hidden="true" />
              <div><h2 id="lesson-notes-title">Minhas anotações</h2><p>Suas anotações ficam armazenadas no Bluejet.</p></div>
            </div>
            <label htmlFor="lesson-notes">Anotação da aula</label>
            <textarea
              id="lesson-notes"
              value={notes}
              maxLength={10000}
              onChange={event => { setNotes(event.target.value); setNoteStatus('idle') }}
              placeholder="Escreva aqui os pontos mais importantes da aula..."
            />
            <div className="learning-note-footer">
              <span>{notes.length}/10000</span>
              <button type="button" disabled={noteStatus === 'saving'} onClick={() => void saveNote()}>
                {noteStatus === 'saving' ? 'Salvando...' : 'Salvar anotações'}
              </button>
            </div>
            {noteStatus === 'saved' && <p className="learning-inline-success" role="status">Anotação salva.</p>}
            {noteStatus === 'error' && <p className="learning-inline-error" role="alert">Não foi possível salvar. Tente novamente.</p>}
          </section>
        </div>

        <aside className="learning-lesson-sidebar" aria-labelledby="lesson-module-title">
          <header><span>Conteúdo do módulo</span><h2 id="lesson-module-title">Aula atual</h2></header>
          <div className="learning-sidebar-item is-active">
            <CheckCircle2 aria-hidden="true" />
            <span><strong>{lesson.title}</strong><small>Status: {lesson.status}</small></span>
          </div>
          {activityId && (
            <button type="button" className="learning-sidebar-item" onClick={() => navigate(`/app/capacitacao/${routeSegment(courseId)}/atividades/${routeSegment(activityId)}`)}>
              <FileText aria-hidden="true" />
              <span><strong>Atividade prática</strong><small>Entrega textual</small></span>
            </button>
          )}
          <div className="learning-materials-unavailable">
            <Paperclip aria-hidden="true" />
            <div><strong>Materiais de apoio</strong><p>Não fornecidos pela API.</p></div>
          </div>
        </aside>
      </div>
    </main>
  )
}

export function LearningActivityScreen({
  api,
  navigate,
  courseId,
  activityId,
}: {
  api: ApiClient
  navigate: (path: string) => void
  courseId: string
  activityId: string
}) {
  const [state, setState] = useState<LoadState<ActivityDetail>>({ status: 'loading' })
  const [content, setContent] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState('')

  const load = useCallback(async () => {
    setState({ status: 'loading' })
    try {
      const activity = await api(`/courses/${routeSegment(courseId)}/activities/${routeSegment(activityId)}`)
      setState({ status: 'ready', data: activity })
    } catch (error) {
      setState({ status: 'error', code: errorStatus(error) })
    }
  }, [activityId, api, courseId])

  useEffect(() => {
    void load()
  }, [load])

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (submitting) return
    const normalized = content.trim()
    if (!normalized) {
      setFormError('Escreva sua atividade antes de enviar.')
      return
    }
    if (normalized.length > 20000) {
      setFormError('A atividade deve ter no máximo 20000 caracteres.')
      return
    }
    setSubmitting(true)
    setFormError('')
    try {
      await api(`/courses/${routeSegment(courseId)}/activities/${routeSegment(activityId)}/submissions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: normalized }),
      })
      navigate(`/app/capacitacao/${routeSegment(courseId)}?atividade=enviada`)
    } catch (error) {
      setFormError(errorStatus(error) === 409 ? 'Esta atividade já foi enviada.' : 'Não foi possível enviar. Tente novamente.')
    } finally {
      setSubmitting(false)
    }
  }

  if (state.status === 'loading') {
    return <main className="learning-flow"><div className="learning-detail-skeleton" role="status">Carregando atividade...</div></main>
  }
  if (state.status === 'error') {
    return <main className="learning-flow"><LearningLoadError code={state.code} retry={() => void load()} /></main>
  }

  const activity = state.data
  return (
    <main className="learning-flow learning-activity" aria-labelledby="activity-title">
      <button className="learning-breadcrumb" type="button" onClick={() => navigate(`/app/capacitacao/${routeSegment(courseId)}/aulas/${routeSegment(activity.lesson_id)}`)}>
        <ArrowLeft aria-hidden="true" /> Voltar para a aula
      </button>
      <span className="learning-kicker">Atividade · {activity.module_id}</span>
      <h1 id="activity-title">{activity.title}</h1>
      <p className="learning-lead">Registre o que você aprendeu e envie sua entrega para concluir esta etapa.</p>

      <div className="learning-activity-grid">
        <section className="learning-activity-brief" aria-labelledby="activity-info-title">
          <h2 id="activity-info-title">Informações da atividade</h2>
          <dl>
            <div><dt>Status</dt><dd>{activity.status}</dd></div>
            <div><dt>Curso</dt><dd>{activity.course_id}</dd></div>
            <div><dt>Aula</dt><dd>{activity.lesson_id}</dd></div>
          </dl>
          <div className="learning-contract-gap">
            <FileText aria-hidden="true" />
            <div><strong>Instruções detalhadas indisponíveis</strong><p>Prazo, critérios e materiais ainda não são fornecidos pelo contrato da API.</p></div>
          </div>
          <div className="learning-contract-gap">
            <Paperclip aria-hidden="true" />
            <div><strong>Anexos indisponíveis nesta fase</strong><p>Esta entrega aceita somente texto. Nenhum arquivo será enviado ao Storage.</p></div>
          </div>
        </section>

        <form className="learning-submission" onSubmit={event => void submit(event)}>
          <span className="learning-kicker">Sua entrega</span>
          <h2>Enviar atividade</h2>
          <label htmlFor="activity-content">Resposta</label>
          <textarea
            id="activity-content"
            value={content}
            aria-describedby="activity-help activity-count"
            onChange={event => { setContent(event.target.value); setFormError('') }}
            placeholder="Descreva sua solução, aprendizado e principais decisões..."
          />
          <div className="learning-submission-meta">
            <small id="activity-help">Somente texto, sem informações pessoais.</small>
            <span id="activity-count" className={content.length > 20000 ? 'is-invalid' : ''}>{content.length}/20000</span>
          </div>
          {formError && <div className="learning-inline-error" role="alert">{formError}</div>}
          <div className="learning-submit-actions">
            <button type="button" disabled title="Rascunhos ainda não são suportados pela API"><RotateCcw aria-hidden="true" /> Salvar rascunho</button>
            <button type="submit" className="is-primary" disabled={submitting}>
              {submitting ? 'Enviando...' : 'Enviar atividade'} <ArrowRight aria-hidden="true" />
            </button>
          </div>
          <p className="learning-disabled-note">Rascunho e upload permanecem desabilitados até existir contrato backend.</p>
        </form>
      </div>
    </main>
  )
}
