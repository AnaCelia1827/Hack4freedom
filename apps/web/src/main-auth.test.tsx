import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { App, resetSessionCache } from './main'

const pubkey = 'a'.repeat(64)

function jsonResponse(payload: unknown, status = 200) {
  return Promise.resolve(new Response(JSON.stringify(payload), {
    status,
    headers: { 'Content-Type': 'application/json' },
  }))
}

describe('fluxo de criação de conta', () => {
  beforeEach(() => {
    resetSessionCache()
    history.replaceState({}, '', '/entrar')
    Object.defineProperty(window, 'nostr', {
      configurable: true,
      value: {
        getPublicKey: vi.fn().mockResolvedValue(pubkey),
        signEvent: vi.fn().mockImplementation(async event => ({
          ...event,
          pubkey,
          id: 'b'.repeat(64),
          sig: 'c'.repeat(128),
        })),
      },
    })
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    Reflect.deleteProperty(window, 'nostr')
    sessionStorage.clear()
  })

  it('preserva a intenção de cadastro após assinar com NIP-07 e prepara a etapa 1', async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL, options?: RequestInit) => {
      const url = String(input)
      if (url.endsWith('/auth/nostr/challenges')) return jsonResponse({
        challenge: 'challenge',
        signing: { kind: 27235, method: 'POST', url: 'http://localhost:5001/auth/nostr/sessions', payload_hash: 'd'.repeat(64) },
      })
      if (url.endsWith('/auth/nostr/sessions')) return jsonResponse({ pubkey, mode: 'REAL', expires_at: '2099-01-01T00:00:00Z' }, 201)
      if (url.endsWith('/me')) return jsonResponse({ pubkey, mode: 'REAL', roles: ['PARTICIPANT'], onboarding_completed: false, expires_at: '2099-01-01T00:00:00Z' })
      if (url.endsWith('/onboarding/drafts') && options?.method === 'POST') return jsonResponse({ id: 'draft-1', status: 'IN_PROGRESS' }, 201)
      return jsonResponse({ title: 'Not Found' }, 404)
    })
    vi.stubGlobal('fetch', fetchMock)
    const user = userEvent.setup()

    render(<App />)
    await user.click(screen.getByRole('button', { name: 'Criar conta' }))
    expect(screen.getByRole('heading', { name: 'Criar conta' })).toBeVisible()

    await user.click(screen.getByRole('button', { name: 'Continuar com Nostr' }))

    expect(await screen.findByRole('heading', { name: 'Dados pessoais' })).toBeVisible()
    expect(location.pathname).toBe('/cadastro/acesso')
    expect(fetchMock).toHaveBeenCalledWith('/api/onboarding/drafts', expect.objectContaining({ method: 'POST' }))
  })

  it('mantém o modo criar conta ao proteger uma rota de cadastro sem sessão', async () => {
    history.replaceState({}, '', '/cadastro/acesso')
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ title: 'Unauthorized' }), {
      status: 401,
      headers: { 'Content-Type': 'application/json' },
    })))

    render(<App />)

    await waitFor(() => expect(location.pathname).toBe('/entrar'))
    expect(new URLSearchParams(location.search).get('intent')).toBe('signup')
    expect(await screen.findByRole('heading', { name: 'Criar conta' })).toBeVisible()
  })
})
