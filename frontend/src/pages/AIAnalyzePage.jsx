import { useState } from 'react';
import { Brain, Loader, AlertCircle, Zap } from 'lucide-react';
import { incidentsAPI } from '../api';

const SEV_COLORS = { Critical:'#ef4444', High:'#f97316', Medium:'#eab308', Low:'#22c55e' };

const INCIDENT_EXAMPLES = [
  { label:'Brute Force', text:'Multiple failed authentication attempts detected against admin account. 500 failed login attempts from IP 10.0.0.1 in last 30 minutes.' },
  { label:'Ransomware', text:'Ransomware detected on production server. Files encrypted with .locked extension and ransom note found. LockBit variant suspected.' },
  { label:'Phishing', text:'Phishing email campaign detected targeting HR employees. Fraudulent email impersonating CEO requesting credential submission.' },
  { label:'Data Exfil', text:'Unauthorized large data transfer detected. 4GB of sensitive customer PII data transferred to external server via FTP.' },
];

export default function AIAnalyzePage() {
  const [description, setDescription] = useState('');
  const [eventType, setEventType] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const analyze = async () => {
    if (!description.trim()) return;
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const r = await incidentsAPI.classify({ description, event_type: eventType });
      setResult(r.data);
    } catch (e) {
      setError(e.response?.data?.detail || 'Classification failed');
    } finally { setLoading(false); }
  };

  const scoreColor = result ? SEV_COLORS[result.recommended_severity] : '#6b7280';

  return (
    <div className="page-container">
      <div className="page-header">
        <div className="page-header-left">
          <h1>AI Incident Analyzer</h1>
          <p>Rule-based ML classification engine with severity scoring and AI recommendations</p>
        </div>
        <div className="ai-badge">🤖 AI Engine v3.0</div>
      </div>

      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:20 }}>
        {/* Input */}
        <div>
          <div className="card" style={{ marginBottom:16 }}>
            <div className="card-header"><span className="card-title"><Brain size={16} /> Incident Description</span></div>
            <div className="card-body">
              <div className="form-group">
                <label className="form-label">Alert / Incident Description *</label>
                <textarea id="ai-description" className="form-control" rows={6}
                  placeholder="Describe the security incident or paste alert text..."
                  value={description} onChange={e => setDescription(e.target.value)} />
              </div>
              <div className="form-group">
                <label className="form-label">Event Type (optional)</label>
                <input className="form-control" placeholder="e.g. Failed Authentication, Malware Detected..."
                  value={eventType} onChange={e => setEventType(e.target.value)} />
              </div>
              {error && <div className="alert alert-error"><AlertCircle size={14} />{error}</div>}
              <button id="analyze-btn" className="btn btn-primary" style={{ width:'100%' }} onClick={analyze} disabled={loading || !description.trim()}>
                {loading ? <><Loader size={15} className="spin" /> Analyzing…</> : <><Brain size={15} /> Analyze with AI</>}
              </button>
            </div>
          </div>

          {/* Examples */}
          <div className="card">
            <div className="card-header"><span className="card-title">💡 Quick Examples</span></div>
            <div className="card-body" style={{ display:'flex', flexDirection:'column', gap:8 }}>
              {INCIDENT_EXAMPLES.map(ex => (
                <button key={ex.label} className="btn btn-secondary btn-sm" style={{ textAlign:'left', justifyContent:'flex-start' }}
                  onClick={() => setDescription(ex.text)}>
                  <span style={{ fontWeight:700, marginRight:8 }}>{ex.label}:</span>
                  <span style={{ fontSize:11, color:'var(--text-muted)', overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>{ex.text.slice(0,60)}…</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Results */}
        <div>
          {!result && !loading && (
            <div className="empty-state" style={{ padding:'80px 24px' }}>
              <div className="empty-state-icon">🤖</div>
              <h3>Ready to Analyze</h3>
              <p>Enter an incident description and click Analyze to get AI classification, severity scoring, and response recommendations.</p>
            </div>
          )}

          {loading && (
            <div className="empty-state" style={{ padding:'80px 24px' }}>
              <div style={{ fontSize:40, marginBottom:16 }}>⚙️</div>
              <h3>Analyzing Incident…</h3>
              <p>Running classification engine and generating recommendations</p>
            </div>
          )}

          {result && (
            <div style={{ display:'flex', flexDirection:'column', gap:16 }}>
              {/* Classification Result */}
              <div className="card" style={{ borderTop:`4px solid ${scoreColor}` }}>
                <div className="card-header"><span className="card-title">Classification Result</span></div>
                <div className="card-body">
                  <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:16, marginBottom:16 }}>
                    <div style={{ padding:16, background:'var(--bg-glass)', border:'1px solid var(--border)', borderRadius:8 }}>
                      <div style={{ fontSize:11, color:'var(--text-muted)', textTransform:'uppercase', marginBottom:6 }}>Incident Type</div>
                      <div style={{ fontSize:15, fontWeight:700 }}>{result.incident_type}</div>
                    </div>
                    <div style={{ padding:16, background:'var(--bg-glass)', border:'1px solid var(--border)', borderRadius:8 }}>
                      <div style={{ fontSize:11, color:'var(--text-muted)', textTransform:'uppercase', marginBottom:6 }}>Confidence</div>
                      <div style={{ fontSize:15, fontWeight:700, fontFamily:'var(--font-mono)', color:'var(--accent-blue)' }}>
                        {(result.confidence * 100).toFixed(1)}%
                      </div>
                    </div>
                    <div style={{ padding:16, background:`${scoreColor}15`, border:`1px solid ${scoreColor}40`, borderRadius:8 }}>
                      <div style={{ fontSize:11, color:'var(--text-muted)', textTransform:'uppercase', marginBottom:6 }}>Recommended Severity</div>
                      <div style={{ fontSize:15, fontWeight:700, color:scoreColor }}>{result.recommended_severity}</div>
                    </div>
                    <div style={{ padding:16, background:'var(--bg-glass)', border:'1px solid var(--border)', borderRadius:8 }}>
                      <div style={{ fontSize:11, color:'var(--text-muted)', textTransform:'uppercase', marginBottom:6 }}>Escalation Risk</div>
                      <div style={{ fontSize:15, fontWeight:700, fontFamily:'var(--font-mono)', color: result.escalation_risk >= 70?'#ef4444':result.escalation_risk >= 50?'#f97316':'#22c55e' }}>
                        {result.escalation_risk?.toFixed(0)}%
                      </div>
                    </div>
                  </div>
                  <div style={{ padding:12, background:'var(--bg-glass)', borderRadius:8, fontSize:13, color:'var(--text-muted)' }}>
                    <strong>Reasoning: </strong>{result.reasoning}
                  </div>
                </div>
              </div>

              {/* AI Recommendation */}
              <div className="card">
                <div className="card-header"><span className="card-title">🤖 AI Response Recommendations</span></div>
                <div className="card-body">
                  <div className="ai-recommendation">
                    <div className="ai-recommendation-body">{result.ai_recommendation}</div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
