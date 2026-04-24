import { useState, useEffect } from 'react';
import { X, Brain, AlertTriangle, Loader, ChevronDown } from 'lucide-react';
import { incidentsAPI, alertsAPI, assetsAPI } from '../api';

const SOURCES = ['SIEM','Firewall','Manual','IDS/IPS','EDR','API'];

export default function CreateIncidentModal({ onClose, onCreated }) {
  const [step, setStep] = useState(1); // 1=details, 2=scoring, 3=review
  const [alerts, setAlerts] = useState([]);
  const [assets, setAssets] = useState([]);
  const [preview, setPreview] = useState(null);
  const [classifying, setClassifying] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const [form, setForm] = useState({
    title: '',
    description: '',
    alert_id: '',
    source_ip: '',
    notes: '',
    asset_criticality: 5,
    threat_confidence: 5,
    impact_level: 5,
    detection_confidence: 5,
  });

  useEffect(() => {
    Promise.all([alertsAPI.list(), assetsAPI.list()])
      .then(([a, as]) => { setAlerts(a.data); setAssets(as.data); })
      .catch(console.error);
  }, []);

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const runClassify = async () => {
    if (!form.description.trim()) return;
    setClassifying(true);
    try {
      const r = await incidentsAPI.classify({ description: form.description });
      setPreview(r.data);
    } catch (e) { console.error(e); }
    finally { setClassifying(false); }
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    setError('');
    try {
      const payload = {
        title: form.title,
        description: form.description,
        alert_id: form.alert_id ? parseInt(form.alert_id) : undefined,
        source_ip: form.source_ip || undefined,
        notes: form.notes || undefined,
        asset_criticality: parseFloat(form.asset_criticality),
        threat_confidence: parseFloat(form.threat_confidence),
        impact_level: parseFloat(form.impact_level),
        detection_confidence: parseFloat(form.detection_confidence),
      };
      await incidentsAPI.create(payload);
      onCreated();
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to create incident');
    } finally { setSubmitting(false); }
  };

  const ScoreSlider = ({ label, field, weight }) => (
    <div className="form-group">
      <label className="form-label">
        {label} <span style={{ color:'var(--text-muted)', fontWeight:400 }}>— weight {weight}</span>
      </label>
      <div className="slider-container">
        <input type="range" className="range-input" min={1} max={10} step={0.5}
          value={form[field]} onChange={e => set(field, e.target.value)} />
        <span className="range-value">{parseFloat(form[field]).toFixed(1)}</span>
      </div>
      <div className="form-hint">
        {form[field] <= 3 ? 'Low' : form[field] <= 6 ? 'Moderate' : form[field] <= 8 ? 'High' : 'Critical'} — {form[field]}/10
      </div>
    </div>
  );

  const SEV_COLORS = { Critical:'#ef4444', High:'#f97316', Medium:'#eab308', Low:'#22c55e' };

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal modal-wide">
        {/* Header */}
        <div className="modal-header">
          <div className="modal-title">
            <AlertTriangle size={20} style={{ color:'var(--accent-blue)' }} />
            Create New Incident
            <span style={{ display:'flex', gap:6, marginLeft:8 }}>
              {[1,2,3].map(s => (
                <span key={s} style={{
                  width:24, height:24, borderRadius:'50%', display:'flex', alignItems:'center',
                  justifyContent:'center', fontSize:11, fontWeight:700,
                  background: step >= s ? 'var(--accent-blue)' : 'var(--bg-3)',
                  color: step >= s ? 'white' : 'var(--text-muted)',
                }}>{s}</span>
              ))}
            </span>
          </div>
          <button className="modal-close" onClick={onClose}><X size={16} /></button>
        </div>

        <div className="modal-body">
          {error && <div className="alert alert-error" style={{ marginBottom:16 }}>{error}</div>}

          {/* Step 1: Incident Details */}
          {step === 1 && (
            <div>
              <div className="form-group">
                <label className="form-label">Incident Title *</label>
                <input id="incident-title" className="form-control" placeholder="e.g. Brute Force Attack on Admin Account"
                  value={form.title} onChange={e => set('title', e.target.value)} required />
              </div>

              <div className="form-group">
                <label className="form-label">Description *</label>
                <textarea id="incident-desc" className="form-control" rows={4}
                  placeholder="Describe the security incident in detail. Include: what happened, when, which systems were affected, any indicators of compromise..."
                  value={form.description} onChange={e => set('description', e.target.value)} required />
                <div className="form-hint">The AI engine will use this to auto-classify the incident type.</div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Linked Alert (optional)</label>
                  <select className="form-control" value={form.alert_id} onChange={e => set('alert_id', e.target.value)}>
                    <option value="">— None —</option>
                    {alerts.filter(a => !a.is_processed).map(a => (
                      <option key={a.id} value={a.id}>[{a.source}] {a.event_type} — {a.alert_id}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Source IP (optional)</label>
                  <input className="form-control" placeholder="e.g. 203.0.113.45"
                    value={form.source_ip} onChange={e => set('source_ip', e.target.value)} />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Notes (optional)</label>
                <textarea className="form-control" rows={2} placeholder="Initial analyst notes..."
                  value={form.notes} onChange={e => set('notes', e.target.value)} />
              </div>

              {/* AI Preview */}
              <div style={{ display:'flex', gap:10, alignItems:'center', marginBottom:16 }}>
                <button type="button" className="btn btn-secondary btn-sm" onClick={runClassify}
                  disabled={classifying || !form.description.trim()}>
                  {classifying ? <><Loader size={13} /> Classifying…</> : <><Brain size={13} /> Preview AI Classification</>}
                </button>
              </div>

              {preview && (
                <div className="ai-recommendation" style={{ marginBottom:8 }}>
                  <div style={{ display:'flex', gap:16, flexWrap:'wrap', marginBottom:12 }}>
                    <div>
                      <div style={{ fontSize:11, color:'var(--text-muted)', marginBottom:3 }}>DETECTED TYPE</div>
                      <div style={{ fontWeight:700, fontSize:14 }}>{preview.incident_type}</div>
                    </div>
                    <div>
                      <div style={{ fontSize:11, color:'var(--text-muted)', marginBottom:3 }}>CONFIDENCE</div>
                      <div style={{ fontWeight:700, fontSize:14, fontFamily:'var(--font-mono)', color:'var(--accent-blue)' }}>{(preview.confidence*100).toFixed(1)}%</div>
                    </div>
                    <div>
                      <div style={{ fontSize:11, color:'var(--text-muted)', marginBottom:3 }}>RECOMMENDED SEVERITY</div>
                      <div style={{ fontWeight:700, fontSize:14, color:SEV_COLORS[preview.recommended_severity] }}>{preview.recommended_severity}</div>
                    </div>
                    <div>
                      <div style={{ fontSize:11, color:'var(--text-muted)', marginBottom:3 }}>ESCALATION RISK</div>
                      <div style={{ fontWeight:700, fontSize:14, fontFamily:'var(--font-mono)', color: preview.escalation_risk >= 70?'#ef4444':preview.escalation_risk >= 50?'#f97316':'#22c55e' }}>{preview.escalation_risk?.toFixed(0)}%</div>
                    </div>
                  </div>
                  <div style={{ fontSize:12, color:'var(--text-muted)' }}>📋 {preview.reasoning}</div>
                </div>
              )}
            </div>
          )}

          {/* Step 2: Severity Scoring */}
          {step === 2 && (
            <div>
              <div style={{ padding:'12px 16px', background:'rgba(59,130,246,0.08)', border:'1px solid rgba(59,130,246,0.2)', borderRadius:8, marginBottom:20, fontSize:13, color:'var(--text-secondary)', lineHeight:1.7 }}>
                <strong>Severity Formula:</strong> Score = (Asset Criticality × 0.30) + (Threat Confidence × 0.30) + (Impact Level × 0.20) + (Detection Confidence × 0.20) × 10
              </div>
              <ScoreSlider label="Asset Criticality" field="asset_criticality" weight="30%" />
              <ScoreSlider label="Threat Confidence" field="threat_confidence" weight="30%" />
              <ScoreSlider label="Impact Level" field="impact_level" weight="20%" />
              <ScoreSlider label="Detection Confidence" field="detection_confidence" weight="20%" />

              {/* Live Score Preview */}
              {(() => {
                const raw = (parseFloat(form.asset_criticality)*0.30 + parseFloat(form.threat_confidence)*0.30 + parseFloat(form.impact_level)*0.20 + parseFloat(form.detection_confidence)*0.20) * 10;
                const score = Math.min(Math.round(raw), 100);
                const level = score >= 80 ? 'Critical' : score >= 60 ? 'High' : score >= 40 ? 'Medium' : 'Low';
                const color = SEV_COLORS[level];
                return (
                  <div style={{ textAlign:'center', padding:20, background:`${color}10`, border:`1px solid ${color}30`, borderRadius:10, marginTop:8 }}>
                    <div style={{ fontSize:48, fontWeight:900, fontFamily:'var(--font-mono)', color, lineHeight:1 }}>{score}</div>
                    <div style={{ fontSize:13, color:'var(--text-muted)', marginTop:6 }}>Estimated Score → <strong style={{ color }}>{level}</strong></div>
                    <div style={{ height:6, background:'var(--bg-3)', borderRadius:3, overflow:'hidden', marginTop:12 }}>
                      <div style={{ width:`${score}%`, height:'100%', background:color, borderRadius:3, transition:'width 0.3s' }} />
                    </div>
                  </div>
                );
              })()}
            </div>
          )}

          {/* Step 3: Review */}
          {step === 3 && (
            <div>
              <div style={{ padding:16, background:'var(--bg-glass)', border:'1px solid var(--border)', borderRadius:8, marginBottom:16 }}>
                <div style={{ fontWeight:700, fontSize:15, marginBottom:12 }}>{form.title}</div>
                <div style={{ fontSize:13, color:'var(--text-muted)', lineHeight:1.7, marginBottom:12 }}>{form.description}</div>
                {form.source_ip && <div style={{ fontSize:12 }}>Source IP: <span style={{ fontFamily:'var(--font-mono)', color:'var(--accent-cyan)' }}>{form.source_ip}</span></div>}
              </div>
              <div style={{ display:'grid', gridTemplateColumns:'repeat(2,1fr)', gap:12 }}>
                {[
                  ['Asset Criticality', form.asset_criticality, '30%'],
                  ['Threat Confidence', form.threat_confidence, '30%'],
                  ['Impact Level', form.impact_level, '20%'],
                  ['Detection Confidence', form.detection_confidence, '20%'],
                ].map(([label, val, weight]) => (
                  <div key={label} style={{ padding:'10px 14px', background:'var(--bg-glass)', border:'1px solid var(--border)', borderRadius:8 }}>
                    <div style={{ fontSize:11, color:'var(--text-muted)', marginBottom:4 }}>{label} ({weight})</div>
                    <div style={{ fontFamily:'var(--font-mono)', fontWeight:700, fontSize:18, color:'var(--accent-blue)' }}>{val}/10</div>
                  </div>
                ))}
              </div>
              <div style={{ marginTop:16, padding:12, background:'rgba(16,185,129,0.08)', border:'1px solid rgba(16,185,129,0.2)', borderRadius:8, fontSize:13, color:'#6ee7b7' }}>
                ✅ AI will auto-classify this incident upon creation and generate response recommendations.
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="modal-footer">
          {step > 1 && <button className="btn btn-secondary" onClick={() => setStep(s => s-1)}>← Back</button>}
          <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
          {step < 3 && (
            <button className="btn btn-primary" disabled={step===1 && (!form.title.trim() || !form.description.trim())}
              onClick={() => setStep(s => s+1)}>
              Next →
            </button>
          )}
          {step === 3 && (
            <button id="submit-incident-btn" className="btn btn-primary" onClick={handleSubmit} disabled={submitting}>
              {submitting ? <><Loader size={14} /> Creating…</> : '🛡️ Create Incident'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
