import { useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'

export default function Landing() {
  const revealRefs = useRef([])

  useEffect(() => {
    const elements = revealRefs.current.filter(Boolean)
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          entry.target.classList.toggle('is-visible', entry.isIntersecting)
        })
      },
      { threshold: 0.18, rootMargin: '0px 0px -8% 0px' }
    )

    elements.forEach((element) => observer.observe(element))

    return () => observer.disconnect()
  }, [])

  const infoSections = [
    {
      side: 'left',
      eyebrow: 'What it does',
      title: 'A focused AI dashboard for gold market direction.',
      text:
        '4M Gold AI brings together historical gold, oil, and USD signals to present a clear 5-day directional view. The goal is to help users understand momentum without drowning in noise.'
    },
    {
      side: 'right',
      eyebrow: 'How it works',
      title: 'Built around live market sync and stored history.',
      text:
        'The backend keeps market data in MySQL, refreshes daily, and supports manual historical backfills. That means the model can train on saved data instead of depending on a one-time spreadsheet import.'
    },
    {
      side: 'left',
      eyebrow: 'For users',
      title: 'Track price trends, predictions, and portfolio activity in one place.',
      text:
        'The dashboard shows gold price history, the next 5-day up/down probabilities, and a recommendation summary. Portfolio pages keep buy lots, linked sells, and profit tracking organized.'
    },
    {
      side: 'right',
      eyebrow: 'Why it matters',
      title: 'Designed for clarity, not hype.',
      text:
        'Every screen is styled to feel calm and premium, with a gold-first visual language. The interface highlights the most useful signals first so the experience stays simple and readable.'
    }
  ]

  const coinSpecs = [
    { left: '8%', delay: '0s', duration: '8.5s', size: '42px', depth: '0px' },
    { left: '22%', delay: '1.2s', duration: '10s', size: '30px', depth: '8px' },
    { left: '46%', delay: '0.8s', duration: '9.2s', size: '36px', depth: '4px' },
    { left: '68%', delay: '2.1s', duration: '11s', size: '28px', depth: '10px' },
    { left: '84%', delay: '0.5s', duration: '9.8s', size: '48px', depth: '2px' },
    { left: '14%', delay: '3.1s', duration: '8.8s', size: '24px', depth: '6px' },
    { left: '31%', delay: '2.7s', duration: '10.6s', size: '40px', depth: '3px' },
    { left: '57%', delay: '1.9s', duration: '9.4s', size: '26px', depth: '9px' },
    { left: '73%', delay: '3.8s', duration: '11.2s', size: '34px', depth: '1px' },
    { left: '92%', delay: '1.6s', duration: '8.9s', size: '30px', depth: '5px' },
    { left: '4%', delay: '2.4s', duration: '10.2s', size: '22px', depth: '7px' },
    { left: '38%', delay: '4.2s', duration: '11.5s', size: '46px', depth: '2px' }
  ]

  return (
    <main className="landing-page">
      <section className="hero">
        <div className="hero-glow hero-glow-left" />
        <div className="hero-glow hero-glow-right" />
        <section className="hero-copy reveal-block reveal-left is-visible">
          <p className="eyebrow">Premium gold intelligence platform</p>
          <h1>Trade with 5-day AI direction forecasts for gold.</h1>
          <p className="hero-text">
            4M Gold AI combines historical gold, oil, and USD market data to estimate
            the probability of gold moving up or down over the next five days.
          </p>
          <div className="hero-actions">
            <Link className="button button-primary" to="/login">Login</Link>
            <Link className="button button-secondary" to="/register">Register</Link>
          </div>
        </section>

        <section className="hero-panel reveal-block reveal-right is-visible">
          <div className="hero-visual">
            <div className="glass-card hero-glass-card">
              <div className="mini-kpi">
                <span>AI signal</span>
                <strong>UP / DOWN</strong>
              </div>
              <div className="mini-kpi">
                <span>Forecast horizon</span>
                <strong>Next 5 days</strong>
              </div>
              <div className="mini-kpi">
                <span>Data sources</span>
                <strong>Gold, oil, USD</strong>
              </div>
            </div>

            <div className="hero-scene" aria-hidden="true">
              <div className="coin-rain">
                {coinSpecs.map((coin, index) => (
                  <span
                    key={index}
                    className="gold-coin falling-coin"
                    style={{
                      left: coin.left,
                      animationDelay: coin.delay,
                      animationDuration: coin.duration,
                      width: coin.size,
                      height: coin.size,
                      '--coin-depth': coin.depth
                    }}
                  />
                ))}
              </div>

              <div className="floating-bar-wrap">
                <span className="floating-bar-shadow" />
                <div className="gold-bar">
                  <span className="gold-bar-top" />
                  <span className="gold-bar-face">4M GOLD</span>
                  <span className="gold-bar-edge" />
                </div>
              </div>
            </div>
          </div>
        </section>
      </section>

      <section className="landing-section landing-intro">
        <div className="section-head landing-head">
          <div className="reveal-block reveal-left" ref={(el) => { revealRefs.current[0] = el }}>
            <p className="eyebrow">Overview</p>
            <h2>Everything you need to follow gold in one dashboard.</h2>
          </div>
          <p
            className="muted landing-summary reveal-block reveal-right"
            ref={(el) => { revealRefs.current[1] = el }}
          >
            The platform is built to help you monitor trends, review predictions, and manage your portfolio with a clean interface and a steady flow of market context.
          </p>
        </div>
      </section>

      <section className="landing-section feature-stack">
        {infoSections.map((section, index) => (
          <article
            key={section.title}
            className={`feature-card reveal-block reveal-${section.side}`}
            ref={(el) => { revealRefs.current[index + 2] = el }}
          >
            <p className="eyebrow">{section.eyebrow}</p>
            <h3>{section.title}</h3>
            <p className="muted">{section.text}</p>
          </article>
        ))}
      </section>

      <section className="landing-section landing-cta">
        <div className="cta-panel reveal-block reveal-left" ref={(el) => { revealRefs.current[6] = el }}>
          <p className="eyebrow">Start here</p>
          <h2>See market direction, then decide with more context.</h2>
          <p className="muted">
            Register or log in to view the dashboard, the forecast cards, portfolio tracking, and the recommendation summary.
          </p>
        </div>
        <div className="cta-actions reveal-block reveal-right" ref={(el) => { revealRefs.current[7] = el }}>
          <Link className="button button-primary" to="/register">Create account</Link>
          <Link className="button button-secondary" to="/login">Sign in</Link>
        </div>
      </section>
    </main>
  )
}
