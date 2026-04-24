import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend,
} from 'recharts';
import {
  AlertTriangle, Shield, Clock, Activity, TrendingUp,
  CheckCircle2, Zap, Target, Eye, ChevronRight, Bell, Radio,
} from 'lucide-react';
import { dashboardAPI } from '../api';

const SEV_COLORS = { Critical: '#ef4444', High: '#f97316', Medium: '#eab308', Low: '#22c55e' };

function SeverityDot({ level }) {
  return <span style={{ display:'inline-block', width:8, height:8, borderRadius:'50%', background: SEV_COLORS[level]||'#6b7280', marginRight:6 }} />;
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background:'var(--bg-2)', border:'1px solid var(--border)', borderRadius:8, padding:'10px 14px', fontSize:13 }}>
      <div style={{ color:'var(--text-muted)', marginBottom:6 }}>{label}</div>
      {payload.map(p => <div key={p.dataKey} style={{ color:p.color, marginBottom:2 }}>{p.name}: <strong>{p.value}</strong></div>)}
    </div>
  );
};

export default function DashboardPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [typeStats, setTypeStats] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([dashboardAPI.get(), dashboardAPI.typeStats()])
      .then(([d, t]) => { setData(d.data); setTypeStats(t.data); })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="page-container">
      <div className="stats-grid">{[...Array(8)].map((_,i) => <div key={i} className="stat-card loading-skeleton" style={{ height:110 }} />)}</div>
    </div>
  );

  if (!data) return (
    <div className="page-container">
      <div className="empty-state"><div className="empty-state-icon">⚠️</div><h3>Failed to load dashboard</h3><p>Make sure the backend is running on port 8000.</p></div>
    </div>
  );

  const { stats, trend, recent_incidents } = data;

  const pieData = [
    { name:'Critical', value:stats.critical_incidents, color:'#ef4444' },
    { name:'High', value:stats.high_incidents, color:'#f97316' },
    { name:'Medium', value:stats.medium_incidents, color:'#eab308' },
    { name:'Low', value:stats.low_incidents, color:'#22c55e' },
  ].filter(d => d.value > 0);

  const typeColors = ['#3b82f6','#8b5cf6','#06b6d4','#10b981','#f97316','#ef4444','#eab308','#ec4899'];

  const statCards = [
    { label:'Total Incidents', value:stats.total_incidents, icon:Shield, color:'#3b82f6', bg:'rgba(59,130,246,0.1)', border:'rgba(59,130,246,0.2)' },
    { label:'Open', value:stats.open_incidents, icon:AlertTriangle, color:'#f97316', bg:'rgba(249,115,22,0.1)', border:'rgba(249,115,22,0.2)' },
    { label:'Investigating', value:stats.investigating_incidents, icon:Eye, color:'#8b5cf6', bg:'rgba(139,92,246,0.1)', border:'rgba(139,92,246,0.2)' },
    { label:'Critical', value:stats.critical_incidents, icon:Zap, color:'#ef4444', bg:'rgba(239,68,68,0.1)', border:'rgba(239,68,68,0.2)' },
    { label:'Resolved', value:stats.closed_incidents, icon:CheckCircle2, color:'#10b981', bg:'rgba(16,185,129,0.1)', border:'rgba(16,185,129,0.2)' },
    { label:'Today', value:stats.incidents_today, icon:Activity, color:'#06b6d4', bg:'rgba(6,182,212,0.1)', border:'rgba(6,182,212,0.2)' },
    { label:'Avg Resolution', value:`${stats.avg_resolution_time_hours}h`, icon:Clock, color:'#f59e0b', bg:'rgba(245,158,11,0.1)', border:'rgba(245,158,11,0.2)' },
    { label:'Playbooks Run', value:stats.playbooks_executed, icon:TrendingUp, color:'#10b981', bg:'rgba(16,185,129,0.1)', border:'rgba(16,185,129,0.2)' },
    { label:'Total Alerts', value:stats.total_alerts, icon:Bell, color:'#ec4899', bg:'rgba(236,72,153,0.1)', border:'rgba(236,72,153,0.2)' },
  ];

  return (
    <div className="page-container">
      <div className="page-header">
        <div className="page-header-left">
          <h1>Security Operations Center</h1>
          <p>Real-time incident monitoring &amp; response dashboard</p>
        </div>
        <div className="topbar-right">
          <div className="status-indicator"><span className="status-dot" />Systems Operational</div>
          <button className="btn btn-primary" onClick={() => navigate('/incidents')}>
            <AlertTriangle size={16} /> New Incident
          </button>
        </div>
      </div>

      {/* Stat Cards */}
      <div className="stats-grid" style={{ gridTemplateColumns:'repeat(auto-fit, minmax(170px,1fr))' }}>
        {statCards.map(({ label, value, icon: Icon, color, bg, border }) => (
          <div className="stat-card" key={label} style={{ '--stat-color':color, '--stat-bg':bg, '--stat-border':border }}>
            <div className="stat-icon"><Icon size={20} /></div>
            <div className="stat-info">
              <div className="stat-value">{value}</div>
              <div className="stat-label">{label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Charts Row 1 */}
      <div style={{ display:'grid', gridTemplateColumns:'1fr 300px', gap:20, marginBottom:20 }}>
        <div className="card">
          <div className="card-header"><span className="card-title"><TrendingUp size={16} /> 7-Day Incident Trend</span></div>
          <div className="card-body">
            <ResponsiveContainer width="100%" height={230}>
              <AreaChart data={trend} margin={{ top:5, right:5, bottom:0, left:-20 }}>
                <defs>
                  <linearGradient id="gC" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/><stop offset="95%" stopColor="#ef4444" stopOpacity={0}/></linearGradient>
                  <linearGradient id="gH" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#f97316" stopOpacity={0.3}/><stop offset="95%" stopColor="#f97316" stopOpacity={0}/></linearGradient>
                  <linearGradient id="gM" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#eab308" stopOpacity={0.2}/><stop offset="95%" stopColor="#eab308" stopOpacity={0}/></linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="date" tick={{ fill:'var(--text-muted)', fontSize:11 }} tickLine={false} />
                <YAxis tick={{ fill:'var(--text-muted)', fontSize:11 }} tickLine={false} axisLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="critical" name="Critical" stroke="#ef4444" fill="url(#gC)" strokeWidth={2} />
                <Area type="monotone" dataKey="high" name="High" stroke="#f97316" fill="url(#gH)" strokeWidth={2} />
                <Area type="monotone" dataKey="medium" name="Medium" stroke="#eab308" fill="url(#gM)" strokeWidth={2} />
                <Area type="monotone" dataKey="low" name="Low" stroke="#22c55e" fill="none" strokeWidth={1.5} strokeDasharray="4 2" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card">
          <div className="card-header"><span className="card-title"><Target size={16} /> Severity Distribution</span></div>
          <div className="card-body">
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height={230}>
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="42%" innerRadius={55} outerRadius={82} paddingAngle={3} dataKey="value">
                    {pieData.map((e,i) => <Cell key={i} fill={e.color} />)}
                  </Pie>
                  <Tooltip contentStyle={{ background:'var(--bg-2)', border:'1px solid var(--border)', borderRadius:8, fontSize:13 }} />
                  <Legend formatter={(v) => <span style={{ color:'var(--text-secondary)', fontSize:12 }}>{v}</span>} />
                </PieChart>
              </ResponsiveContainer>
            ) : <div className="empty-state" style={{ padding:'40px 0' }}><div className="empty-state-icon">📊</div><p>No incidents yet</p></div>}
          </div>
        </div>
      </div>

      {/* Incident Types Bar Chart */}
      {typeStats.length > 0 && (
        <div className="card" style={{ marginBottom: 20 }}>
          <div className="card-header"><span className="card-title"><Activity size={16} /> Incidents by Type</span></div>
          <div className="card-body">
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={typeStats} margin={{ top:5, right:5, bottom:20, left:-20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="type" tick={{ fill:'var(--text-muted)', fontSize:10 }} tickLine={false} angle={-20} textAnchor="end" interval={0} />
                <YAxis tick={{ fill:'var(--text-muted)', fontSize:11 }} tickLine={false} axisLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="count" name="Count" radius={[4,4,0,0]}>
                  {typeStats.map((_, i) => <Cell key={i} fill={typeColors[i % typeColors.length]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Recent Incidents */}
      <div className="card">
        <div className="card-header">
          <span className="card-title"><Eye size={16} /> Recent Incidents</span>
          <button className="btn btn-secondary btn-sm" onClick={() => navigate('/incidents')}>View All <ChevronRight size={14} /></button>
        </div>
        <div className="table-container">
          {recent_incidents.length === 0 ? (
            <div className="empty-state"><div className="empty-state-icon">🛡️</div><h3>No incidents recorded</h3><p>Create your first incident to get started.</p></div>
          ) : (
            <table>
              <thead><tr><th>Incident ID</th><th>Title</th><th>Type</th><th>Severity</th><th>Status</th><th>Score</th><th>Risk</th><th>Created</th></tr></thead>
              <tbody>
                {recent_incidents.map(inc => (
                  <tr key={inc.id} onClick={() => navigate(`/incidents/${inc.id}`)} style={{ cursor:'pointer' }}>
                    <td><span style={{ fontFamily:'var(--font-mono)', fontSize:12, color:'var(--accent-blue)' }}>{inc.incident_id}</span></td>
                    <td style={{ maxWidth:200, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>{inc.title}</td>
                    <td style={{ fontSize:12, color:'var(--text-muted)' }}>{inc.incident_type}</td>
                    <td><span className={`severity-badge ${inc.severity?.toLowerCase()}`}><SeverityDot level={inc.severity}/>{inc.severity}</span></td>
                    <td><span className={`status-badge ${inc.status?.toLowerCase().replace(' ','')}`}>{inc.status}</span></td>
                    <td><span style={{ fontFamily:'var(--font-mono)', fontWeight:700 }}>{inc.severity_score?.toFixed(1)}</span></td>
                    <td>
                      <span style={{ fontFamily:'var(--font-mono)', fontSize:12, color: inc.escalation_risk >= 70 ? '#ef4444' : inc.escalation_risk >= 50 ? '#f97316' : '#22c55e' }}>
                        {inc.escalation_risk?.toFixed(0)}%
                      </span>
                    </td>
                    <td style={{ fontSize:12, color:'var(--text-muted)' }}>{new Date(inc.created_at).toLocaleDateString()}</td>
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
