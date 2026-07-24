import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import {
  CommunityScreen,
  ExternalOpportunityDetailScreen,
  OpportunitiesScreen,
  OpportunityListingWizard,
  safeExternalUrl,
  type ApiClient,
} from './phase8'

const post = {
  id: 'post-1', author_pubkey: 'a'.repeat(64), category: 'learning', content: 'Aprendi testes acessíveis.',
  created_at: '2026-07-24T10:00:00Z', moderation_status: 'VISIBLE', delivery: 'LOCAL_ONLY',
}

const listing = {
  id: 'listing-1', type: 'EXTERNAL_OPPORTUNITY', publisher_pubkey: 'b'.repeat(64), title: 'Hackathon aberto',
  description: 'Evento gratuito para a comunidade.', category: 'HACKATHON', organization_name: 'Instituto Aberto',
  external_url: 'https://example.org/hackathon', format: 'HYBRID', location: 'São Paulo',
  starts_at: '2026-09-20T12:00:00Z', application_deadline: '2026-09-10T12:00:00Z', tags: ['tecnologia'],
  requirements: 'Inscrição no site externo.', moderation_status: 'VISIBLE',
}

const paidTask = { id: 'task-1', type: 'PAID_TASK', title: 'Revisão de acessibilidade', instructions: 'Revisar uma tela.', reward_sats: 5000, company: { name: 'Empresa' } }

function apiForCommunity(items: any[] = [post]) {
  return vi.fn(async (path: string, options?: RequestInit) => {
    if (path.startsWith('/community/feed')) return { items, next_offset: null }
    if (path === '/courses') return { items: [] }
    if (path === '/me') return { roles: ['PARTICIPANT'] }
    if (path === '/admin/me') throw Object.assign(new Error('Forbidden'), { status: 403 })
    if (path === '/community/posts' && options?.method === 'POST') return { id: 'created' }
    if (path.endsWith('/reactions')) return { active: true }
    if (path === '/community/reports') return { id: 'report-1' }
    throw new Error(`Unexpected ${path}`)
  })
}

async function openComposer(user: ReturnType<typeof userEvent.setup>) {
  await user.click(await screen.findByRole('button', { name: /Compartilhe algo/i }))
}

async function fillAndPublishPost(api: ReturnType<typeof vi.fn>, type: 'Aprendizado' | 'Dúvidas' | 'Conquistas') {
  const user = userEvent.setup()
  render(<CommunityScreen api={api as ApiClient} navigate={vi.fn()}/>)
  await openComposer(user)
  await user.click(screen.getByRole('radio', { name: type }))
  await user.type(screen.getByLabelText('Conteúdo da publicação'), `Conteúdo ${type}`)
  await user.click(screen.getByRole('checkbox', { name: /Li e compreendi/i }))
  await user.click(screen.getByRole('button', { name: 'Publicar' }))
  await waitFor(() => expect(api).toHaveBeenCalledWith('/community/posts', expect.objectContaining({ method: 'POST' })))
  return JSON.parse(api.mock.calls.find(call => call[0] === '/community/posts')?.[1]?.body as string)
}

describe('Comunidade da Fase 8', () => {
  beforeEach(() => localStorage.clear())

  it('renderiza o feed real e o estado LOCAL_ONLY', async () => {
    render(<CommunityScreen api={apiForCommunity() as ApiClient} navigate={vi.fn()}/>)
    expect(await screen.findByText('Aprendi testes acessíveis.')).toBeInTheDocument()
    expect(screen.getByText('LOCAL_ONLY')).toBeInTheDocument()
  })

  it('exibe loading durante a busca', () => {
    const api = vi.fn((path: string) => path.startsWith('/community/feed') ? new Promise(() => undefined) : Promise.resolve({ items: [] }))
    render(<CommunityScreen api={api as ApiClient} navigate={vi.fn()}/>)
    expect(screen.getByText('Carregando publicações…')).toBeInTheDocument()
  })

  it('exibe erro e permite retry', async () => {
    let failures = 1
    const api = vi.fn(async (path: string) => {
      if (path.startsWith('/community/feed') && failures--) throw new Error('network')
      if (path.startsWith('/community/feed')) return { items: [], next_offset: null }
      if (path === '/courses') return { items: [] }
      throw Object.assign(new Error('Forbidden'), { status: 403 })
    })
    const user = userEvent.setup()
    render(<CommunityScreen api={api as ApiClient} navigate={vi.fn()}/>)
    await user.click(await screen.findByRole('button', { name: 'Tentar novamente' }))
    expect(await screen.findByText('Ainda não há publicações nesta categoria.')).toBeInTheDocument()
  })

  it('renderiza lista vazia', async () => {
    render(<CommunityScreen api={apiForCommunity([]) as ApiClient} navigate={vi.fn()}/>)
    expect(await screen.findByText('Ainda não há publicações nesta categoria.')).toBeInTheDocument()
  })

  it('filtra por categoria usando o contrato da API', async () => {
    const api = apiForCommunity()
    const user = userEvent.setup()
    render(<CommunityScreen api={api as ApiClient} navigate={vi.fn()}/>)
    await screen.findByText(post.content)
    await user.click(screen.getByRole('button', { name: /Dúvidas/ }))
    await waitFor(() => expect(api).toHaveBeenCalledWith(expect.stringContaining('category=question')))
  })

  it.each([
    ['Aprendizado', 'learning'], ['Dúvidas', 'question'], ['Conquistas', 'achievement'],
  ] as const)('cria uma publicação %s', async (label, category) => {
    const payload = await fillAndPublishPost(apiForCommunity(), label)
    expect(payload).toMatchObject({ category, public_acknowledged: true })
  })

  it('rejeita conteúdo vazio e mantém mídia desabilitada', async () => {
    const api = apiForCommunity()
    const user = userEvent.setup()
    render(<CommunityScreen api={api as ApiClient} navigate={vi.fn()}/>)
    await openComposer(user)
    expect(screen.getByRole('button', { name: /Mídia/i })).toBeDisabled()
    await user.click(screen.getByRole('checkbox', { name: /Li e compreendi/i }))
    await user.click(screen.getByRole('button', { name: 'Publicar' }))
    expect(await screen.findByText('Escreva uma publicação antes de enviar.')).toBeInTheDocument()
    expect(api.mock.calls.some(call => call[0] === '/community/posts')).toBe(false)
  })

  it('impede envio duplicado durante uma requisição em andamento', async () => {
    let resolvePost!: (value: any) => void
    const api = apiForCommunity()
    api.mockImplementation(async (path: string, options?: RequestInit) => {
      if (path === '/community/posts' && options?.method === 'POST') return new Promise(resolve => { resolvePost = resolve })
      if (path.startsWith('/community/feed')) return { items: [], next_offset: null }
      if (path === '/courses') return { items: [] }
      throw Object.assign(new Error('Forbidden'), { status: 403 })
    })
    const user = userEvent.setup()
    render(<CommunityScreen api={api as ApiClient} navigate={vi.fn()}/>)
    await openComposer(user)
    await user.type(screen.getByLabelText('Conteúdo da publicação'), 'Uma vez')
    await user.click(screen.getByRole('checkbox', { name: /Li e compreendi/i }))
    const button = screen.getByRole('button', { name: 'Publicar' })
    await user.dblClick(button)
    expect(api.mock.calls.filter(call => call[0] === '/community/posts')).toHaveLength(1)
    resolvePost({ id: 'created' })
  })

  it('envia denúncia sem ocultar localmente o post', async () => {
    const api = apiForCommunity()
    const user = userEvent.setup()
    render(<CommunityScreen api={api as ApiClient} navigate={vi.fn()}/>)
    await user.click(await screen.findByRole('button', { name: 'Denunciar' }))
    await user.selectOptions(screen.getByLabelText('Motivo'), 'SPAM')
    await user.click(screen.getByRole('button', { name: 'Enviar denúncia' }))
    expect(await screen.findByText('Denúncia recebida')).toBeInTheDocument()
    expect(screen.getByText(post.content)).toBeInTheDocument()
  })

  it('trata 401 no feed', async () => {
    const navigate = vi.fn()
    const api = vi.fn(async (path: string) => {
      if (path.startsWith('/community/feed')) throw Object.assign(new Error('Unauthorized'), { status: 401 })
      if (path === '/courses') return { items: [] }
      throw Object.assign(new Error('Forbidden'), { status: 403 })
    })
    const user = userEvent.setup()
    render(<CommunityScreen api={api as ApiClient} navigate={navigate}/>)
    await user.click(await screen.findByRole('button', { name: 'Entrar novamente' }))
    expect(navigate).toHaveBeenCalledWith(expect.stringContaining('/entrar?returnTo='))
  })

  it('não exibe moderação quando o backend responde 403', async () => {
    render(<CommunityScreen api={apiForCommunity() as ApiClient} navigate={vi.fn()}/>)
    await screen.findByText(post.content)
    expect(screen.queryByRole('heading', { name: 'Moderação' })).not.toBeInTheDocument()
  })
})

describe('Oportunidades da Fase 8', () => {
  beforeEach(() => localStorage.clear())

  it('distingue OpportunityListing de PaidTask pela resposta da API', async () => {
    const api = vi.fn().mockResolvedValue({ external_opportunities: [listing], paid_tasks: [paidTask] })
    const { rerender } = render(<OpportunitiesScreen api={api} navigate={vi.fn()} query={new URLSearchParams()}/>)
    expect(await screen.findByText('Hackathon aberto')).toBeInTheDocument()
    expect(screen.getByText('Sem pagamento processado pelo Bluejet')).toBeInTheDocument()
    expect(screen.queryByText('Revisão de acessibilidade')).not.toBeInTheDocument()
    rerender(<OpportunitiesScreen api={api} navigate={vi.fn()} query={new URLSearchParams('tipo=remuneradas')}/>)
    expect(await screen.findByText('Revisão de acessibilidade')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Publicar oportunidade' })).not.toBeInTheDocument()
  })

  it('renderiza CTA externo com proteções seguras', async () => {
    const api = vi.fn().mockResolvedValue(listing)
    render(<ExternalOpportunityDetailScreen api={api} navigate={vi.fn()} id="listing-1"/>)
    const link = await screen.findByRole('link', { name: /Acessar oportunidade externa/ })
    expect(link).toHaveAttribute('href', listing.external_url)
    expect(link).toHaveAttribute('rel', 'noopener noreferrer')
    expect(screen.queryByText(/Candidatar-se|Enviar atividade|Receber pagamento/)).not.toBeInTheDocument()
  })

  it('aceita HTTP/HTTPS e rejeita esquemas perigosos ou credenciais na URL', () => {
    expect(safeExternalUrl('javascript:alert(1)')).toBeNull()
    expect(safeExternalUrl('data:text/html,test')).toBeNull()
    expect(safeExternalUrl('file:///etc/passwd')).toBeNull()
    expect(safeExternalUrl('https://user:password@example.org')).toBeNull()
    expect(safeExternalUrl('http://example.org')).toBe('http://example.org/')
    expect(safeExternalUrl('https://example.org')).toBe('https://example.org/')
  })

  it('Voltar retorna à etapa imediatamente anterior', async () => {
    const navigate = vi.fn()
    const user = userEvent.setup()
    render(<OpportunityListingWizard api={vi.fn()} navigate={navigate} step="requisitos"/>)
    const backButtons = screen.getAllByRole('button', { name: 'Voltar' })
    await user.click(backButtons[backButtons.length - 1])
    expect(navigate).toHaveBeenCalledWith('/app/oportunidades/nova/basico')
  })

  it('bloqueia URL javascript na etapa de origem', async () => {
    const navigate = vi.fn()
    const user = userEvent.setup()
    render(<OpportunityListingWizard api={vi.fn()} navigate={navigate} step="origem"/>)
    await user.type(screen.getByLabelText('Organizador externo'), 'Organização')
    await user.type(screen.getByLabelText('URL externa'), 'javascript:alert(1)')
    await user.click(screen.getByRole('checkbox', { name: /Confirmo que esta oportunidade/ }))
    await user.click(screen.getByRole('button', { name: /Continuar/ }))
    expect(await screen.findByText(/URL segura iniciada por http:\/\/ ou https:\/\//)).toBeInTheDocument()
    expect(navigate).not.toHaveBeenCalled()
  })

  it('revisa e cria somente OpportunityListing com idempotência', async () => {
    localStorage.setItem('bluejet_external_opportunity_draft_v1', JSON.stringify({
      ...listing, tags: 'tecnologia, gratuito', non_remunerated_ack: true, review_ack: false,
      location: 'São Paulo', starts_at: '2026-09-20T12:00', application_deadline: '2026-09-10T12:00',
      idempotency_key: 'opportunity-listing-test',
    }))
    const api = vi.fn().mockResolvedValue({ ...listing, id: 'created-listing' })
    const navigate = vi.fn()
    const user = userEvent.setup()
    render(<OpportunityListingWizard api={api} navigate={navigate} step="revisao"/>)
    expect(screen.getByText('Esta é uma oportunidade externa e não remunerada pelo Bluejet.')).toBeInTheDocument()
    expect(screen.getByText(listing.external_url)).toBeInTheDocument()
    await user.click(screen.getByRole('checkbox', { name: /Revisei a origem/ }))
    await user.click(screen.getByRole('button', { name: 'Publicar oportunidade' }))
    await waitFor(() => expect(api).toHaveBeenCalledTimes(1))
    expect(api).toHaveBeenCalledWith('/opportunities/external', expect.objectContaining({ method: 'POST', headers: expect.objectContaining({ 'Idempotency-Key': 'opportunity-listing-test' }) }))
    expect(api.mock.calls.some(call => String(call[0]).includes('paid-tasks'))).toBe(false)
    expect(navigate).toHaveBeenCalledWith('/app/oportunidades?publicada=1')
  })

  it('expõe labels e regiões navegáveis por teclado', async () => {
    const user = userEvent.setup()
    render(<OpportunitiesScreen api={vi.fn().mockResolvedValue({ external_opportunities: [listing], paid_tasks: [] })} navigate={vi.fn()} query={new URLSearchParams()}/>)
    const tablist = screen.getByRole('tablist', { name: 'Tipos de oportunidade' })
    expect(within(tablist).getAllByRole('tab')).toHaveLength(2)
    await user.tab()
    expect(document.activeElement).toBeInstanceOf(HTMLElement)
  })
})
