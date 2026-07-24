import { useCallback, useEffect, useState } from 'react'
import {
  ArrowDownToLine,
  ArrowLeft,
  BadgeDollarSign,
  Bolt,
  BriefcaseBusiness,
  CircleDollarSign,
  ReceiptText,
  Search,
  ShieldAlert,
  Trophy,
} from 'lucide-react'
import type { ApiClient } from './phase8'

type WalletTransaction = {
  id: string
  amount_sats: number
  mode?: string
  created_at?: string
  settled_at?: string
}

type InProgressItem = {
  id: string
  assignment_id?: string
  status?: string
}

type WalletSummary = {
  mode: string
  score: number
  total_sats: number
  transactions: WalletTransaction[]
  in_progress?: InProgressItem[]
}

type WalletState =
  | { status: 'loading' }
  | { status: 'error'; code?: number }
  | { status: 'ready'; data: WalletSummary }

function errorStatus(error: unknown) {
  return (error as Error & { status?: number })?.status
}

function sats(value: number) {
  return `${new Intl.NumberFormat('pt-BR').format(Math.max(0, Number(value) || 0))} sats`
}

function WalletError({ code, retry }: { code?: number; retry: () => void }) {
  return (
    <div className="wallet-state" role="alert">
      <strong>{code === 401 ? 'Sua sessão expirou.' : code === 403 ? 'Acesso à carteira não autorizado.' : 'Não foi possível carregar sua carteira.'}</strong>
      <p>Nenhum valor foi estimado ou substituído por mock visual.</p>
      <button type="button" onClick={retry}>Tentar novamente</button>
    </div>
  )
}

export function WalletScreen({ api, navigate }: { api: ApiClient; navigate: (path: string) => void }) {
  const [state, setState] = useState<WalletState>({ status: 'loading' })

  const load = useCallback(async () => {
    setState({ status: 'loading' })
    try {
      const data = await api('/wallet/summary')
      setState({
        status: 'ready',
        data: {
          mode: data.mode || 'UNKNOWN',
          score: Number(data.score) || 0,
          total_sats: Number(data.total_sats) || 0,
          transactions: Array.isArray(data.transactions) ? data.transactions : [],
          in_progress: Array.isArray(data.in_progress) ? data.in_progress : [],
        },
      })
    } catch (error) {
      setState({ status: 'error', code: errorStatus(error) })
    }
  }, [api])

  useEffect(() => { void load() }, [load])

  if (state.status === 'loading') return <main className="wallet-page"><div className="wallet-skeleton" role="status">Carregando carteira...</div></main>
  if (state.status === 'error') return <main className="wallet-page"><WalletError code={state.code} retry={() => void load()} /></main>

  const wallet = state.data
  const mockMode = wallet.mode !== 'REAL'
  return (
    <main className="wallet-page" aria-labelledby="wallet-title">
      <header className="wallet-heading">
        <div><h1 id="wallet-title">Meus rendimentos</h1><p>Seu painel de controle e evolução financeira.</p></div>
        <button type="button" onClick={() => navigate('/app/oportunidades')}><Search aria-hidden="true" /> Nova busca</button>
      </header>

      {mockMode && (
        <div className="wallet-mode-warning" role="status">
          <ShieldAlert aria-hidden="true" />
          <span><strong>Modo {wallet.mode}</strong> — estes valores não comprovam dinheiro real disponível para saque.</span>
        </div>
      )}

      <section className="wallet-dashboard" aria-label="Resumo da carteira">
        <article className="wallet-total-card">
          <div><h2>Total recebido</h2><p>Somente transações liquidadas retornadas pela API.</p></div>
          <div className="wallet-total-row">
            <strong>{sats(wallet.total_sats)}</strong>
            <div>
              <button type="button" className="wallet-statement" onClick={() => document.getElementById('wallet-transactions')?.scrollIntoView()}><ReceiptText aria-hidden="true" /> Extrato</button>
              <button type="button" className="wallet-withdraw" onClick={() => navigate('/app/carteira/saque')}><ArrowDownToLine aria-hidden="true" /> Resgatar</button>
            </div>
          </div>
        </article>
        <article className="wallet-score-card">
          <div><h2>Meu Score</h2><p>Pontuação não é saldo.</p></div>
          <div><strong>{wallet.score}</strong><Trophy aria-hidden="true" /></div>
          <div className="wallet-score-track" aria-hidden="true"><span style={{ width: `${Math.min(100, Math.max(0, wallet.score / 10))}%` }} /></div>
        </article>
      </section>

      <section className="wallet-records" id="wallet-transactions" aria-labelledby="wallet-transactions-title">
        <div className="wallet-records-heading"><CircleDollarSign aria-hidden="true" /><div><h2 id="wallet-transactions-title">Fluxo de receita</h2><p>Valores rastreáveis retornados pelo backend.</p></div></div>
        {wallet.transactions.length === 0 ? (
          <div className="wallet-empty"><ReceiptText aria-hidden="true" /><strong>Nenhum rendimento liquidado ainda.</strong></div>
        ) : (
          <ul>{wallet.transactions.map(transaction => <li key={transaction.id}><span><ReceiptText aria-hidden="true" /> Transação liquidada</span><strong>{sats(transaction.amount_sats)}</strong><small>{transaction.mode || wallet.mode}</small></li>)}</ul>
        )}
      </section>

      <section className="wallet-progress" aria-labelledby="wallet-progress-title">
        <h2 id="wallet-progress-title">Em andamento</h2>
        {!wallet.in_progress?.length ? (
          <div className="wallet-empty"><BriefcaseBusiness aria-hidden="true" /><strong>Nenhuma atividade financeira em andamento.</strong></div>
        ) : wallet.in_progress.map(item => (
          <button type="button" key={item.id} onClick={() => item.assignment_id && navigate(`/app/trabalhos/${encodeURIComponent(item.assignment_id)}`)}>
            <BriefcaseBusiness aria-hidden="true" /><span><strong>{item.assignment_id || item.id}</strong><small>{item.status || 'Em andamento'}</small></span>
          </button>
        ))}
      </section>
    </main>
  )
}

export function WithdrawalScreen({ api, navigate }: { api: ApiClient; navigate: (path: string) => void }) {
  const [state, setState] = useState<WalletState>({ status: 'loading' })
  const [amount, setAmount] = useState('')
  const [invoice, setInvoice] = useState('')

  const load = useCallback(async () => {
    setState({ status: 'loading' })
    try {
      const data = await api('/wallet/summary')
      setState({ status: 'ready', data: { ...data, transactions: data.transactions || [], in_progress: data.in_progress || [] } })
    } catch (error) {
      setState({ status: 'error', code: errorStatus(error) })
    }
  }, [api])

  useEffect(() => { void load() }, [load])

  if (state.status === 'loading') return <main className="withdrawal-page"><div className="wallet-skeleton" role="status">Carregando saldo...</div></main>
  if (state.status === 'error') return <main className="withdrawal-page"><WalletError code={state.code} retry={() => void load()} /></main>

  const wallet = state.data
  return (
    <main className="withdrawal-page" aria-labelledby="withdrawal-title">
      <button className="withdrawal-back" type="button" onClick={() => navigate('/app/carteira')}><ArrowLeft aria-hidden="true" /> Voltar para Minha Carteira</button>
      <section className="withdrawal-card">
        <header><h1 id="withdrawal-title">Realizar saque</h1><p>Transfira fundos disponíveis para sua carteira externa.</p></header>
        <div className="withdrawal-balance"><span>Saldo informado pela API</span><strong>{sats(wallet.total_sats)}</strong><BadgeDollarSign aria-hidden="true" /></div>
        <div className="wallet-mode-warning" role="status"><ShieldAlert aria-hidden="true" /><span><strong>Operação indisponível</strong> — o backend não possui contrato de saque de saldo. Modo atual: {wallet.mode || 'UNKNOWN'}.</span></div>
        <label htmlFor="withdrawal-amount">Valor do saque (sats)</label>
        <input id="withdrawal-amount" inputMode="numeric" value={amount} onChange={event => setAmount(event.target.value.replace(/\D/g, ''))} placeholder="0" />
        <fieldset><legend>Método de recebimento</legend><label className="withdrawal-method is-selected"><input type="radio" name="withdrawal-method" checked readOnly /><Bolt aria-hidden="true" /><span>Lightning Network<small>Exige obrigação aprovada</small></span></label><label className="withdrawal-method is-disabled"><input type="radio" name="withdrawal-method" disabled /><CircleDollarSign aria-hidden="true" /><span>Bitcoin On-chain<small>Não suportado</small></span></label></fieldset>
        <label htmlFor="withdrawal-invoice">Endereço da carteira / Invoice</label>
        <input id="withdrawal-invoice" value={invoice} onChange={event => setInvoice(event.target.value)} placeholder="lnbc..." autoComplete="off" />
        <button className="withdrawal-confirm" type="button" disabled aria-describedby="withdrawal-blocked">Confirmar saque</button>
        <p id="withdrawal-blocked" className="withdrawal-blocked">Confirmação bloqueada até existir uma PaymentObligation válida e endpoint autorizado.</p>
        <button className="withdrawal-cancel" type="button" onClick={() => navigate('/app/carteira')}>Cancelar</button>
      </section>
    </main>
  )
}
