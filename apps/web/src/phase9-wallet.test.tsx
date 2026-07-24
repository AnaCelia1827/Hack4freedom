import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { WalletScreen, WithdrawalScreen } from './phase9-wallet'

const summary = {
  mode: 'MOCK',
  score: 80,
  total_sats: 1200,
  transactions: [{ id: 'receipt-1', amount_sats: 1200, mode: 'SANDBOX' }],
  in_progress: [{ id: 'progress-1', assignment_id: 'assignment-1', status: 'ACTIVE' }],
}

describe('Carteira da Fase 9', () => {
  it('exibe somente valores da API e diferencia score de saldo', async () => {
    render(<WalletScreen api={vi.fn().mockResolvedValue(summary)} navigate={vi.fn()} />)
    expect(await screen.findAllByText('1.200 sats')).toHaveLength(2)
    expect(screen.getByText('80')).toBeInTheDocument()
    expect(screen.getByText('Pontuação não é saldo.')).toBeInTheDocument()
    expect(screen.getByText(/Modo MOCK/)).toBeInTheDocument()
    expect(screen.queryByText('R$ 1.240,50')).not.toBeInTheDocument()
  })

  it('navega para saque e preserva assignment em andamento', async () => {
    const navigate = vi.fn()
    const user = userEvent.setup()
    render(<WalletScreen api={vi.fn().mockResolvedValue(summary)} navigate={navigate} />)
    await user.click(await screen.findByRole('button', { name: /Resgatar/ }))
    expect(navigate).toHaveBeenCalledWith('/app/carteira/saque')
    await user.click(screen.getByRole('button', { name: /assignment-1/ }))
    expect(navigate).toHaveBeenCalledWith('/app/trabalhos/assignment-1')
  })

  it('expõe loading, erro e retry', async () => {
    const api = vi.fn().mockRejectedValueOnce(new Error('offline')).mockResolvedValueOnce(summary)
    const user = userEvent.setup()
    render(<WalletScreen api={api} navigate={vi.fn()} />)
    expect(screen.getByText('Carregando carteira...')).toBeInTheDocument()
    await user.click(await screen.findByRole('button', { name: 'Tentar novamente' }))
    expect(await screen.findAllByText('1.200 sats')).toHaveLength(2)
    expect(api).toHaveBeenCalledTimes(2)
  })
})

describe('Saque protegido da Fase 9', () => {
  it('preserva o layout do fluxo sem habilitar operação inexistente', async () => {
    render(<WithdrawalScreen api={vi.fn().mockResolvedValue(summary)} navigate={vi.fn()} />)
    expect(await screen.findByRole('heading', { name: 'Realizar saque' })).toBeInTheDocument()
    expect(screen.getByText('1.200 sats')).toBeInTheDocument()
    expect(screen.getByText(/backend não possui contrato de saque/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Confirmar saque' })).toBeDisabled()
  })

  it('sanitiza o valor para dígitos e não envia invoice', async () => {
    const api = vi.fn().mockResolvedValue(summary)
    const user = userEvent.setup()
    render(<WithdrawalScreen api={api} navigate={vi.fn()} />)
    const amount = await screen.findByLabelText('Valor do saque (sats)')
    await user.type(amount, 'R$ 12a00')
    expect(amount).toHaveValue('1200')
    await user.type(screen.getByLabelText('Endereço da carteira / Invoice'), 'lnbc-private-value')
    expect(api).toHaveBeenCalledTimes(1)
  })

  it('cancela e volta para Minha Carteira', async () => {
    const navigate = vi.fn()
    const user = userEvent.setup()
    render(<WithdrawalScreen api={vi.fn().mockResolvedValue(summary)} navigate={navigate} />)
    await user.click(await screen.findByRole('button', { name: 'Cancelar' }))
    await waitFor(() => expect(navigate).toHaveBeenCalledWith('/app/carteira'))
  })
})
