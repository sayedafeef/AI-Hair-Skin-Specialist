import { useEffect, useState } from 'react'
import { fetchHistory } from './api.js'
import { useAuth } from './AuthContext.jsx'

export default function HistoryPage() {
  const { token } = useAuth()
  const [records, setRecords] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    fetchHistory(token)
      .then((data) => {
        if (!cancelled) setRecords(data)
      })
      .catch((err) => {
        if (!cancelled) setError(err.message)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [token])

  return (
    <div className="history-page">
      <h2>Your consultation history</h2>

      {loading && <p className="intro">Loading…</p>}
      {error && <p className="error">{error}</p>}
      {!loading && !error && records.length === 0 && (
        <p className="intro">You haven't had a consultation yet.</p>
      )}

      <div className="history-list">
        {records.map((r) => (
          <div key={r.id} className="history-item">
            <div className="history-item-header">
              <span className={`badge badge-${r.specialty}`}>
                {r.specialty === 'skin' ? 'Skin specialist' : 'Hair specialist'}
              </span>
              <span className="history-date">{new Date(r.created_at).toLocaleString()}</span>
            </div>
            <p>
              <strong>You said:</strong> {r.transcript}
            </p>
            <p>
              <strong>Guidance:</strong> {r.specialist_response}
            </p>
            {r.audioUrl && <audio controls src={r.audioUrl} />}
          </div>
        ))}
      </div>
    </div>
  )
}
