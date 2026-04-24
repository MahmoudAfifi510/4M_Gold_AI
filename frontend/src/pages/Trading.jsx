import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import client from '../api/client'

export default function Trading() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    weight_oz: '',
    karat: 21,
    price: '',
    transaction_date: ''
  })
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    try {
      await client.post('/portfolio/buys', {
        ...form,
        weight_oz: Number(form.weight_oz),
        karat: Number(form.karat),
        price: Number(form.price)
      })
      setSuccess('Buy transaction saved successfully.')
      navigate('/portfolio')
    } catch (err) {
      setError(err?.response?.data?.detail || 'Could not save transaction')
    }
  }

  return (
    <main className="content-grid">
      <section className="panel panel-wide">
        <div className="section-head">
          <div>
            <p className="eyebrow">Trading</p>
            <h2>Add buy transactions</h2>
          </div>
        </div>

        <form className="trade-form gold-trade-form" onSubmit={submit}>
          <input
            type="number"
            step="0.01"
            min="0"
            placeholder="Weight (oz)"
            value={form.weight_oz}
            onChange={(e) => setForm({ ...form, weight_oz: e.target.value })}
          />
          <select
            className="gold-select"
            value={form.karat}
            onChange={(e) => setForm({ ...form, karat: e.target.value })}
          >
            <option value="24">24K</option>
            <option value="21">21K</option>
            <option value="18">18K</option>
          </select>
          <input
            type="number"
            step="0.01"
            min="0"
            placeholder="Price"
            value={form.price}
            onChange={(e) => setForm({ ...form, price: e.target.value })}
          />
          <input
            type="date"
            value={form.transaction_date}
            onChange={(e) => setForm({ ...form, transaction_date: e.target.value })}
          />
          {error && <div className="error-box">{error}</div>}
          {success && <div className="success-box">{success}</div>}
          <button className="button button-primary" type="submit">Save buy</button>
        </form>
      </section>
    </main>
  )
}
