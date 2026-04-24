import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertTriangle, Search, Filter, RefreshCw, Plus, ChevronDown } from 'lucide-react';
import { incidentsAPI } from '../api';
import CreateIncidentModal from '../components/CreateIncidentModal';

const SEV_COLORS = { Critical:'#ef4444', High:'#f97316', Medium:'#eab308', Low:'#22c55e' };

function SeverityDot({ level }) {
  return <span style={{ display:'inline-block', width:8, height:8, borderRadius:'50%', background:SEV_COLORS[level]||'#6b7280', marginRight:6 }} />;
}

function EscalationBar({ value }) {
  const color = value >= 70 ? '#ef4444' : value >= 50 ? '#f97316' : '#22c55e';
  return (
    <div style={{ display:'flex', alignItems:'center', gap:8 }}>
      <div style={{ flex:1, height:4, background:'var(--bg-3)', borderRadius:2, overflow:'hidden' }}>
        <div style={{ width:`${value}%`, height:'100%', background:color, borderRadius:2, transition:'width 0.3s' }} />
      </div>
      <span style={{ fontFamily:'var(--font-mono)', fontSize:11, color, minWidth:30 }}>{value?.toFixed(0)}%</span>
    </div>
  );
}

const STATUSES = ['', 'Open', 'Investigating', 'Contained', 'Resolved', 'Closed'];
const SEVERITIES = ['', 'Critical', 'High', 'Medium', 'Low'];

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [filters, setFilters] = useState({ status:'', severity:'', search:'' });
  const navigate = useNavigate();

  const fetchIncidents = useCallback(() => {
    setLoading(true);
    const params = {};
    if (filters.status) params.status = filters.status;
    if (filters.severity) params.severity = filters.severity;
    if (filters.search) params.search = filters.search;
    incidentsAPI.list(params)
      .then(r => setIncidents(r.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [filters]);

  useEffect(() => { fetchIncidents(); }, [fetchIncidents]);

  const handleCreated = () => { setShowModal(false); fetchIncidents(); };

  const counts = {
    all: incidents.length,
    critical: incidents.filter(i => i.severity === 'Critical').length,
    open: incidents.filter(i => i.status === 'Open').length,
    investigating: incidents.filter(i => i.status === 'Investigating').length,
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <div className="page-header-left">
          <h1>Incident Management</h1>
          <p>Track, classify, and respond to security incidents</p>
        </div>
        <div className="topbar-right">
          <button className="btn btn-secondary" onClick={fetchIncidents}><RefreshCw size={15} /> Refresh</button>
          <button id="create-incident-btn" className="btn btn-primary" onClick={() => setShowModal(true)}>
            <Plus size={16} /> New Incident
          </button>
        </div>
      </div>

      {/* Quick Stats */}
      <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:12, marginBottom:20 }}>
        {[
          { label:'Total', value:counts.all, color:'#3b82f6' },
          { label:'Open', value:counts.open, color:'#f97316' },
          { label:'Investigating', value:counts.investigating, color:'#8b5cf6' },
          { label:'Critical', value:counts.critical, color:'#ef4444' },
        ].map(({ label, value, color }) => (
          <div key={label} style={{ background:'var(--bg-card)', border:'1px solid var(--border)', borderRadius:'var(--radius-sm)', padding:'14px 18px', borderTop:`3px solid ${color}` }}>
            <div style={{ fontFamily:'var(--font-mono)', fontSize:24, fontWeight:800, color }}>{value}</div>
            <div style={{ fontSize:12, color:'var(--text-muted)', marginTop:2 }}>{label}</div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="card" style={{ padding:'16px 20px', marginBottom:20 }}>
        <div className="filter-bar" style={{ marginBottom:0 }}>
          <div className="search-input-wrap" style={{ flex:1 }}>
            <Search size={16} />
            <input className="form-control" placeholder="Search incidents..." value={filters.search}
              onChange={e => setFilters(f => ({ ...f, search:e.target.value }))} style={{ paddingLeft:38 }} />
          </div>
          <select className="form-control" style={{ width:160 }} value={filters.status}
            onChange={e => setFilters(f => ({ ...f, status:e.target.value }))}>
            {STATUSES.map(s => <option key={s} value={s}>{s || 'All Statuses'}</option>)}
          </select>
          <select className="form-control" style={{ width:150 }} value={filters.severity}
            onChange={e => setFilters(f => ({ ...f, severity:e.target.value }))}>
            {SEVERITIES.map(s => <option key={s} value={s}>{s || 'All Severities'}</option>)}
          </select>
          {(filters.status || filters.severity || filters.search) && (
            <button className="btn btn-secondary btn-sm" onClick={() => setFilters({ status:'', severity:'', search:'' })}>Clear</button>
          )}
        </div>
      </div>

      {/* Incidents Table */}
      <div className="card">
        <div className="card-header">
          <span className="card-title"><AlertTriangle size={16} /> Incidents ({incidents.length})</span>
        </div>
        <div className="table-container">
          {loading ? (
            <div style={{ padding:40, textAlign:'center', color:'var(--text-muted)' }}>Loading incidents…</div>
          ) : incidents.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">🛡️</div>
              <h3>No incidents found</h3>
              <p>No incidents match your current filters.</p>
            </div>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>ID</th><th>Title</th><th>Type</th><th>Severity</th><th>Status</th>
                  <th>Score</th><th>Escalation Risk</th><th>Source IP</th><th>Created</th>
                </tr>
              </thead>
              <tbody>
                {incidents.map(inc => (
                  <tr key={inc.id} onClick={() => navigate(`/incidents/${inc.id}`)} style={{ cursor:'pointer' }}>
                    <td><span style={{ fontFamily:'var(--font-mono)', fontSize:11, color:'var(--accent-blue)' }}>{inc.incident_id}</span></td>
                    <td style={{ maxWidth:220, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap', fontWeight:500 }}>{inc.title}</td>
                    <td style={{ fontSize:12, color:'var(--text-muted)', whiteSpace:'nowrap' }}>{inc.incident_type}</td>
                    <td><span className={`severity-badge ${inc.severity?.toLowerCase()}`}><SeverityDot level={inc.severity}/>{inc.severity}</span></td>
                    <td><span className={`status-badge ${inc.status?.toLowerCase().replace(/ /g,'')}`}>{inc.status}</span></td>
                    <td>
                      <span style={{ fontFamily:'var(--font-mono)', fontWeight:700, color: inc.severity_score >= 80?'#ef4444':inc.severity_score >= 60?'#f97316':inc.severity_score >= 40?'#eab308':'#22c55e' }}>
                        {inc.severity_score?.toFixed(1)}
                      </span>
                    </td>
                    <td style={{ minWidth:130 }}><EscalationBar value={inc.escalation_risk || 0} /></td>
                    <td style={{ fontFamily:'var(--font-mono)', fontSize:11, color:'var(--text-muted)' }}>{inc.source_ip || '—'}</td>
                    <td style={{ fontSize:12, color:'var(--text-muted)', whiteSpace:'nowrap' }}>
                      {new Date(inc.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {showModal && <CreateIncidentModal onClose={() => setShowModal(false)} onCreated={handleCreated} />}
    </div>
  );
}
