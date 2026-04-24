import { useState, useEffect } from 'react';
import { BookOpen, Play, ChevronDown, ChevronUp, Clock, Zap } from 'lucide-react';
import { playbooksAPI } from '../api';

const TYPE_COLORS = {
  'Brute Force Attack':'#3b82f6','Malware Infection':'#ef4444','Phishing Attempt':'#f97316',
  'Data Exfiltration':'#8b5cf6','Privilege Escalation':'#eab308','Ransomware':'#dc2626',
  'DoS/DDoS Attack':'#06b6d4','Insider Threat':'#ec4899','Unknown':'#6b7280',
};

export default function PlaybooksPage() {
  const [playbooks, setPlaybooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState({});
  const [filter, setFilter] = useState('');

  useEffect(() => {
    playbooksAPI.list().then(r => setPlaybooks(r.data)).catch(console.error).finally(() => setLoading(false));
  }, []);

  const toggle = (id) => setExpanded(p => ({ ...p, [id]: !p[id] }));
  const filtered = filter ? playbooks.filter(pb => pb.incident_type === filter) : playbooks;
  const types = [...new Set(playbooks.map(pb => pb.incident_type))];

  const totalSteps = (pb) => pb.steps?.length || 0;
  const autoSteps = (pb) => pb.steps?.filter(s => s.action_type === 'automated').length || 0;
  const totalDuration = (pb) => pb.steps?.reduce((acc, s) => acc + (s.estimated_duration || 0), 0) || 0;

  return (
    <div className="page-container">
      <div className="page-header">
        <div className="page-header-left">
          <h1>Automated Playbooks</h1>
          <p>Predefined response workflows for each incident type</p>
        </div>
        <div style={{ fontSize:13, color:'var(--text-muted)' }}>{playbooks.length} playbooks loaded</div>
      </div>

      {/* Filter */}
      <div style={{ marginBottom:20, display:'flex', gap:8, flexWrap:'wrap' }}>
        <button className={`btn btn-sm ${!filter ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setFilter('')}>All</button>
        {types.map(t => (
          <button key={t} className={`btn btn-sm ${filter===t ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setFilter(t)}
            style={{ borderLeft:`3px solid ${TYPE_COLORS[t]||'#6b7280'}` }}>
            {t}
          </button>
        ))}
      </div>

      {loading ? (
        <div style={{ padding:60, textAlign:'center', color:'var(--text-muted)' }}>Loading playbooks…</div>
      ) : (
        <div style={{ display:'flex', flexDirection:'column', gap:16 }}>
          {filtered.map(pb => (
            <div key={pb.id} className="card" style={{ borderLeft:`4px solid ${TYPE_COLORS[pb.incident_type]||'#6b7280'}` }}>
              <div className="card-header" style={{ cursor:'pointer' }} onClick={() => toggle(pb.id)}>
                <div style={{ display:'flex', alignItems:'center', gap:14, flex:1 }}>
                  <div style={{ width:40, height:40, borderRadius:8, background:`${TYPE_COLORS[pb.incident_type]||'#6b7280'}20`, border:`1px solid ${TYPE_COLORS[pb.incident_type]||'#6b7280'}40`, display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0 }}>
                    <BookOpen size={18} style={{ color:TYPE_COLORS[pb.incident_type]||'#6b7280' }} />
                  </div>
                  <div>
                    <div style={{ fontWeight:700, fontSize:15 }}>{pb.name}</div>
                    <div style={{ fontSize:12, color:'var(--text-muted)', marginTop:2 }}>{pb.description}</div>
                  </div>
                </div>
                <div style={{ display:'flex', alignItems:'center', gap:16 }}>
                  <div style={{ textAlign:'center' }}>
                    <div style={{ fontFamily:'var(--font-mono)', fontWeight:700, fontSize:18 }}>{totalSteps(pb)}</div>
                    <div style={{ fontSize:10, color:'var(--text-muted)', textTransform:'uppercase' }}>Steps</div>
                  </div>
                  <div style={{ textAlign:'center' }}>
                    <div style={{ fontFamily:'var(--font-mono)', fontWeight:700, fontSize:18, color:'var(--accent-blue)' }}>{autoSteps(pb)}</div>
                    <div style={{ fontSize:10, color:'var(--text-muted)', textTransform:'uppercase' }}>Auto</div>
                  </div>
                  <div style={{ textAlign:'center' }}>
                    <div style={{ fontFamily:'var(--font-mono)', fontWeight:700, fontSize:18, color:'#f59e0b' }}>{totalDuration(pb)}m</div>
                    <div style={{ fontSize:10, color:'var(--text-muted)', textTransform:'uppercase' }}>Est. Time</div>
                  </div>
                  <span style={{ padding:'3px 10px', borderRadius:20, fontSize:11, fontWeight:700, background:`${TYPE_COLORS[pb.incident_type]||'#6b7280'}20`, color:TYPE_COLORS[pb.incident_type]||'#6b7280', border:`1px solid ${TYPE_COLORS[pb.incident_type]||'#6b7280'}40` }}>
                    {pb.incident_type}
                  </span>
                  <span style={{ padding:'2px 8px', borderRadius:4, fontSize:11, background:'rgba(16,185,129,0.15)', color:'#6ee7b7', border:'1px solid rgba(16,185,129,0.3)' }}>v{pb.version}</span>
                  {expanded[pb.id] ? <ChevronUp size={18} style={{ color:'var(--text-muted)' }} /> : <ChevronDown size={18} style={{ color:'var(--text-muted)' }} />}
                </div>
              </div>

              {expanded[pb.id] && (
                <div className="card-body">
                  <div className="playbook-steps">
                    {pb.steps?.map((step, idx) => (
                      <div key={step.id} className="playbook-step">
                        <div className="step-number" style={{ background: step.is_critical ? 'rgba(239,68,68,0.15)' : undefined, borderColor: step.is_critical ? '#ef4444' : undefined, color: step.is_critical ? '#fca5a5' : undefined }}>
                          {idx + 1}
                        </div>
                        <div className="step-content">
                          <div className="step-title">{step.title}</div>
                          {step.description && <div className="step-desc">{step.description}</div>}
                          <div className="step-meta">
                            <span className={`step-tag ${step.action_type}`}>{step.action_type}</span>
                            {step.is_critical && <span className="step-tag critical">Critical</span>}
                            <span style={{ display:'flex', alignItems:'center', gap:4, fontSize:11, color:'var(--text-muted)' }}>
                              <Clock size={11} /> {step.estimated_duration}m
                            </span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                  {pb.author && (
                    <div style={{ marginTop:16, fontSize:12, color:'var(--text-muted)', textAlign:'right' }}>
                      Author: <strong style={{ color:'var(--text-secondary)' }}>{pb.author}</strong>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
