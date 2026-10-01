import { useRef, useState } from 'react'
import { submitConsultation } from './api.js'
import { useAuth } from './AuthContext.jsx'

export default function ConsultationPage({ pageTitle, pageDescription, mediaLabel }) {
  const { token } = useAuth()
  const [isRecording, setIsRecording] = useState(false)
  const [audioBlob, setAudioBlob] = useState(null)
  const [audioPreviewUrl, setAudioPreviewUrl] = useState(null)
  const [imageFile, setImageFile] = useState(null)
  const [videoFile, setVideoFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)

  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])

  const startRecording = async () => {
    setError(null)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream)
      chunksRef.current = []

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        setAudioBlob(blob)
        setAudioPreviewUrl(URL.createObjectURL(blob))
        stream.getTracks().forEach((track) => track.stop())
      }

      recorder.start()
      mediaRecorderRef.current = recorder
      setIsRecording(true)
    } catch (err) {
      setError('Could not access microphone: ' + err.message)
    }
  }

  const stopRecording = () => {
    mediaRecorderRef.current?.stop()
    setIsRecording(false)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setResult(null)

    if (!audioBlob) {
      setError('Please record your voice description first.')
      return
    }
    if (!imageFile && !videoFile) {
      setError(`Please upload a ${mediaLabel.toLowerCase()} or a video.`)
      return
    }

    setLoading(true)
    try {
      const data = await submitConsultation({ audioBlob, imageFile, videoFile, token })
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="layout-grid">
      <div className="form-panel">
        <h2>{pageTitle}</h2>
        <p className="intro">{pageDescription}</p>

        <form onSubmit={handleSubmit} className="consultation-form">
          <section className="field">
            <label>Describe your concern</label>
            <div className="recorder-controls">
              {!isRecording ? (
                <button type="button" onClick={startRecording}>
                  Start recording
                </button>
              ) : (
                <button type="button" className="recording" onClick={stopRecording}>
                  <span className="pulse-dot" />
                  Stop recording
                </button>
              )}
              {audioPreviewUrl && <audio controls src={audioPreviewUrl} />}
            </div>
          </section>

          <section className="field">
            <label>{mediaLabel}</label>
            <input
              type="file"
              accept="image/*"
              onChange={(e) => setImageFile(e.target.files?.[0] || null)}
            />
          </section>

          <section className="field">
            <label>{mediaLabel}, video (optional)</label>
            <input
              type="file"
              accept="video/*"
              onChange={(e) => setVideoFile(e.target.files?.[0] || null)}
            />
          </section>

          {error && <p className="error">{error}</p>}

          <button type="submit" className="primary" disabled={loading}>
            {loading ? 'Analyzing…' : 'Analyze concern'}
          </button>
        </form>
      </div>

      <div className="results-panel">
        {!result && !loading && (
          <div className="empty-state">
            <p>Your specialist's guidance will appear here once you submit a consultation.</p>
          </div>
        )}

        {loading && (
          <div className="empty-state">
            <p>Reading your description and photo now.</p>
          </div>
        )}

        {result && (
          <div className="result">
            <p className={`badge badge-${result.specialty}`}>
              Routed to {result.specialty === 'skin' ? 'skin specialist' : 'hair specialist'}
            </p>
            <div className="result-block">
              <h3>Your transcript</h3>
              <p>{result.transcript}</p>
            </div>
            <div className="result-block">
              <h3>Specialist guidance</h3>
              <p>{result.specialist_response}</p>
            </div>
            <div className="result-block">
              <h3>Voice response</h3>
              <audio controls autoPlay src={result.audioUrl} />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
