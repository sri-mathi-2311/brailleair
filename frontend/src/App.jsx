import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Activity, Battery, BookOpenText, Cable, CirclePause, CirclePlay, Square, Thermometer, Upload, Link as LinkIcon, Camera, Columns2, Trash2 } from 'lucide-react';
import './App.css';

const API_BASE = 'http://localhost:8000';

function BrailleDot({ active }) {
  return (
    <div className={`braille-dot ${active ? 'active' : ''}`} />
  );
}

function BrailleChar({ char, dots }) {
  return (
    <div className="braille-char-container">
      <div className="braille-char-label">{char}</div>
      <div className="braille-dots">
        {dots.map((active, i) => (
          <BrailleDot key={i} active={active === 1} />
        ))}
      </div>
    </div>
  );
}

function App() {
  const [file, setFile] = useState(null);
  const [urlInput, setUrlInput] = useState('');
  const [resource, setResource] = useState(null);
  const [resources, setResources] = useState([]);
  const [session, setSession] = useState(null);
  const [wpm, setWpm] = useState(120);
  const [telemetry, setTelemetry] = useState(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('Ready');

  // ESP32 State
  const [espResult, setEspResult] = useState(null);

  // Braille encoding for current session word
  const [sessionBraille, setSessionBraille] = useState(null);

  const loadResources = async () => {
    try {
      const response = await axios.get(`${API_BASE}/online/resources`);
      setResources(response.data.resources || []);
    } catch (err) {
      console.error(err);
    }
  };

  const deleteResource = async (resourceId) => {
    if (!window.confirm("Are you sure you want to delete this resource?")) return;
    setBusy(true);
    try {
      await axios.delete(`${API_BASE}/online/resources/${resourceId}`);
      setMessage('Resource deleted.');
      await loadResources();
      if (session?.resource_id === resourceId) {
        setSession(null);
        setSessionBraille(null);
      }
    } catch (err) {
      setMessage(`Delete failed: ${err?.response?.data?.detail || err.message}`);
    } finally {
      setBusy(false);
    }
  };

  const loadTelemetry = async () => {
    try {
      const response = await axios.get(`${API_BASE}/online/telemetry/glove`);
      setTelemetry(response.data);
    } catch (err) {
      console.error(err);
    }
  };

  const loadSession = async (sessionId) => {
    try {
      const response = await axios.get(`${API_BASE}/online/sessions/${sessionId}`);
      setSession(response.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadResources();
    loadTelemetry();
  }, []);

  useEffect(() => {
    const timer = setInterval(() => {
      loadTelemetry();
      if (session?.session_id && (session.status === 'running' || session.status === 'paused')) {
        loadSession(session.session_id);
      }
    }, 200);

    return () => clearInterval(timer);
  }, [session?.session_id, session?.status]);

  // Fetch Braille encoding whenever the current word changes
  useEffect(() => {
    if (!session?.current_word) return;
    const word = session.current_word;
    const lang = /[\u0B80-\u0BFF]/.test(word) ? 'ta' : 'en';
    axios
      .get(`${API_BASE}/online/encode`, { params: { text: word, lang } })
      .then((res) => setSessionBraille(res.data))
      .catch(() => setSessionBraille(null));
  }, [session?.current_word]);

  const uploadFile = async () => {
    if (!file) return;
    setBusy(true);
    setMessage('Uploading file and extracting words...');
    const formData = new FormData();
    formData.append('file', file);
    try {
      const response = await axios.post(`${API_BASE}/online/upload-resource`, formData);
      setResource(response.data);
      setMessage(`Resource ready: ${response.data.total_words} words`);
      await loadResources();
    } catch (err) {
      setMessage(`Upload failed: ${err?.response?.data?.detail || err.message}`);
    } finally {
      setBusy(false);
    }
  };

  const addUrl = async () => {
    if (!urlInput.trim()) return;
    setBusy(true);
    setMessage('Fetching URL...');
    try {
      const response = await axios.post(`${API_BASE}/online/add-link`, { url: urlInput.trim() });
      setResource(response.data);
      setMessage(`Resource ready: ${response.data.total_words} words`);
      await loadResources();
    } catch (err) {
      setMessage(`URL failed: ${err?.response?.data?.detail || err.message}`);
    } finally {
      setBusy(false);
    }
  };

  const captureEsp32 = async () => {
    setBusy(true);
    setEspResult(null);
    setMessage('Requesting image from ESP32 camera...');
    try {
      const response = await axios.get(`${API_BASE}/online/capture-esp32`);
      setEspResult(response.data);
      setMessage('ESP32 Capture & OCR complete!');
    } catch (err) {
      setMessage(`ESP32 Capture failed: ${err?.response?.data?.detail || err.message}`);
    } finally {
      setBusy(false);
    }
  };

  const startSession = async (resourceId) => {
    setBusy(true);
    try {
      const response = await axios.post(`${API_BASE}/online/sessions/start`, {
        resource_id: resourceId,
        wpm,
      });
      setSession(response.data);
      setMessage('Reading session started.');
    } catch (err) {
      setMessage(`Start failed: ${err?.response?.data?.detail || err.message}`);
    } finally {
      setBusy(false);
    }
  };

  const controlSession = async (action) => {
    if (!session?.session_id) return;
    setBusy(true);
    try {
      const response = await axios.post(`${API_BASE}/online/sessions/${session.session_id}/${action}`);
      setSession(response.data);
      setMessage(`Session ${action} successful`);
    } catch (err) {
      setMessage(`Session ${action} failed: ${err?.response?.data?.detail || err.message}`);
    } finally {
      setBusy(false);
    }
  };

  const updateSpeed = async (newWpm) => {
    setWpm(newWpm);
    if (!session?.session_id) return;
    try {
      const response = await axios.post(`${API_BASE}/online/sessions/${session.session_id}/speed`, {
        wpm: newWpm
      });
      setSession(response.data);
    } catch (err) {
      console.error('Failed to update speed:', err);
    }
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <h1>BrailleAir Control Center</h1>
        <div className="status-pill">{busy ? 'Working...' : message}</div>
      </header>

      <section className="grid telemetry-grid">
        <div className="card">
          <h3><Cable size={18} /> Connection</h3>
          <p className={telemetry?.connected ? 'ok' : 'bad'}>{telemetry?.connected ? 'Glove Connected' : 'Glove Offline'}</p>
        </div>
        <div className="card">
          <h3><Battery size={18} /> Battery</h3>
          <p>{telemetry?.battery_pct ?? '--'}%</p>
          <small>{telemetry?.charging ? 'Charging' : 'On Battery'}</small>
        </div>
        <div className="card">
          <h3><Thermometer size={18} /> Thermal</h3>
          <p>{telemetry?.temperature_c ?? '--'}°C</p>
          <small className={telemetry?.safety?.temperature_alert ? 'bad' : 'ok'}>
            {telemetry?.safety?.temperature_alert ? 'Overheated' : 'Normal'}
          </small>
        </div>
        <div className="card">
          <h3><Activity size={18} /> Firmware</h3>
          <p>{telemetry?.firmware_version || '--'}</p>
          <small>Status: Ok</small>
        </div>
      </section>

      <div className="main-layout">
        <aside className="left-panel">
          <div className="card">
            <h2><Camera size={20} /> Remote Capture</h2>
            <p className="muted">Bridge to ESP32-CAM module portal.</p>
            <button className="primary-btn full-width" onClick={captureEsp32} disabled={busy}>
              <Camera size={18} /> Single Capture
            </button>
          </div>

          <div className="card">
            <h2>Settings</h2>
            <div className="speed-row" style={{ marginTop: '10px' }}>
              <label>Reading Speed (WPM):</label>
              <input 
                type="range" 
                min="30" 
                max="300" 
                step="10" 
                value={wpm} 
                onChange={(e) => updateSpeed(Number(e.target.value))} 
              />
              <span>{wpm}</span>
            </div>
            <p className="muted" style={{ fontSize: '0.8rem', marginTop: '8px' }}>
              Changes will apply to new and active sessions instantly.
            </p>
          </div>

          <div className="card tall">
            <h2>Library</h2>
            <div className="upload-row">
              <input type="file" onChange={(e) => setFile(e.target.files?.[0] || null)} />
              <button className="secondary-btn" onClick={uploadFile} disabled={!file || busy}><Upload size={16} /></button>
            </div>
            <div className="upload-row">
              <input
                type="url"
                placeholder="Article URL..."
                value={urlInput}
                onChange={(e) => setUrlInput(e.target.value)}
              />
              <button className="secondary-btn" onClick={addUrl} disabled={!urlInput.trim() || busy}><LinkIcon size={16} /></button>
            </div>

            <div className="list-box">
              {resources.map((item) => (
                <div key={item.resource_id} className="list-item">
                  <div style={{maxWidth: '180px', overflow: 'hidden'}}>
                    <strong>{item.source_name}</strong>
                    <p className="muted">{item.total_words} words</p>
                  </div>
                  <div style={{ display: 'flex', gap: '8px', zIndex: 10 }}>
                    <button className="secondary-btn" onClick={() => startSession(item.resource_id)} disabled={busy}>Read</button>
                    <button 
                      className="secondary-btn" 
                      style={{ color: 'var(--danger)', borderColor: 'var(--danger)', padding: '8px' }} 
                      onClick={() => deleteResource(item.resource_id)} 
                      disabled={busy}
                      title="Delete Resource"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </aside>

        <main className="right-panel">
          <div className="card tall split-viewer">
            <h2><Columns2 size={20} /> Live Processor</h2>
            
            {!espResult && !session && (
              <div className="center-message">
                <p className="muted">No active data stream.</p>
                <small>Run a capture or select a book to begin.</small>
              </div>
            )}
            
            {(espResult || session) && (
              <div className="split-columns">
                <section className="text-column">
                  <h3>Real Text</h3>
                  <div className="text-display">
                    {espResult?.final_text ? (
                      espResult.final_text
                    ) : session?.current_word ? (
                      <span className="current-word-display">{session.current_word}</span>
                    ) : (
                      <span className="muted">Awaiting signal...</span>
                    )}
                  </div>
                  {session && !espResult && (
                    <div className="session-word-info">
                      <span className="muted">Word {session.current_word_index} of {session.total_words}</span>
                    </div>
                  )}
                </section>
                <section className="braille-column">
                  <h3>Braille Patterns</h3>
                  <div className="braille-display">
                    {(() => {
                      const seq = espResult?.vibration_seq ?? sessionBraille?.vibration_seq ?? [];
                      return seq
                        .filter(step => step.char !== ' ')
                        .map((step, idx) => (
                          <BrailleChar key={idx} char={step.char} dots={step.dots} />
                        ));
                    })()}
                    {!espResult && !sessionBraille && session && (
                      <p className="muted">Loading braille...</p>
                    )}
                  </div>
                </section>
              </div>
            )}

          </div>

          {session && (
            <div className="card">
              <div className="session-stats">
                <span>Progress: {session.progress_pct}%</span>
                <span>Speed: {session.wpm} WPM</span>
              </div>
              <div className="control-row">
                <button className="control-btn" onClick={() => controlSession('resume')} disabled={busy || session.status === 'running'}><CirclePlay size={22} /></button>
                <button className="control-btn" onClick={() => controlSession('pause')} disabled={busy || session.status !== 'running'}><CirclePause size={22} /></button>
                <button className="control-btn stop" onClick={() => controlSession('stop')} disabled={busy || session.status === 'stopped'}><Square size={22} /></button>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
