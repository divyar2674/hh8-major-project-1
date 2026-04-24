import { useState, useEffect } from 'react';
import { FileText, RefreshCw } from 'lucide-react';
import { dashboardAPI } from '../api';

const ACTION_COLORS = {
  CREATE_INCIDENT: '#3b82f6',
  UPDATE_INCIDENT: '#8b5cf6',
  DELETE_INCIDENT: '#ef4444',
};

export default function AuditPage() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchLogs = () => {
    setLoading(true);
    dashboardAPI.auditLogs(200).then(r => setLogs(r.data)).catch(console.error).finally(() => setLoading(false));
  };

  useEffect(() => { fetchLogs(); }, []);

  return (
    <div className="page-container">
      <div className="page-header">
        <div className="page-header-left">
          <h1>Audit Log</h1>
          <p>Complete trail of all actions performed in the system</p>
        </div>
        <button className="btn btn-secondary" onClick={fetchLogs}><RefreshCw size={15} /> Refresh</button>
      </div>

      <div className="card">
        <div className="card-header">
          <span className="card-title"><FileText size={16} /> Activity Log ({logs.length})</span>
        </div>
        <div className="table-container">
          {loading ? (
            <div style={{ padding:40, textAlign:'center', color:'var(--text-muted)' }}>Loading audit logs…</div>
          ) : logs.length === 0 ? (
            <div className="empty-state"><div className="empty-state-icon">📋</div><h3>No audit logs yet</h3><p>Actions will be recorded here.</p></div>
          ) : (
            <table>
              <thead><tr><th>#</th><th>Action</th><th>Entity</th><th>User</th><th>Incident ID</th><th>Timestamp</th></tr></thead>
              <tbody>
                {logs.map(log => (
                  <tr key={log.id}>
                    <td style={{ fontFamily:'var(--font-mono)', fontSize:11, color:'var(--text-muted)' }}>{log.id}</td>
                    <td>
                      <span style={{ padding:'3px 10px', borderRadius:20, fontSize:11, fontWeight:700, background:`${ACTION_COLORS[log.action]||'#6b7280'}20`, color:ACTION_COLORS[log.action]||'#9ca3af', border:`1px solid ${ACTION_COLORS[log.action]||'#6b7280'}40` }}>
                        {log.action}
                      </span>
                    </td>
                    <td style={{ fontSize:12 }}>{log.entity_type} #{log.entity_id}</td>
                    <td style={{ fontWeight:500 }}>{log.username}</td>
                    <td style={{ fontFamily:'var(--font-mono)', fontSize:11, color:'var(--accent-blue)' }}>{log.incident_id ? `#${log.incident_id}` : '—'}</td>
                    <td style={{ fontSize:12, color:'var(--text-muted)', whiteSpace:'nowrap' }}>{new Date(log.timestamp).toLocaleString()}</td>
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
