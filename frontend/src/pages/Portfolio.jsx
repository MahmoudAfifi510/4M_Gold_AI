import { useEffect, useMemo, useState } from 'react'
import client from '../api/client'

function todayISO() {
  return new Date().toISOString().slice(0, 10)
}

export default function Portfolio() {
  const [summary, setSummary] = useState(null)
  const [error, setError] = useState('')
  const [sellingBuyId, setSellingBuyId] = useState(null)
  const [sellForms, setSellForms] = useState({})

  const load = async () => {
    try {
      const { data } = await client.get('/portfolio/summary')
      setSummary(data)
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to load portfolio')
    }
  }

  useEffect(() => {
    load()
  }, [])

  const startSell = (buy) => {
    setError('')
    setSellingBuyId(buy.id)
    setSellForms((current) => ({
      ...current,
      [buy.id]: current[buy.id] || {
        sell_weight_oz: '',
        price: '',
        transaction_date: todayISO()
      }
    }))
  }

  const updateSellForm = (buyId, field, value) => {
    setSellForms((current) => ({
      ...current,
      [buyId]: {
        ...(current[buyId] || {}),
        [field]: value
      }
    }))
  }

  const submitSell = async (buyId) => {
    setError('')
    try {
      const form = sellForms[buyId]
      await client.post(`/portfolio/buys/${buyId}/sell`, {
        sell_weight_oz: Number(form.sell_weight_oz),
        price: Number(form.price),
        transaction_date: form.transaction_date
      })
      setSellingBuyId(null)
      await load()
    } catch (err) {
      setError(err?.response?.data?.detail || 'Could not save sell transaction')
    }
  }

  const buys = useMemo(() => summary?.buys || [], [summary])
  const sales = useMemo(() => summary?.sales || [], [summary])

  return (
    <main className="content-grid">
      <section className="panel panel-wide">
        <div className="section-head">
          <div>
            <p className="eyebrow">Portfolio</p>
            <h2>My gold holdings</h2>
          </div>
          {summary && (
            <div className={`big-stat ${summary.total_profit_loss >= 0 ? 'positive' : 'negative'}`}>
              {summary.total_profit_loss >= 0 ? '+' : ''}
              {summary.total_profit_loss.toFixed(2)}
            </div>
          )}
        </div>

        {error && <div className="error-box">{error}</div>}

        {summary && (
          <div className="portfolio-stats">
            <div className="market-chip">Realized P/L: {summary.total_realized_profit_loss >= 0 ? '+' : ''}{summary.total_realized_profit_loss.toFixed(2)}</div>
            <div className="market-chip">Unrealized P/L: {summary.total_unrealized_profit_loss >= 0 ? '+' : ''}{summary.total_unrealized_profit_loss.toFixed(2)}</div>
            <div className="market-chip">Open buy lots: {buys.length}</div>
          </div>
        )}

        <h3 className="section-subtitle">Buy lots</h3>
        <div className="transaction-list">
          {buys.length === 0 && <p className="muted">No buy transactions yet.</p>}
          {buys.map((buy) => (
            <article className="holding-card" key={buy.id}>
              <div className="holding-main">
                <div>
                  <strong>{buy.weight_oz.toFixed(2)} oz</strong>
                  <p>{buy.transaction_date}</p>
                </div>
                <div>
                  <span className="holding-label">Karat</span>
                  <strong>{buy.karat}K</strong>
                </div>
                <div>
                  <span className="holding-label">Remaining</span>
                  <strong>{buy.remaining_weight_oz.toFixed(2)} oz</strong>
                </div>
                <div>
                  <span className="holding-label">Current value</span>
                  <strong className={buy.unrealized_profit_loss >= 0 ? 'positive' : 'negative'}>
                    ${buy.current_value.toFixed(2)}
                  </strong>
                </div>
              </div>

              <div className="holding-footer">
                <div className={buy.unrealized_profit_loss >= 0 ? 'positive' : 'negative'}>
                  Unrealized P/L: {buy.unrealized_profit_loss >= 0 ? '+' : ''}{buy.unrealized_profit_loss.toFixed(2)}
                </div>
                <button className="button button-secondary" type="button" onClick={() => startSell(buy)}>
                  Sell
                </button>
              </div>

              {sellingBuyId === buy.id && (
                <div className="sell-panel">
                  <h4>Sell from this buy lot</h4>
                  <div className="trade-form sell-form">
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      max={buy.remaining_weight_oz}
                      placeholder="Sell weight (oz)"
                      value={sellForms[buy.id]?.sell_weight_oz || ''}
                      onChange={(e) => updateSellForm(buy.id, 'sell_weight_oz', e.target.value)}
                    />
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      placeholder="Sell price"
                      value={sellForms[buy.id]?.price || ''}
                      onChange={(e) => updateSellForm(buy.id, 'price', e.target.value)}
                    />
                    <input
                      type="date"
                      value={sellForms[buy.id]?.transaction_date || todayISO()}
                      onChange={(e) => updateSellForm(buy.id, 'transaction_date', e.target.value)}
                    />
                    <button className="button button-primary" type="button" onClick={() => submitSell(buy.id)}>
                      Confirm sell
                    </button>
                  </div>
                </div>
              )}
            </article>
          ))}
        </div>

        <h3 className="section-subtitle">Sell history</h3>
        <div className="transaction-list">
          {sales.length === 0 && <p className="muted">No sell transactions yet.</p>}
          {sales.map((sell) => (
            <article className="holding-card" key={sell.id}>
              <div className="holding-main">
                <div>
                  <strong>{sell.sell_weight_oz.toFixed(2)} oz sold</strong>
                  <p>{sell.transaction_date}</p>
                </div>
                <div>
                  <span className="holding-label">Linked buy</span>
                  <strong>#{sell.buy_transaction_id}</strong>
                </div>
                <div>
                  <span className="holding-label">P/L</span>
                  <strong className={sell.profit_loss >= 0 ? 'positive' : 'negative'}>
                    {sell.profit_loss >= 0 ? '+' : ''}{sell.profit_loss.toFixed(2)}
                  </strong>
                </div>
              </div>
            </article>
          ))}
        </div>

      </section>
    </main>
  )
}
