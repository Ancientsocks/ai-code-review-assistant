
import { useState } from 'react'

type Finding = {
  source: string
  severity: string
  title: string
  message: string
  line?: number | null
  rule_id?: string | null
  suggestion?: string | null
}

type Review = {
  id?: number
  language: string
  summary: string
  findings: Finding[]
}

const API = import.meta.env.VITE_API_URL || ''
const REQUEST_TIMEOUT_MS = 20_000

function getErrorMessage(detail: unknown, fallback: string): string {
  if (typeof detail === 'string' && detail.trim()) {
    return detail
  }

  if (Array.isArray(detail)) {
    const messages = detail
      .map((item: unknown) => {
        if (item && typeof item === 'object' && !Array.isArray(item)) {
          const obj = item as Record<string, unknown>
          const message = obj.msg ?? obj.message ?? obj.detail
          const location = Array.isArray(obj.loc)
            ? `${obj.loc.map(String).join('.')}: `
            : ''

          return message != null
            ? `${location}${getErrorMessage(message, '')}`
            : JSON.stringify(item)
        }

        return getErrorMessage(item, '')
      })
      .filter(Boolean)

    return messages.join('; ') || fallback
  }

  if (detail && typeof detail === 'object') {
    const obj = detail as Record<string, unknown>
    const nested = obj.detail ?? obj.message ?? obj.msg ?? obj.error

    if (nested !== undefined && nested !== detail) {
      return getErrorMessage(nested, fallback)
    }

    try {
      return JSON.stringify(detail)
    } catch {
      return fallback
    }
  }

  return fallback
}

async function readResponse(
  response: Response
): Promise<Record<string, unknown>> {
  const text = await response.text()

  if (!text.trim()) return {}

  try {
    const data: unknown = JSON.parse(text)
    if (data && typeof data === 'object' && !Array.isArray(data)) {
      return data as Record<string, unknown>
    }

    return { detail: data }
  } catch {
    if (text.trimStart().startsWith('<')) {
      return {
        detail: `Server returned an unexpected response (${response.status}).`,
      }
    }

    return { detail: text }
  }
}

async function fetchWithTimeout(
  input: RequestInfo | URL,
  init: RequestInit
): Promise<Response> {
  const controller = new AbortController()
  const timeoutId = window.setTimeout(
    () => controller.abort(),
    REQUEST_TIMEOUT_MS
  )

  try {
    return await fetch(input, { ...init, signal: controller.signal })
  } catch (error: unknown) {
    if (controller.signal.aborted) {
      throw new Error('Request timed out. Please try again in a moment.')
    }

    if (error instanceof TypeError) {
      throw new Error(
        'Could not connect to ReviewPilot. Check that the frontend and backend services are running, then try again.'
      )
    }

    throw error
  } finally {
    window.clearTimeout(timeoutId)
  }
}

export default function App() {
  const [email, setEmail] = useState('developer@example.com')
  const [password, setPassword] = useState('')
  const [token, setToken] = useState(
    localStorage.getItem('review_token') || ''
  )
  const [language, setLanguage] = useState('python')
  const [code, setCode] = useState(
    "import os\n\npassword = 'admin123'\nprint(password)\n"
  )
  const [review, setReview] = useState<Review | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function auth(mode: 'login' | 'register') {
    setError('')
    setBusy(true)

    try {
      const response =
        mode === 'register'
          ? await fetchWithTimeout(`${API}/api/v1/auth/register`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ email: email.trim(), password }),
            })
          : await fetchWithTimeout(`${API}/api/v1/auth/login`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
              },
              body: new URLSearchParams({
                username: email.trim(),
                password,
              }),
            })

      const data = await readResponse(response)

      if (!response.ok) {
        throw new Error(
          getErrorMessage(
            data.detail ?? data.message,
            `Authentication failed (${response.status})`
          )
        )
      }

      if (mode === 'register') {
        setError('Account created. Sign in to continue.')
        return
      }

      if (typeof data.access_token !== 'string' || !data.access_token) {
        throw new Error(
          'Login response did not contain an access token. Check the backend API response.'
        )
      }

      localStorage.setItem('review_token', data.access_token)
      setToken(data.access_token)
      setPassword('')
      setError('')
    } catch (e: unknown) {
      setError(
        e instanceof Error
          ? e.message
          : getErrorMessage(e, 'Request failed. Please try again.')
      )
    } finally {
      setBusy(false)
    }
  }

  async function runReview() {
    setBusy(true)
    setError('')
    setReview(null)

    try {
      const response = await fetchWithTimeout(`${API}/api/v1/reviews`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ language, code }),
      })

      const data = await readResponse(response)

      if (!response.ok) {
        throw new Error(
          getErrorMessage(
            data.detail ?? data.message,
            `Review failed (${response.status})`
          )
        )
      }

      if (!Array.isArray(data.findings)) {
        throw new Error(
          'The review API returned an unexpected response. Check the backend API schema.'
        )
      }

      setReview(data as Review)
    } catch (e: unknown) {
      setError(
        e instanceof Error
          ? e.message
          : getErrorMessage(e, 'Review request failed.')
      )
    } finally {
      setBusy(false)
    }
  }

  function logout() {
    localStorage.removeItem('review_token')
    setToken('')
    setReview(null)
    setError('')
    setPassword('')
  }

  return (
    <main className="shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-icon">CR</span>
          <div>
            <strong>ReviewPilot</strong>
            <small>AI-powered code review</small>
          </div>
        </div>

        {token ? (
          <button className="quiet" onClick={logout} disabled={busy}>
            Sign out
          </button>
        ) : (
          <span className="status">Developer workspace</span>
        )}
      </header>

      <section className="hero">
        <p className="eyebrow">CODE QUALITY WORKSPACE</p>
        <h1>
          Catch issues before
          <br />
          <span>they reach production.</span>
        </h1>
        <p className="intro">
          Combine deterministic static analysis with optional AI explanations
          in one review workflow.
        </p>
      </section>

      {!token ? (
        <section className="panel auth-panel">
          <div>
            <p className="eyebrow">GET STARTED</p>
            <h2>Sign in to your workspace</h2>
            <p className="muted">New here? Create an account first.</p>
          </div>

          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              required
            />
          </label>

          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </label>

          <div className="actions">
            <button
              onClick={() => auth('login')}
              disabled={busy || !email.trim() || !password}
            >
              {busy ? 'Please wait…' : 'Sign in'}
            </button>

            <button
              className="secondary"
              onClick={() => auth('register')}
              disabled={busy || !email.trim() || !password}
            >
              Create account
            </button>
          </div>
        </section>
      ) : (
        <section className="workspace">
          <div className="panel editor-panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">01 / INPUT</p>
                <h2>Submit code</h2>
              </div>
              <span className="pill">Private review</span>
            </div>

            <label>
              Language
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
              >
                <option value="python">Python</option>
                <option value="javascript">JavaScript</option>
                <option value="typescript">TypeScript</option>
                <option value="java">Java</option>
                <option value="go">Go</option>
              </select>
            </label>

            <label>
              Source code
              <textarea
                spellCheck={false}
                value={code}
                onChange={(e) => setCode(e.target.value)}
              />
            </label>

            <div className="editor-footer">
              <span>{code.length.toLocaleString()} characters</span>
              <button
                onClick={runReview}
                disabled={busy || !code.trim()}
              >
                {busy ? 'Reviewing…' : 'Run code review →'}
              </button>
            </div>
          </div>

          <div className="results">
            <div className="panel result-panel">
              <p className="eyebrow">02 / RESULTS</p>
              <h2>Review findings</h2>

              {!review && (
                <div className="empty">
                  <div className="empty-icon">⌘</div>
                  <strong>Your review will appear here</strong>
                  <p>
                    Run an analysis to see severity-ranked findings and
                    suggested improvements.
                  </p>
                </div>
              )}

              {review && (
                <>
                  <div className="summary">
                    <span className="summary-number">
                      {review.findings.length}
                    </span>
                    <div>
                      <strong>Finding(s) reported</strong>
                      <p>{review.summary}</p>
                    </div>
                  </div>

                  {review.findings.length === 0 && (
                    <p className="muted">
                      No findings were reported. This does not guarantee the
                      code is bug-free.
                    </p>
                  )}

                  {review.findings.map((f, i) => (
                    <article
                      className="finding"
                      key={`${f.source}-${f.rule_id}-${i}`}
                    >
                      <div className="finding-top">
                        <span className={`severity ${f.severity}`}>
                          {f.severity}
                        </span>
                        <span className="source">
                          {f.source}
                          {f.line ? ` · line ${f.line}` : ''}
                        </span>
                      </div>

                      <h3>{f.title}</h3>
                      <p>{f.message}</p>

                      {f.suggestion && (
                        <div className="suggestion">
                          <strong>Suggestion</strong>
                          <p>{f.suggestion}</p>
                        </div>
                      )}
                    </article>
                  ))}
                </>
              )}
            </div>
          </div>
        </section>
      )}

      {error && (
        <div className="notice" role="alert" aria-live="polite">
          {error}
        </div>
      )}

      <footer>
        <span>ReviewPilot · Built for safer code</span>
        <span>AI suggestions are advisory; always verify findings.</span>
      </footer>
    </main>
  )
}
