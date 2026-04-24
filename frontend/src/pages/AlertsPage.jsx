import { useState, useEffect } from 'react';
import { Bell, RefreshCw, Plus } from 'lucide-react';
import { alertsAPI } from '../api';

const SOURCE_COLORS = { SIEM:'#3b82f6', Firewall:'#ef4444', Manual:'#6b7280', 'IDS/IPS':'#f97316', EDR:'#10b981', API:'#8b5cf6' };

export default function AlertsPage() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ source:'SIEM', event_type:'', description:'' });
  const [submitting, setSubmitting] = useState(false);

  const fetchAlerts = () => {
    setLoading(true);
    alertsAPI.list().then(r => setAlerts(r.data)).catch(console.error).finally(() => setLoading(false));
  };

  useEffect(() => { fetchAlerts(); }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await alertsAPI.create(form);
      setShowCreate(false);
      setForm({ source:'SIEM', event_type:'', description:'' });
      fetchAlerts();
    } catch (err) { console.error(err); }
    finally { setSubmitting(false); }
  };

  const unprocessed = alerts.filter(a => !a.is_processed).length;

  return (
    <div className="page-container">
      <div className="page-header">
        <div className="page-header-left">
          <h1>Alert Intake</h1>
          <p>Security alerts ingestion from SIEM, Firewall, EDR, and manual sources</p>
        </div>
        <div className="topbar-right">
          {unprocessed > 0 && (
            <div style={{ display:'flex', alignItems:'center', gap:8, padding:'6px 14px', background:'rgba(239,68,68,0.1)', border:'1px solid rgba(239,68,68,0.3)', borderRadius:20, fontSize:12, color:'#fca5a5', fontWeight:700 }}>
              🔔 {unprocessed} unprocessed
            </div>
          )}
          <button className="btn btn-secondary" onClick={fetchAlerts}><RefreshCw size={15} /></button>
          <button className="btn btn-primary" onClick={() => setShowCreate(s => !s)}><Plus size={16} /> New Alert</button>
        </div>
      </div>

      {/* Create Alert Form */}
      {showCreate && (
        <div className="card" style={{ marginBottom:20 }}>
          <div className="card-header"><span className="card-title"><Bell size={16} /> Create Alert</span></div>
          <div className="card-body">
            <form onSubmit={handleCreate}>
              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Source *</label>
                  <select className="form-control" value={form.source} onChange={e => setForm(f => ({...f, source:e.target.value}))}>
                    {['SIEM','Firewall','Manual','IDS/IPS','EDR','API'].map(s => <option key={s}>{s}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Event Type *</label>
                  <input className="form-control" placeholder="e.g. Failed Login, Malware Detected" required
                    value={form.event_type} onChange={e => setForm(f => ({...f, event_type:e.target.value}))} />
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">Description *</label>
                <textarea className="form-control" rows={3} placeholder="Describe the alert..." required
                  value={form.description} onChange={e => setForm(f => ({...f, description:e.target.value}))} />
              </div>
              <div style={{ display:'flex', gap:8, justifyContent:'flex-end' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowCreate(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={submitting}>{submitting ? 'Creating…' : 'Create Alert'}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Alerts Table */}
      <div className="card">
        <div className="card-header">
          <span className="card-title"><Bell size={16} /> All Alerts ({alerts.length})</span>
        </div>
        <div className="table-container">
          {loading ? (
            <div style={{ padding:40, textAlign:'center', color:'var(--text-muted)' }}>Loading alerts…</div>
          ) : alerts.length === 0 ? (
            <div className="empty-state"><div className="empty-state-icon">🔔</div><h3>No alerts yet</h3><p>Create a new alert or connect a SIEM source.</p></div>
          ) : (
            <table>
              <thead><tr><th>Alert ID</th><th>Source</th><th>Event Type</th><th>Description</th><th>Status</th><th>Timestamp</th></tr></thead>
              <tbody>
                {alerts.map(a => (
                  <tr key={a.id}>
                    <td><span style={{ fontFamily:'var(--font-mono)', fontSize:11, color:'var(--accent-cyan)' }}>{a.alert_id}</span></td>
                    <td>
                      <span style={{ padding:'3px 10px', borderRadius:20, fontSize:11, fontWeight:700, background:`${SOURCE_COLORS[a.source]||'#6b7280'}20`, color:SOURCE_COLORS[a.source]||'#6b7280', border:`1px solid ${SOURCE_COLORS[a.source]||'#6b7280'}40` }}>
                        {a.source}
                      </span>
                    </td>
                    <td style={{ fontWeight:500 }}>{a.event_type}</td>
                    <td style={{ maxWidth:320, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap', fontSize:13, color:'var(--text-muted)' }}>{a.description}</td>
                    <td>
                      <span style={{ padding:'3px 10px', borderRadius:20, fontSize:11, fontWeight:600, background: a.is_processed?'rgba(16,185,129,0.15)':'rgba(249,115,22,0.15)', color:a.is_processed?'#6ee7b7':'#fdba74', border:`1px solid ${a.is_processed?'rgba(16,185,129,0.3)':'rgba(249,115,22,0.3)'}` }}>
                        {a.is_processed ? '✓ Processed' : '⏳ Pending'}
                      </span>
                    </td>
                    <td style={{ fontSize:12, color:'var(--text-muted)', whiteSpace:'nowrap' }}>{new Date(a.timestamp).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
