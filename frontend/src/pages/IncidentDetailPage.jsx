import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Edit2, CheckCircle2, Play, ChevronRight, Loader, AlertTriangle, Brain, Clock } from 'lucide-react';
import { incidentsAPI, playbooksAPI } from '../api';

const SEV_COLORS = { Critical:'#ef4444', High:'#f97316', Medium:'#eab308', Low:'#22c55e' };
const STATUS_OPTIONS = ['Open','Investigating','Contained','Resolved','Closed'];
const SEV_OPTIONS = ['Critical','High','Medium','Low'];

function InfoRow({ label, value }) {
  return (
    <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', padding:'10px 0', borderBottom:'1px solid var(--border)' }}>
      <span style={{ fontSize:12, color:'var(--text-muted)', textTransform:'uppercase', letterSpacing:'0.05em', flexShrink:0, marginRight:12 }}>{label}</span>
      <span style={{ fontSize:13, fontWeight:500, textAlign:'right' }}>{value || '—'}</span>
    </div>
  );
}

export default function IncidentDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [incident, setIncident] = useState(null);
  const [playbooks, setPlaybooks] = useState([]);
  const [executions, setExecutions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [editStatus, setEditStatus] = useState('');
  const [editSev, setEditSev] = useState('');

  useEffect(() => {
    Promise.all([
      incidentsAPI.get(id),
      playbooksAPI.list(),
      playbooksAPI.getExecutions(id),
    ]).then(([inc, pbs, execs]) => {
      setIncident(inc.data);
      setPlaybooks(pbs.data);
      setExecutions(execs.data);
      setEditStatus(inc.data.status);
      setEditSev(inc.data.severity);
    }).catch(console.error).finally(() => setLoading(false));
  }, [id]);

  const handleUpdate = async () => {
    setUpdating(true);
    try {
      const r = await incidentsAPI.update(id, { status: editStatus, severity: editSev });
      setIncident(r.data);
      setEditStatus(r.data.status);
      setEditSev(r.data.severity);
    } catch (e) { console.error(e); }
    finally { setUpdating(false); }
  };

  const handleExecutePlaybook = async (pbId) => {
    try {
      const r = await playbooksAPI.execute(pbId, id);
      setExecutions(prev => [r.data, ...prev]);
      setActiveTab('playbook');
    } catch (e) { console.error(e); }
  };

  const handleStepUpdate = async (execId, stepIdx, status, result = 'Completed') => {
    try {
      const r = await playbooksAPI.updateStep(execId, { step_index: stepIdx, status, result });
      setExecutions(prev => prev.map(e => e.id === execId ? r.data : e));
    } catch (e) { console.error(e); }
  };

  if (loading) return <div className="page-container"><div style={{ padding:60, textAlign:'center', color:'var(--text-muted)' }}>Loading incident…</div></div>;
  if (!incident) return <div className="page-container"><div className="empty-state"><div className="empty-state-icon">❌</div><h3>Incident not found</h3></div></div>;

  const scoreColor = incident.severity_score >= 80?'#ef4444':incident.severity_score >= 60?'#f97316':incident.severity_score >= 40?'#eab308':'#22c55e';
  const matchedPlaybooks = playbooks.filter(pb => pb.incident_type === incident.incident_type);
  const latestExec = executions[0];

  const tabs = [
    { key:'overview', label:'Overview' },
    { key:'ai', label:'🤖 AI Analysis' },
    { key:'playbook', label:`📋 Playbook${latestExec ? ` (${latestExec.status})` : ''}` },
    { key:'scores', label:'📊 Severity Scoring' },
  ];

  return (
    <div className="page-container">
      {/* Header */}
      <div style={{ display:'flex', alignItems:'center', gap:16, marginBottom:24 }}>
        <button className="btn btn-secondary btn-sm" onClick={() => navigate('/incidents')}><ArrowLeft size={14} /> Back</button>
        <div style={{ flex:1 }}>
          <div style={{ display:'flex', alignItems:'center', gap:12, flexWrap:'wrap' }}>
            <span style={{ fontFamily:'var(--font-mono)', fontSize:13, color:'var(--accent-blue)' }}>{incident.incident_id}</span>
            <span className={`severity-badge ${incident.severity?.toLowerCase()}`}>{incident.severity}</span>
            <span className={`status-badge ${incident.status?.toLowerCase().replace(/ /g,'')}`}>{incident.status}</span>
            {incident.escalation_risk >= 70 && <span style={{ fontSize:11, background:'rgba(239,68,68,0.15)', color:'#fca5a5', border:'1px solid rgba(239,68,68,0.3)', padding:'3px 10px', borderRadius:20, fontWeight:700 }}>⚡ HIGH RISK</span>}
          </div>
          <h1 style={{ marginTop:6, fontSize:20, fontWeight:800 }}>{incident.title}</h1>
        </div>
        <div style={{ display:'flex', gap:8 }}>
          <select className="form-control" style={{ width:150 }} value={editStatus} onChange={e => setEditStatus(e.target.value)}>
            {STATUS_OPTIONS.map(s => <option key={s}>{s}</option>)}
          </select>
          <select className="form-control" style={{ width:120 }} value={editSev} onChange={e => setEditSev(e.target.value)}>
            {SEV_OPTIONS.map(s => <option key={s}>{s}</option>)}
          </select>
          <button className="btn btn-primary" onClick={handleUpdate} disabled={updating}>
            {updating ? <Loader size={14} className="spin" /> : <CheckCircle2 size={14} />} Save
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display:'flex', gap:4, marginBottom:20, borderBottom:'1px solid var(--border)', paddingBottom:0 }}>
        {tabs.map(t => (
          <button key={t.key} onClick={() => setActiveTab(t.key)}
            style={{ padding:'10px 18px', background:'none', border:'none', cursor:'pointer', fontSize:13, fontWeight:600, color: activeTab===t.key ? 'var(--accent-blue)' : 'var(--text-muted)', borderBottom: activeTab===t.key ? '2px solid var(--accent-blue)' : '2px solid transparent', transition:'all 0.2s', marginBottom:-1 }}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div style={{ display:'grid', gridTemplateColumns:'1fr 320px', gap:20 }}>
          <div>
            <div className="card" style={{ marginBottom:16 }}>
              <div className="card-header"><span className="card-title">Incident Details</span></div>
              <div className="card-body">
                <InfoRow label="Type" value={incident.incident_type} />
                <InfoRow label="Description" value={incident.description} />
                <InfoRow label="Source IP" value={incident.source_ip} />
                <InfoRow label="Notes" value={incident.notes} />
                <InfoRow label="Created" value={new Date(incident.created_at).toLocaleString()} />
                <InfoRow label="Updated" value={new Date(incident.updated_at).toLocaleString()} />
                {incident.resolved_at && <InfoRow label="Resolved" value={new Date(incident.resolved_at).toLocaleString()} />}
              </div>
            </div>

            {/* Matched Playbooks */}
            {matchedPlaybooks.length > 0 && (
              <div className="card">
                <div className="card-header"><span className="card-title">📋 Recommended Playbooks</span></div>
                <div className="card-body">
                  {matchedPlaybooks.map(pb => (
                    <div key={pb.id} style={{ display:'flex', justifyContent:'space-between', alignItems:'center', padding:'12px 0', borderBottom:'1px solid var(--border)' }}>
                      <div>
                        <div style={{ fontWeight:600, fontSize:14 }}>{pb.name}</div>
                        <div style={{ fontSize:12, color:'var(--text-muted)', marginTop:2 }}>{pb.steps?.length} steps · v{pb.version}</div>
                      </div>
                      <button className="btn btn-success btn-sm" onClick={() => handleExecutePlaybook(pb.id)}>
                        <Play size={13} /> Execute
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Right Sidebar */}
          <div>
            {/* Score Gauge */}
            <div className="card" style={{ marginBottom:16 }}>
              <div className="card-header"><span className="card-title">Severity Score</span></div>
              <div className="card-body" style={{ textAlign:'center' }}>
                <div style={{ fontSize:64, fontWeight:900, fontFamily:'var(--font-mono)', color:scoreColor, lineHeight:1 }}>
                  {incident.severity_score?.toFixed(0)}
                </div>
                <div style={{ fontSize:12, color:'var(--text-muted)', marginTop:6, textTransform:'uppercase', letterSpacing:'0.08em' }}>/ 100</div>
                <div style={{ marginTop:12, height:6, background:'var(--bg-3)', borderRadius:3, overflow:'hidden' }}>
                  <div style={{ width:`${incident.severity_score}%`, height:'100%', background:`linear-gradient(90deg, ${scoreColor}, ${scoreColor}aa)`, borderRadius:3 }} />
                </div>
              </div>
            </div>

            {/* Escalation Risk */}
            <div className="card" style={{ marginBottom:16 }}>
              <div className="card-header"><span className="card-title">Escalation Risk</span></div>
              <div className="card-body" style={{ textAlign:'center' }}>
                <div style={{ fontSize:48, fontWeight:900, fontFamily:'var(--font-mono)', color: incident.escalation_risk >= 70?'#ef4444':incident.escalation_risk >= 50?'#f97316':'#22c55e', lineHeight:1 }}>
                  {incident.escalation_risk?.toFixed(0)}%
                </div>
                <div style={{ height:6, background:'var(--bg-3)', borderRadius:3, overflow:'hidden', marginTop:12 }}>
                  <div style={{ width:`${incident.escalation_risk}%`, height:'100%', background: incident.escalation_risk >= 70?'#ef4444':incident.escalation_risk >= 50?'#f97316':'#22c55e', borderRadius:3 }} />
                </div>
              </div>
            </div>

            {/* Tags */}
            {incident.tags?.length > 0 && (
              <div className="card">
                <div className="card-header"><span className="card-title">Tags</span></div>
                <div className="card-body" style={{ display:'flex', flexWrap:'wrap', gap:8 }}>
                  {incident.tags.map(tag => (
                    <span key={tag} style={{ padding:'4px 10px', background:'var(--bg-3)', border:'1px solid var(--border)', borderRadius:4, fontSize:12, color:'var(--text-secondary)' }}>{tag}</span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* AI Analysis Tab */}
      {activeTab === 'ai' && (
        <div className="card">
          <div className="card-header"><span className="card-title"><Brain size={16} /> AI Recommendation</span></div>
          <div className="card-body">
            <div className="ai-recommendation">
              <div className="ai-recommendation-header">
                <span className="ai-badge">🤖 AI Analysis</span>
                <span style={{ fontSize:12, color:'var(--text-muted)' }}>Type: <strong style={{ color:'var(--text-secondary)' }}>{incident.incident_type}</strong></span>
              </div>
              <div className="ai-recommendation-body">{incident.ai_recommendation || 'No AI recommendation available.'}</div>
            </div>
          </div>
        </div>
      )}

      {/* Playbook Tab */}
      {activeTab === 'playbook' && (
        <div>
          {executions.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">📋</div>
              <h3>No playbooks executed</h3>
              <p>Go to Overview to execute a playbook for this incident.</p>
            </div>
          ) : (
            executions.map(exec => (
              <div key={exec.id} className="card" style={{ marginBottom:16 }}>
                <div className="card-header">
                  <span className="card-title">Playbook Execution #{exec.id}</span>
                  <span className={`status-badge ${exec.status?.toLowerCase().replace(/ /g,'')}`}>{exec.status}</span>
                </div>
                <div className="card-body">
                  <div className="playbook-steps">
                    {exec.step_statuses && Object.entries(exec.step_statuses).map(([idx, step]) => (
                      <div key={idx} className="playbook-step">
                        <div className={`step-number ${step.status === 'completed' ? 'completed' : step.status === 'pending' ? '' : step.status}`}>
                          {step.status === 'completed' ? '✓' : parseInt(idx) + 1}
                        </div>
                        <div className="step-content">
                          <div className="step-title">{step.title}</div>
                          <div className="step-meta">
                            <span className={`step-tag ${step.action_type || 'manual'}`}>{step.action_type || 'manual'}</span>
                            <span className="step-tag" style={{ background:'var(--bg-3)', color:'var(--text-muted)', border:'none' }}>{step.status}</span>
                          </div>
                        </div>
                        {step.status === 'pending' && exec.status !== 'Completed' && (
                          <div style={{ display:'flex', gap:6 }}>
                            <button className="btn btn-success btn-sm" onClick={() => handleStepUpdate(exec.id, parseInt(idx), 'completed')}>✓ Done</button>
                            <button className="btn btn-secondary btn-sm" onClick={() => handleStepUpdate(exec.id, parseInt(idx), 'skipped', 'Skipped')}>Skip</button>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Severity Scores Tab */}
      {activeTab === 'scores' && (
        <div className="card">
          <div className="card-header"><span className="card-title">📊 Severity Scoring Breakdown</span></div>
          <div className="card-body">
            <div style={{ marginBottom:20, padding:16, background:'var(--bg-glass)', border:'1px solid var(--border)', borderRadius:8 }}>
              <p style={{ fontSize:13, color:'var(--text-muted)', lineHeight:1.8 }}>
                <strong>Formula:</strong> Score = (Asset Criticality × 0.30) + (Threat Confidence × 0.30) + (Impact Level × 0.20) + (Detection Confidence × 0.20)<br/>
                Normalised to 0–100 scale. Score ≥80 → Critical, ≥60 → High, ≥40 → Medium, &lt;40 → Low.
              </p>
            </div>
            {incident.severity_scores?.map((s, i) => (
              <div key={i} style={{ display:'grid', gridTemplateColumns:'repeat(2,1fr)', gap:16 }}>
                {[
                  { label:'Asset Criticality', value:s.asset_criticality, weight:'30%' },
                  { label:'Threat Confidence', value:s.threat_confidence, weight:'30%' },
                  { label:'Impact Level', value:s.impact_level, weight:'20%' },
                  { label:'Detection Confidence', value:s.detection_confidence, weight:'20%' },
                ].map(({ label, value, weight }) => (
                  <div key={label} style={{ padding:16, background:'var(--bg-glass)', border:'1px solid var(--border)', borderRadius:8 }}>
                    <div style={{ display:'flex', justifyContent:'space-between', marginBottom:8 }}>
                      <span style={{ fontSize:13, fontWeight:600 }}>{label}</span>
                      <span style={{ fontSize:11, color:'var(--text-muted)' }}>weight: {weight}</span>
                    </div>
                    <div style={{ display:'flex', alignItems:'center', gap:12 }}>
                      <div style={{ flex:1, height:6, background:'var(--bg-3)', borderRadius:3, overflow:'hidden' }}>
                        <div style={{ width:`${value*10}%`, height:'100%', background:'var(--accent-blue)', borderRadius:3 }} />
                      </div>
                      <span style={{ fontFamily:'var(--font-mono)', fontWeight:700, color:'var(--accent-blue)' }}>{value}/10</span>
                    </div>
                  </div>
                ))}
              </div>
            ))}
            <div style={{ marginTop:20, padding:20, background:`${scoreColor}15`, border:`1px solid ${scoreColor}40`, borderRadius:8, textAlign:'center' }}>
              <div style={{ fontSize:40, fontWeight:900, fontFamily:'var(--font-mono)', color:scoreColor }}>{incident.severity_score?.toFixed(1)}</div>
              <div style={{ fontSize:13, color:'var(--text-muted)', marginTop:4 }}>Total Severity Score → <strong style={{ color:SEV_COLORS[incident.severity] }}>{incident.severity}</strong></div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
