import {
  BookOpen,
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  Flag,
  Heart,
  Image as ImageIcon,
  MapPin,
  MessageCircle,
  Search,
  ShieldCheck,
  Sparkles,
  X,
} from 'lucide-react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

export type ApiClient = (path: string, options?: RequestInit) => Promise<any>
type Navigate = (path: string) => void

type CommunityPost = {
  id: string
  author_pubkey?: string
  category: 'learning' | 'question' | 'achievement'
  content: string
  created_at?: string
  moderation_status?: string
  delivery?: string
}

type OpportunityListing = {
  id: string
  type: 'EXTERNAL_OPPORTUNITY'
  publisher_pubkey?: string
  title: string
  description: string
  category: string
  organization_name: string
  external_url: string
  format: 'ONLINE' | 'ONSITE' | 'HYBRID'
  location?: string | null
  starts_at: string
  application_deadline?: string | null
  tags?: string[]
  requirements?: string
  moderation_status?: string
}

type PaidTask = {
  id: string
  type: 'PAID_TASK'
  title: string
  instructions?: string
  reward_sats?: number
  company?: { name?: string }
}

const categories = [
  { value: '', label: 'Todos' },
  { value: 'learning', label: 'Aprendizado' },
  { value: 'question', label: 'Dúvidas' },
  { value: 'achievement', label: 'Conquistas' },
] as const

const reportCategories = [
  ['SPAM', 'Spam'],
  ['FRAUD', 'Fraude'],
  ['PERSONAL_DATA', 'Dados pessoais'],
  ['HARASSMENT', 'Assédio'],
  ['MISLEADING_CONTENT', 'Conteúdo enganoso'],
  ['MALICIOUS_LINK', 'Link malicioso'],
  ['OUT_OF_SCOPE', 'Fora do escopo'],
  ['OTHER', 'Outro'],
] as const

const opportunityTypes = [
  ['HACKATHON', 'Hackathon'],
  ['FREE_COURSE', 'Curso gratuito'],
  ['EVENT', 'Evento'],
  ['TALK', 'Palestra'],
  ['MEETUP', 'Encontro'],
  ['MENTORSHIP', 'Mentoria'],
  ['EDUCATIONAL_PROGRAM', 'Programa educacional'],
  ['OTHER', 'Outro'],
] as const

const typeLabels = Object.fromEntries(opportunityTypes)
const formatLabels = { ONLINE: 'Online', ONSITE: 'Presencial', HYBRID: 'Híbrido' }
const categoryLabels: Record<string, string> = {
  learning: 'Aprendizado',
  question: 'Dúvida',
  achievement: 'Conquista',
}

function errorStatus(error: unknown) {
  return (error as Error & { status?: number })?.status
}

function randomIdempotencyKey(prefix: string) {
  const suffix = globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random()}`
  return `${prefix}-${suffix}`
}

export function safeExternalUrl(value: string) {
  try {
    const url = new URL(value)
    const supportedProtocol = url.protocol === 'http:' || url.protocol === 'https:'
    return supportedProtocol && url.hostname && !url.username && !url.password ? url.href : null
  } catch {
    return null
  }
}

function shortIdentity(value?: string) {
  if (!value) return 'Participante da comunidade'
  return `${value.slice(0, 8)}…${value.slice(-6)}`
}

function dateLabel(value?: string | null) {
  if (!value) return 'Data não informada'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'Data não informada'
  return new Intl.DateTimeFormat('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' }).format(date)
}

function relativeTime(value?: string) {
  if (!value) return 'agora'
  const diff = Math.max(0, Date.now() - new Date(value).getTime())
  const minutes = Math.floor(diff / 60_000)
  if (minutes < 1) return 'agora'
  if (minutes < 60) return `há ${minutes} min`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `há ${hours} h`
  return dateLabel(value)
}

function Phase8State({ children, role = 'status' }: { children: React.ReactNode; role?: 'status' | 'alert' }) {
  return <div className="phase8-state" role={role}>{children}</div>
}

function ApiFailure({ error, retry, navigate }: { error: unknown; retry: () => void; navigate: Navigate }) {
  const status = errorStatus(error)
  if (status === 401) {
    return <Phase8State role="alert">Sua sessão expirou. <button onClick={() => navigate(`/entrar?returnTo=${encodeURIComponent(location.pathname + location.search)}`)}>Entrar novamente</button></Phase8State>
  }
  if (status === 403) return <Phase8State role="alert">Você não tem permissão para acessar este conteúdo.</Phase8State>
  return <Phase8State role="alert">Não foi possível carregar os dados. <button onClick={retry}>Tentar novamente</button></Phase8State>
}

function ReportDialog({
  subjectType,
  subjectId,
  api,
  onClose,
}: {
  subjectType: 'POST' | 'OPPORTUNITY'
  subjectId: string
  api: ApiClient
  onClose: () => void
}) {
  const [category, setCategory] = useState('')
  const [details, setDetails] = useState('')
  const [status, setStatus] = useState<'idle' | 'saving' | 'sent'>('idle')
  const [error, setError] = useState('')
  async function submit(event: React.FormEvent) {
    event.preventDefault()
    if (!category) return setError('Selecione o motivo da denúncia.')
    if (category === 'OTHER' && !details.trim()) return setError('Descreva o motivo quando escolher Outro.')
    setStatus('saving')
    setError('')
    try {
      await api('/community/reports', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ subject_type: subjectType, subject_id: subjectId, category, details: details.trim() }),
      })
      setStatus('sent')
    } catch (caught) {
      setError(errorStatus(caught) === 409 ? 'Você já denunciou este conteúdo.' : 'Não foi possível enviar a denúncia.')
      setStatus('idle')
    }
  }
  return <div className="phase8-dialog-backdrop" role="presentation" onMouseDown={event => event.target === event.currentTarget && onClose()}>
    <section className="phase8-dialog" role="dialog" aria-modal="true" aria-labelledby={`report-title-${subjectId}`}>
      <button className="phase8-icon-button dialog-close" aria-label="Fechar denúncia" onClick={onClose}><X size={20}/></button>
      {status === 'sent' ? <>
        <h2 id={`report-title-${subjectId}`}>Denúncia recebida</h2>
        <p>O conteúdo não foi apagado nem ocultado automaticamente. A moderação analisará o caso.</p>
        <button className="phase8-primary" onClick={onClose}>Concluir</button>
      </> : <form onSubmit={submit}>
        <h2 id={`report-title-${subjectId}`}>Denunciar conteúdo</h2>
        <p>Informe o motivo para que a equipe de moderação possa avaliar.</p>
        <label>Motivo
          <select value={category} onChange={event => setCategory(event.target.value)}>
            <option value="">Selecione</option>
            {reportCategories.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
        </label>
        <label>Detalhes {category === 'OTHER' ? '(obrigatório)' : '(opcional)'}
          <textarea maxLength={1000} value={details} onChange={event => setDetails(event.target.value)} />
        </label>
        {error && <p className="phase8-error" role="alert">{error}</p>}
        <div className="phase8-actions">
          <button type="button" className="phase8-secondary" onClick={onClose}>Cancelar</button>
          <button className="phase8-primary" disabled={status === 'saving'}>{status === 'saving' ? 'Enviando…' : 'Enviar denúncia'}</button>
        </div>
      </form>}
    </section>
  </div>
}

function PostCard({ post, api }: { post: CommunityPost; api: ApiClient }) {
  const [reporting, setReporting] = useState(false)
  const [reacted, setReacted] = useState(false)
  const [reactionError, setReactionError] = useState('')
  async function react() {
    setReactionError('')
    try {
      const response = await api(`/community/posts/${post.id}/reactions`, { method: 'POST' })
      setReacted(Boolean(response.active))
    } catch {
      setReactionError('A reação não foi registrada.')
    }
  }
  return <article className="phase8-card community-post">
    <header className="post-author">
      <span className="post-avatar" aria-hidden="true">{shortIdentity(post.author_pubkey).slice(0, 1).toUpperCase()}</span>
      <div><strong>{shortIdentity(post.author_pubkey)}</strong><span>{categoryLabels[post.category] ?? post.category} · {relativeTime(post.created_at)}</span></div>
      <span className="local-status">{post.delivery ?? 'LOCAL_ONLY'}</span>
    </header>
    <p className="post-content">{post.content}</p>
    <div className="post-actions" aria-label="Ações da publicação">
      <button aria-pressed={reacted} onClick={react}><Heart size={19} fill={reacted ? 'currentColor' : 'none'}/> {reacted ? 'Curtido' : 'Curtir'}</button>
      <button disabled title="Comentários ainda não disponíveis neste feed"><MessageCircle size={19}/> Comentar</button>
      <button onClick={() => setReporting(true)}><Flag size={18}/> Denunciar</button>
    </div>
    {reactionError && <p className="phase8-error" role="alert">{reactionError}</p>}
    {reporting && <ReportDialog subjectType="POST" subjectId={post.id} api={api} onClose={() => setReporting(false)}/>}
  </article>
}

function CommunityComposer({ api, onCreated }: { api: ApiClient; onCreated: () => Promise<void> }) {
  const [expanded, setExpanded] = useState(false)
  const [category, setCategory] = useState<CommunityPost['category']>('learning')
  const [content, setContent] = useState('')
  const [acknowledged, setAcknowledged] = useState(false)
  const [status, setStatus] = useState<'idle' | 'saving'>('idle')
  const [message, setMessage] = useState('')
  const inFlight = useRef(false)
  const idempotency = useRef(randomIdempotencyKey('community-post'))
  async function publish(event: React.FormEvent) {
    event.preventDefault()
    if (inFlight.current) return
    if (!content.trim()) return setMessage('Escreva uma publicação antes de enviar.')
    if (content.trim().length > 2000) return setMessage('A publicação deve ter no máximo 2.000 caracteres.')
    if (!acknowledged) return setMessage('Confirme o aviso de privacidade antes de publicar.')
    inFlight.current = true
    setStatus('saving')
    setMessage('')
    try {
      await api('/community/posts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Idempotency-Key': idempotency.current },
        body: JSON.stringify({ category, content: content.trim(), public_acknowledged: true }),
      })
      setContent('')
      setAcknowledged(false)
      setExpanded(false)
      idempotency.current = randomIdempotencyKey('community-post')
      await onCreated()
      setMessage('Publicação salva no Bluejet como LOCAL_ONLY.')
    } catch (error) {
      setMessage(errorStatus(error) === 403 ? 'Você não tem permissão para publicar.' : 'Não foi possível publicar. Tente novamente.')
    } finally {
      inFlight.current = false
      setStatus('idle')
    }
  }
  return <section className={`phase8-card community-composer ${expanded ? 'expanded' : ''}`} aria-label="Criar publicação">
    {!expanded ? <button className="composer-trigger" onClick={() => { setExpanded(true); setMessage('') }}>
      <span className="post-avatar" aria-hidden="true">U</span>
      <span>Compartilhe algo com a comunidade…</span>
    </button> : <form onSubmit={publish}>
      <div className="composer-heading"><div><span className="phase8-eyebrow">Nova publicação</span><h2>Compartilhe com a comunidade</h2></div><button type="button" className="phase8-icon-button" aria-label="Cancelar publicação" onClick={() => { setExpanded(false); setMessage('') }}><X size={20}/></button></div>
      <fieldset className="post-type-picker"><legend>Tipo de publicação</legend>{categories.slice(1).map(item => <label key={item.value}><input type="radio" name="post-type" value={item.value} checked={category === item.value} onChange={() => setCategory(item.value as CommunityPost['category'])}/><span>{item.label}</span></label>)}</fieldset>
      <label className="sr-only" htmlFor="community-post-content">Conteúdo da publicação</label>
      <textarea id="community-post-content" autoFocus maxLength={2000} value={content} onChange={event => setContent(event.target.value)} placeholder="O que você quer compartilhar?"/>
      <div className="character-count">{content.length}/2000</div>
      <div className="privacy-warning"><ShieldCheck size={20}/><p>Esta publicação será armazenada no Bluejet. A integração com relays públicos do Nostr está desabilitada neste ambiente. Não publique documentos, endereços, dados financeiros ou outras informações pessoais.</p></div>
      <label className="phase8-check"><input type="checkbox" checked={acknowledged} onChange={event => setAcknowledged(event.target.checked)}/> Li e compreendi o aviso de privacidade.</label>
      <div className="composer-footer"><button type="button" disabled aria-disabled="true" title="Mídia indisponível nesta fase"><ImageIcon size={19}/> Mídia <small>Em breve</small></button><button className="phase8-primary" disabled={status === 'saving'}>{status === 'saving' ? 'Publicando…' : 'Publicar'}</button></div>
    </form>}
    {message && <p className={message.includes('LOCAL_ONLY') ? 'phase8-success' : 'phase8-error'} role="status">{message}</p>}
  </section>
}

function ModerationPanel({ api }: { api: ApiClient }) {
  const [items, setItems] = useState<any[]>([])
  const [reason, setReason] = useState<Record<string, string>>({})
  const [error, setError] = useState('')
  const load = useCallback(async () => {
    try {
      const response = await api('/admin/community/moderation-queue')
      setItems(response.items ?? [])
    } catch {
      setError('Não foi possível atualizar a moderação.')
    }
  }, [api])
  useEffect(() => { void load() }, [load])
  async function decide(item: any, action: 'HIDE' | 'RESTORE' | 'KEEP') {
    const justification = reason[item.subject_id]?.trim()
    if (!justification) return setError('Toda decisão de moderação exige justificativa.')
    setError('')
    try {
      await api('/admin/moderation-decisions', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ subject_type: item.subject_type, subject_id: item.subject_id, action, reason: justification }),
      })
      await load()
    } catch (caught) {
      setError(errorStatus(caught) === 422 ? 'A decisão foi recusada. A autoria e a justificativa são validadas pelo servidor.' : 'Não foi possível registrar a decisão.')
    }
  }
  return <section className="phase8-card moderation-panel"><span className="phase8-eyebrow">Acesso autorizado</span><h2>Moderação</h2>{error && <p className="phase8-error" role="alert">{error}</p>}{items.length ? items.slice(0, 5).map(item => <article key={`${item.subject_type}-${item.subject_id}`}>
    <strong>{item.subject_type === 'POST' ? 'Publicação' : 'Oportunidade'}</strong><p>{item.report_count} denúncia(s) · {item.moderation_status}</p>
    <label>Justificativa<textarea value={reason[item.subject_id] ?? ''} onChange={event => setReason(current => ({ ...current, [item.subject_id]: event.target.value }))}/></label>
    <div className="moderation-actions"><button onClick={() => decide(item, 'KEEP')}>Manter</button><button onClick={() => decide(item, item.moderation_status === 'HIDDEN' ? 'RESTORE' : 'HIDE')}>{item.moderation_status === 'HIDDEN' ? 'Restaurar' : 'Ocultar'}</button></div>
  </article>) : <p className="phase8-muted">Nenhum conteúdo aguarda decisão.</p>}</section>
}

export function CommunityScreen({ api, navigate }: { api: ApiClient; navigate: Navigate }) {
  const [category, setCategory] = useState('')
  const [feed, setFeed] = useState<{ items: CommunityPost[]; next: number | null; loading: boolean; error?: unknown }>({ items: [], next: 0, loading: true })
  const [course, setCourse] = useState<any>(null)
  const [canModerate, setCanModerate] = useState(false)
  const load = useCallback(async (offset = 0) => {
    setFeed(current => ({ ...current, loading: true, error: undefined }))
    try {
      const query = new URLSearchParams({ limit: '20', offset: String(offset) })
      if (category) query.set('category', category)
      const response = await api(`/community/feed?${query}`)
      setFeed(current => ({ items: offset ? [...current.items, ...response.items] : response.items, next: response.next_offset, loading: false }))
    } catch (error) {
      setFeed(current => ({ ...current, loading: false, error }))
    }
  }, [api, category])
  useEffect(() => { void load(0) }, [load])
  useEffect(() => {
    api('/courses').then(response => setCourse(response.items?.[0] ?? null)).catch(() => setCourse(null))
    api('/me').then(response => setCanModerate(
      Array.isArray(response.roles) && response.roles.some((role: string) => role === 'ADMIN' || role === 'REVIEWER'),
    )).catch(() => setCanModerate(false))
  }, [api])
  return <main className="phase8-page community-page">
    <h1 className="sr-only">Comunidade</h1>
    <div className="community-layout">
      <aside className="community-sidebar" aria-label="Categorias da comunidade">
        <h2>Categorias</h2>
        {categories.map(item => <button key={item.value || 'all'} className={category === item.value ? 'active' : ''} aria-pressed={category === item.value} onClick={() => setCategory(item.value)}>{item.value === 'learning' ? <BookOpen size={18}/> : item.value === 'achievement' ? <Sparkles size={18}/> : item.value === 'question' ? <MessageCircle size={18}/> : <span aria-hidden="true">✦</span>}{item.label}</button>)}
      </aside>
      <section className="community-feed" aria-label="Publicações da comunidade">
        <CommunityComposer api={api} onCreated={() => load(0)}/>
        {feed.loading && !feed.items.length ? <Phase8State>Carregando publicações…</Phase8State> : feed.error ? <ApiFailure error={feed.error} retry={() => load(0)} navigate={navigate}/> : feed.items.length ? feed.items.map(post => <PostCard key={post.id} post={post} api={api}/>) : <Phase8State>Ainda não há publicações nesta categoria.</Phase8State>}
        {feed.loading && feed.items.length > 0 && <p className="phase8-muted" role="status">Carregando mais…</p>}
        {!feed.loading && feed.next !== null && <button className="load-more" onClick={() => load(feed.next!)}>Carregar mais publicações</button>}
      </section>
      <aside className="community-rail">
        <section className="phase8-card trends-card"><h2>Assuntos em alta</h2><p className="phase8-muted">As tendências ainda não possuem dados suficientes.</p></section>
        <section className="phase8-card learning-card"><span className="phase8-eyebrow">Capacitação</span>{course ? <><h2>{course.title}</h2><p>{course.objective}</p><button onClick={() => navigate(`/app/capacitacao/${course.id}`)}>Ver trilha <ChevronRight size={17}/></button></> : <p className="phase8-muted">Nenhuma capacitação disponível agora.</p>}</section>
        {canModerate && <ModerationPanel api={api}/>}
      </aside>
    </div>
  </main>
}

function ExternalOpportunityCard({ item, api, navigate }: { item: OpportunityListing; api: ApiClient; navigate: Navigate }) {
  const [reporting, setReporting] = useState(false)
  return <article className="phase8-card opportunity-card external-listing">
    <div className="opportunity-card-top"><span className="external-badge">Oportunidade externa</span><button className="phase8-icon-button" aria-label={`Denunciar ${item.title}`} onClick={() => setReporting(true)}><Flag size={18}/></button></div>
    <p className="no-payment">Sem pagamento processado pelo Bluejet</p>
    <h2>{item.title}</h2>
    <p className="opportunity-organizer">{item.organization_name}</p>
    <div className="opportunity-meta"><span><CalendarDays size={17}/>{dateLabel(item.starts_at)}</span><span><MapPin size={17}/>{formatLabels[item.format]}{item.location ? ` · ${item.location}` : ''}</span></div>
    {!!item.tags?.length && <div className="tag-list">{item.tags.map(tag => <span key={tag}>#{tag}</span>)}</div>}
    <button className="phase8-primary" onClick={() => navigate(`/app/oportunidades/externas/${item.id}`)}>Ver detalhes</button>
    {reporting && <ReportDialog subjectType="OPPORTUNITY" subjectId={item.id} api={api} onClose={() => setReporting(false)}/>}
  </article>
}

function PaidTaskCard({ item, navigate }: { item: PaidTask; navigate: Navigate }) {
  return <article className="phase8-card opportunity-card paid-task-card">
    <span className="paid-badge">Tarefa remunerada</span><h2>{item.title}</h2><p>{item.company?.name ?? 'Organização contratante'}</p><strong>{item.reward_sats ? `${item.reward_sats} sats` : 'Valor definido pela organização'}</strong><button className="phase8-primary" onClick={() => navigate(`/app/oportunidades/${item.id}`)}>Ver tarefa</button>
  </article>
}

export function OpportunitiesScreen({ api, navigate, query }: { api: ApiClient; navigate: Navigate; query: URLSearchParams }) {
  const tab = query.get('tipo') === 'remuneradas' ? 'paid' : 'external'
  const [search, setSearch] = useState(query.get('busca') ?? '')
  const [state, setState] = useState<{ external: OpportunityListing[]; paid: PaidTask[]; loading: boolean; error?: unknown }>({ external: [], paid: [], loading: true })
  const load = useCallback(async () => {
    setState(current => ({ ...current, loading: true, error: undefined }))
    try {
      const response = await api('/opportunities')
      setState({ external: response.external_opportunities ?? [], paid: response.paid_tasks ?? [], loading: false })
    } catch (error) { setState(current => ({ ...current, loading: false, error })) }
  }, [api])
  useEffect(() => { void load() }, [load])
  const items = useMemo(() => {
    const needle = search.trim().toLocaleLowerCase('pt-BR')
    const source = tab === 'external' ? state.external : state.paid
    return needle ? source.filter(item => `${item.title} ${'organization_name' in item ? item.organization_name : item.company?.name ?? ''}`.toLocaleLowerCase('pt-BR').includes(needle)) : source
  }, [search, state, tab])
  function changeTab(value: 'external' | 'paid') {
    const next = new URLSearchParams(query)
    if (value === 'paid') next.set('tipo', 'remuneradas'); else next.delete('tipo')
    navigate(`/app/oportunidades${next.size ? `?${next}` : ''}`)
  }
  return <main className="phase8-page opportunities-page">
    <header className="opportunities-heading"><div><span className="phase8-eyebrow">Descubra novas possibilidades</span><h1>Oportunidades</h1><p>Iniciativas externas compartilhadas pela comunidade e tarefas profissionais remuneradas.</p></div>{tab === 'external' && <button className="phase8-primary" onClick={() => navigate('/app/oportunidades/nova/basico')}>Publicar oportunidade</button>}</header>
    {query.get('publicada') === '1' && <p className="opportunity-published" role="status">Oportunidade externa publicada e adicionada ao feed.</p>}
    <div className="opportunity-tabs" role="tablist" aria-label="Tipos de oportunidade"><button role="tab" aria-selected={tab === 'external'} className={tab === 'external' ? 'active' : ''} onClick={() => changeTab('external')}>Oportunidades externas</button><button role="tab" aria-selected={tab === 'paid'} className={tab === 'paid' ? 'active' : ''} onClick={() => changeTab('paid')}>Tarefas remuneradas</button></div>
    <label className="opportunity-search"><Search size={19}/><span className="sr-only">Buscar oportunidades</span><input value={search} onChange={event => setSearch(event.target.value)} placeholder="Buscar por título ou organização"/></label>
    {tab === 'external' && <div className="external-explainer"><ExternalLink size={21}/><div><strong>Oportunidades externas</strong><p>São apenas divulgações comunitárias. O Bluejet não processa pagamento, seleção ou certificado.</p></div></div>}
    {state.loading ? <Phase8State>Carregando oportunidades…</Phase8State> : state.error ? <ApiFailure error={state.error} retry={load} navigate={navigate}/> : items.length ? <div className="opportunity-grid">{tab === 'external' ? (items as OpportunityListing[]).map(item => <ExternalOpportunityCard key={item.id} item={item} api={api} navigate={navigate}/>) : (items as PaidTask[]).map(item => <PaidTaskCard key={item.id} item={item} navigate={navigate}/>)}</div> : <Phase8State>{search ? 'Nenhum resultado para sua busca.' : tab === 'external' ? 'Nenhuma oportunidade externa publicada.' : 'Nenhuma tarefa remunerada disponível.'}</Phase8State>}
  </main>
}

export function ExternalOpportunityDetailScreen({ api, navigate, id }: { api: ApiClient; navigate: Navigate; id: string }) {
  const [state, setState] = useState<{ loading: boolean; item?: OpportunityListing; error?: unknown }>({ loading: true })
  const [reporting, setReporting] = useState(false)
  const load = useCallback(async () => { setState({ loading: true }); try { setState({ loading: false, item: await api(`/opportunities/external/${id}`) }) } catch (error) { setState({ loading: false, error }) } }, [api, id])
  useEffect(() => { void load() }, [load])
  if (state.loading) return <main className="phase8-page"><Phase8State>Carregando oportunidade…</Phase8State></main>
  if (state.error || !state.item) return <main className="phase8-page"><ApiFailure error={state.error} retry={load} navigate={navigate}/></main>
  const item = state.item
  const safeUrl = safeExternalUrl(item.external_url)
  return <main className="phase8-page opportunity-detail-page">
    <button className="back-link" onClick={() => navigate('/app/oportunidades')}><ChevronLeft size={19}/> Voltar para oportunidades</button>
    <article className="phase8-card opportunity-detail">
      <div className="opportunity-card-top"><span className="external-badge">Oportunidade externa</span><button className="phase8-secondary report-button" onClick={() => setReporting(true)}><Flag size={17}/> Denunciar</button></div>
      <p className="no-payment">Sem pagamento processado pelo Bluejet</p>
      <h1>{item.title}</h1><p className="detail-description">{item.description}</p>
      <div className="detail-grid"><section><span>Divulgada por</span><strong>{shortIdentity(item.publisher_pubkey)}</strong></section><section><span>Organizador externo</span><strong>{item.organization_name}</strong></section><section><span>Formato e local</span><strong>{formatLabels[item.format]}{item.location ? ` · ${item.location}` : ''}</strong></section><section><span>Data de início</span><strong>{dateLabel(item.starts_at)}</strong></section>{item.application_deadline && <section><span>Inscrições até</span><strong>{dateLabel(item.application_deadline)}</strong></section>}<section><span>Tipo</span><strong>{typeLabels[item.category] ?? item.category}</strong></section></div>
      {item.requirements && <section className="detail-section"><h2>Requisitos informativos</h2><p>{item.requirements}</p></section>}
      {!!item.tags?.length && <div className="tag-list">{item.tags.map(tag => <span key={tag}>#{tag}</span>)}</div>}
      <div className="external-origin"><strong>Origem externa</strong><span>{safeUrl ? new URL(safeUrl).hostname : 'URL inválida'}</span><p>O Bluejet não garante seleção, participação, certificado ou condições oferecidas pelo organizador.</p></div>
      {safeUrl ? <a className="phase8-primary external-cta" href={safeUrl} target="_blank" rel="noopener noreferrer">Acessar oportunidade externa <ExternalLink size={18}/></a> : <button className="phase8-primary" disabled>URL externa indisponível</button>}
      {reporting && <ReportDialog subjectType="OPPORTUNITY" subjectId={item.id} api={api} onClose={() => setReporting(false)}/>}
    </article>
  </main>
}

type ListingDraft = {
  title: string
  description: string
  category: string
  organization_name: string
  external_url: string
  format: 'ONLINE' | 'ONSITE' | 'HYBRID'
  location: string
  starts_at: string
  application_deadline: string
  tags: string
  requirements: string
  non_remunerated_ack: boolean
  review_ack: boolean
  idempotency_key: string
}

const draftKey = 'bluejet_external_opportunity_draft_v1'
const blankDraft = (): ListingDraft => ({ title: '', description: '', category: 'HACKATHON', organization_name: '', external_url: '', format: 'ONLINE', location: '', starts_at: '', application_deadline: '', tags: '', requirements: '', non_remunerated_ack: false, review_ack: false, idempotency_key: randomIdempotencyKey('opportunity-listing') })

function loadDraft(): ListingDraft {
  try { return { ...blankDraft(), ...JSON.parse(localStorage.getItem(draftKey) ?? '{}') } } catch { return blankDraft() }
}

export function OpportunityListingWizard({ api, navigate, step }: { api: ApiClient; navigate: Navigate; step: string }) {
  const normalizedStep = step === 'midia' ? 'origem' : ['basico', 'requisitos', 'origem', 'revisao'].includes(step) ? step : 'basico'
  const [draft, setDraft] = useState<ListingDraft>(loadDraft)
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const inFlight = useRef(false)
  const steps = ['basico', 'requisitos', 'origem', 'revisao']
  const index = steps.indexOf(normalizedStep)
  function update<K extends keyof ListingDraft>(key: K, value: ListingDraft[K]) {
    const next = { ...draft, [key]: value }
    setDraft(next)
    localStorage.setItem(draftKey, JSON.stringify(next))
  }
  function validateCurrent() {
    if (normalizedStep === 'basico' && (!draft.title.trim() || !draft.description.trim() || !draft.category)) return 'Informe título, descrição e tipo.'
    if (normalizedStep === 'requisitos') {
      if (!draft.starts_at) return 'Informe a data de início.'
      if (draft.format !== 'ONLINE' && !draft.location.trim()) return 'Informe a localização da oportunidade.'
      if (draft.application_deadline && new Date(draft.application_deadline) > new Date(draft.starts_at)) return 'O encerramento das inscrições não pode ocorrer depois do início.'
    }
    if (normalizedStep === 'origem') {
      if (!draft.organization_name.trim()) return 'Informe o organizador externo.'
      if (!safeExternalUrl(draft.external_url)) return 'Informe uma URL segura iniciada por http:// ou https://.'
      if (!draft.non_remunerated_ack) return 'Confirme que a oportunidade não possui remuneração pelo Bluejet.'
    }
    if (normalizedStep === 'revisao' && !draft.review_ack) return 'Confirme as responsabilidades antes de publicar.'
    return ''
  }
  async function next() {
    const validation = validateCurrent()
    if (validation) return setError(validation)
    setError('')
    if (index < 3) return navigate(`/app/oportunidades/nova/${steps[index + 1]}`)
    if (inFlight.current) return
    inFlight.current = true
    setSaving(true)
    try {
      await api('/opportunities/external', {
        method: 'POST', headers: { 'Content-Type': 'application/json', 'Idempotency-Key': draft.idempotency_key },
        body: JSON.stringify({
          title: draft.title.trim(), description: draft.description.trim(), category: draft.category,
          organization_name: draft.organization_name.trim(), external_url: draft.external_url.trim(), format: draft.format,
          location: draft.format === 'ONLINE' ? null : draft.location.trim(), starts_at: new Date(draft.starts_at).toISOString(),
          application_deadline: draft.application_deadline ? new Date(draft.application_deadline).toISOString() : null,
          tags: draft.tags.split(',').map(tag => tag.trim().replace(/^#/, '')).filter(Boolean).slice(0, 8),
          requirements: draft.requirements.trim(), non_remunerated_ack: true,
        }),
      })
      localStorage.removeItem(draftKey)
      navigate('/app/oportunidades?publicada=1')
    } catch (caught) {
      setError(errorStatus(caught) === 403 ? 'Seu perfil não pode publicar esta oportunidade.' : 'Não foi possível publicar. Revise os dados e tente novamente.')
    } finally { inFlight.current = false; setSaving(false) }
  }
  function back() { if (index === 0) navigate('/app/oportunidades'); else navigate(`/app/oportunidades/nova/${steps[index - 1]}`) }
  return <main className="phase8-page opportunity-wizard-page">
    <button className="back-link" onClick={back}><ChevronLeft size={19}/> Voltar</button>
    <div className="wizard-progress" aria-label={`Etapa ${index + 1} de 4`}><span>Etapa {String(index + 1).padStart(2, '0')} de 04</span><div>{steps.map((item, itemIndex) => <i key={item} className={itemIndex <= index ? 'active' : ''}/>)}</div></div>
    <section className="wizard-shell">
      <span className="phase8-eyebrow">Oportunidade comunitária</span>
      {normalizedStep === 'basico' && <><h1>Conte sobre a oportunidade</h1><p>Compartilhe uma iniciativa externa relevante para a comunidade.</p><label>Título<input autoFocus maxLength={140} value={draft.title} onChange={event => update('title', event.target.value)}/></label><label>Descrição<textarea maxLength={2000} value={draft.description} onChange={event => update('description', event.target.value)}/></label><label>Tipo<select value={draft.category} onChange={event => update('category', event.target.value)}>{opportunityTypes.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label></>}
      {normalizedStep === 'requisitos' && <><h1>Detalhes e requisitos</h1><p>Informe como e quando a iniciativa acontece.</p><div className="wizard-two-columns"><label>Formato<select value={draft.format} onChange={event => update('format', event.target.value as ListingDraft['format'])}><option value="ONLINE">Online</option><option value="ONSITE">Presencial</option><option value="HYBRID">Híbrido</option></select></label>{draft.format !== 'ONLINE' && <label>Localização<input value={draft.location} onChange={event => update('location', event.target.value)}/></label>}<label>Data de início<input type="datetime-local" value={draft.starts_at} onChange={event => update('starts_at', event.target.value)}/></label><label>Encerramento das inscrições<input type="datetime-local" value={draft.application_deadline} onChange={event => update('application_deadline', event.target.value)}/></label></div><label>Requisitos informativos<textarea value={draft.requirements} onChange={event => update('requirements', event.target.value)}/></label><label>Tags separadas por vírgula<input value={draft.tags} onChange={event => update('tags', event.target.value)} placeholder="tecnologia, mulheres, gratuito"/></label></>}
      {normalizedStep === 'origem' && <><h1>Origem e confirmação</h1><p>A oportunidade será acessada no site do organizador.</p><label>Organizador externo<input value={draft.organization_name} onChange={event => update('organization_name', event.target.value)}/></label><label>URL externa<input type="url" inputMode="url" value={draft.external_url} onChange={event => update('external_url', event.target.value)} placeholder="https://exemplo.org/oportunidade"/></label><div className="external-explainer"><ShieldCheck size={22}/><p>O Bluejet não processa pagamento, candidatura, entrega ou certificado nesta oportunidade.</p></div><label className="phase8-check"><input type="checkbox" checked={draft.non_remunerated_ack} onChange={event => update('non_remunerated_ack', event.target.checked)}/> Confirmo que esta oportunidade é externa e não remunerada pelo Bluejet.</label></>}
      {normalizedStep === 'revisao' && <><h1>Revisar e publicar</h1><p>Confira as informações antes de compartilhar.</p><div className="wizard-review"><ReviewSection title="Informações básicas" edit={() => navigate('/app/oportunidades/nova/basico')}><strong>{draft.title}</strong><p>{draft.description}</p><span>{typeLabels[draft.category]}</span></ReviewSection><ReviewSection title="Detalhes e requisitos" edit={() => navigate('/app/oportunidades/nova/requisitos')}><p>{formatLabels[draft.format]}{draft.location ? ` · ${draft.location}` : ''}</p><p>Início: {dateLabel(draft.starts_at)}</p><p>{draft.requirements || 'Sem requisitos adicionais.'}</p></ReviewSection><ReviewSection title="Origem" edit={() => navigate('/app/oportunidades/nova/origem')}><strong>{draft.organization_name}</strong><p className="review-url">{draft.external_url}</p></ReviewSection></div><div className="review-disclaimer"><strong>Esta é uma oportunidade externa e não remunerada pelo Bluejet.</strong><p>A participante atua somente como divulgadora.</p><p>O Bluejet não garante seleção, participação, certificado ou condições oferecidas pelo organizador.</p></div><label className="phase8-check"><input type="checkbox" checked={draft.review_ack} onChange={event => update('review_ack', event.target.checked)}/> Revisei a origem e confirmo que compreendo essas condições.</label></>}
      {error && <p className="phase8-error" role="alert">{error}</p>}
      <div className="wizard-actions"><button className="phase8-secondary" onClick={back}>Voltar</button><button className="phase8-primary" disabled={saving} onClick={next}>{saving ? 'Publicando…' : normalizedStep === 'revisao' ? 'Publicar oportunidade' : <>Continuar <ChevronRight size={18}/></>}</button></div>
    </section>
  </main>
}

function ReviewSection({ title, edit, children }: { title: string; edit: () => void; children: React.ReactNode }) {
  return <section><header><h2>{title}</h2><button onClick={edit}>Editar</button></header>{children}</section>
}
