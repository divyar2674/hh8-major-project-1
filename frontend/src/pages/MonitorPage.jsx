import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Activity, Cpu, MemoryStick, HardDrive, Wifi, Shield,
  AlertTriangle, Zap, Server, Network, Eye, RefreshCw,
  Terminal, ChevronRight, TrendingUp, Radio
} from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, AreaChart, Area
} from 'recharts';
import useMonitorWebSocket from '../hooks/useMonitorWebSocket';
import api from '../api';

// ─── Gauge Ring Component ─────────────────────────────────────────────────────
function GaugeRing({ value = 0, max = 100, color = '#3b82f6', label, sublabel, size = 110 }) {
  const r = (size / 2) - 10;
  const circ = 2 * Math.PI * r;
  const pct = Math.min(value / max, 1);
  const dash = pct * circ;
  const colorMap = { low: '#22c55e', medium: '#eab308', high: '#f97316', critical: '#ef4444' };
  const dynamicColor =
    pct >= 0.9 ? colorMap.critical
    : pct >= 0.75 ? colorMap.high
    : pct >= 0.5 ? colorMap.medium
    : colorMap.low;
  const c = color === 'dynamic' ? dynamicColor : color;

  return (
    <div style={{ textAlign: 'center', position: 'relative', width: size, margin: '0 auto' }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={8} />
        <circle
          cx={size/2} cy={size/2} r={r} fill="none" stroke={c} strokeWidth={8}
          strokeDasharray={`${dash} ${circ - dash}`}
          strokeLinecap="round"
          style={{ transition: 'stroke-dasharray 0.6s ease, stroke 0.4s ease' }}
        />
      </svg>
      <div style={{
        position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
      }}>
        <div style={{ fontSize: 18, fontWeight: 900, fontFamily: 'var(--font-mono)', color: c }}>
          {typeof value === 'number' ? `${value.toFixed(0)}%` : value}
        </div>
        {sublabel && <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 1 }}>{sublabel}</div>}
      </div>
      <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 6, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
        {label}
      </div>
    </div>
  );
}

// ─── Threat Level Badge ────────────────────────────────────────────────────────
function ThreatLevelBadge({ level }) {
  const config = {
    CRITICAL: { bg: 'rgba(239,68,68,0.15)', color: '#ef4444', border: 'rgba(239,68,68,0.4)', pulse: true },
    HIGH:     { bg: 'rgba(249,115,22,0.15)', color: '#f97316', border: 'rgba(249,115,22,0.35)', pulse: false },
    MEDIUM:   { bg: 'rgba(234,179,8,0.15)',  color: '#eab308', border: 'rgba(234,179,8,0.3)', pulse: false },
    LOW:      { bg: 'rgba(34,197,94,0.15)',  color: '#22c55e', border: 'rgba(34,197,94,0.3)', pulse: false },
  }[level] || { bg: 'rgba(107,114,128,0.15)', color: '#9ca3af', border: 'rgba(107,114,128,0.3)', pulse: false };

  return (
    <div style={{
      display: 'inline-flex', alignItems: 'center', gap: 8,
      background: config.bg, color: config.color, border: `1px solid ${config.border}`,
      borderRadius: 24, padding: '6px 18px', fontWeight: 800, fontSize: 13,
      letterSpacing: '0.08em',
    }}>
      {config.pulse && (
        <span style={{
          width: 8, height: 8, borderRadius: '50%', background: config.color,
          animation: 'pulse-alert 1s infinite',
          display: 'inline-block',
        }} />
      )}
      {level}
    </div>
  );
}

// ─── Live Event Row ────────────────────────────────────────────────────────────
function EventRow({ ev }) {
  const threat = ev?.data?.threat || ev?.data;
  if (!threat) return null;
  const isCritical = (threat.severity === 'Critical') || (threat.severity_score >= 80);
  return (
    <div style={{
      padding: '10px 14px',
      borderBottom: '1px solid var(--border)',
      display: 'flex', alignItems: 'flex-start', gap: 12,
      background: isCritical ? 'rgba(239,68,68,0.04)' : 'transparent',
      animation: 'fadeIn 0.3s ease',
    }}>
      <div style={{
        width: 8, height: 8, borderRadius: '50%', marginTop: 5, flexShrink: 0,
        background: isCritical ? '#ef4444' : threat.severity === 'High' ? '#f97316' : '#eab308',
        boxShadow: isCritical ? '0 0 6px #ef4444' : 'none',
      }} />
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 2 }}>
          {threat.event_type || ev.type}
        </div>
        <div style={{ fontSize: 11, color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '100%' }}>
          {threat.description || threat.classification_hint || '—'}
        </div>
      </div>
      <div style={{ fontSize: 10, color: 'var(--text-muted)', whiteSpace: 'nowrap', fontFamily: 'var(--font-mono)' }}>
        {new Date().toLocaleTimeString()}
      </div>
    </div>
  );
}

// ─── Main Monitor Page ─────────────────────────────────────────────────────────
export default function MonitorPage() {
  const { connected, metrics, events, threats } = useMonitorWebSocket();
  const [threatSummary, setThreatSummary] = useState(null);
  const [autoIngesting, setAutoIngesting] = useState(false);
  const [ingestResult, setIngestResult] = useState(null);
  const [cpuHistory, setCpuHistory] = useState([]);
  const [memHistory, setMemHistory] = useState([]);
  const navigate = useNavigate();

  // Update rolling history
  useEffect(() => {
    if (!metrics) return;
    const ts = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
    setCpuHistory(prev => [...prev.slice(-29), { time: ts, cpu: metrics.cpu_percent, mem: metrics.memory_percent }]);
  }, [metrics]);

  // Load threat summary on mount + every 30s
  useEffect(() => {
    const load = () =>
      api.get('/monitor/threat-summary')
        .then(r => setThreatSummary(r.data))
        .catch(() => {});
    load();
    const t = setInterval(load, 30000);
    return () => clearInterval(t);
  }, []);

  const handleAutoIngest = async () => {
    setAutoIngesting(true);
    setIngestResult(null);
    try {
      const res = await api.post('/monitor/auto-ingest');
      setIngestResult(res.data);
      setTimeout(() => setIngestResult(null), 8000);
    } catch (e) {
      setIngestResult({ message: 'Failed to auto-ingest', created: [] });
    } finally {
      setAutoIngesting(false);
    }
  };

  const m = metrics;
  const anomalyScore = m?.anomaly_score ?? threatSummary?.anomaly_score ?? 0;
  const threatLevel = threatSummary?.threat_level || (anomalyScore >= 70 ? 'CRITICAL' : anomalyScore >= 50 ? 'HIGH' : anomalyScore >= 30 ? 'MEDIUM' : 'LOW');

  const CUSTOM_TT = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null;
    return (
      <div style={{ background: 'var(--bg-2)', border: '1px solid var(--border)', borderRadius: 8, padding: '8px 12px', fontSize: 12 }}>
        <div style={{ color: 'var(--text-muted)', marginBottom: 4 }}>{label}</div>
        {payload.map(p => (
          <div key={p.dataKey} style={{ color: p.color }}>{p.name}: <b>{p.value?.toFixed(1)}%</b></div>
        ))}
      </div>
    );
  };

  return (
    <div className="page-container">
      <style>{`
        @keyframes pulse-alert {
          0%,100% { opacity:1; box-shadow:0 0 0 0 rgba(239,68,68,0.5); }
          50% { opacity:0.7; box-shadow:0 0 0 6px rgba(239,68,68,0); }
        }
        @keyframes fadeIn { from{opacity:0;transform:translateY(-4px)} to{opacity:1;transform:none} }
        @keyframes scan {
          0% { background-position: 0% 0%; }
          100% { background-position: 0% 100%; }
        }
      `}</style>

      {/* Header */}
      <div className="page-header">
        <div className="page-header-left">
          <h1>Live System Monitor</h1>
          <p>Real-time Windows security telemetry — {connected ? '🟢 WebSocket connected' : '🔴 Reconnecting…'}</p>
        </div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <ThreatLevelBadge level={threatLevel} />
          <button
            className="btn btn-primary"
            onClick={handleAutoIngest}
            disabled={autoIngesting}
            title="Scan system for threats and auto-create incidents"
          >
            <Zap size={15} />
            {autoIngesting ? 'Scanning…' : 'Scan & Auto-Ingest'}
          </button>
        </div>
      </div>

      {/* Auto-ingest result */}
      {ingestResult && (
        <div className={`alert ${ingestResult.created?.length > 0 ? 'alert-warning' : 'alert-success'}`} style={{ marginBottom: 16 }}>
          <AlertTriangle size={16} />
          {ingestResult.message}
          {ingestResult.created?.length > 0 && (
            <span style={{ marginLeft: 8 }}>
              Created: <b>{ingestResult.created.join(', ')}</b>
              <button className="btn btn-secondary btn-sm" style={{ marginLeft: 12 }} onClick={() => navigate('/incidents')}>
                View →
              </button>
            </span>
          )}
        </div>
      )}

      {/* Top Row: Gauges + Anomaly Score */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 16, marginBottom: 20 }}>
        {/* CPU */}
        <div className="card" style={{ padding: 20 }}>
          <GaugeRing value={m?.cpu_percent ?? 0} color="dynamic" label="CPU" sublabel={`${m?.cpu_count ?? 0} cores`} />
        </div>
        {/* RAM */}
        <div className="card" style={{ padding: 20 }}>
          <GaugeRing value={m?.memory_percent ?? 0} color="dynamic" label="Memory" sublabel={`${m?.memory_used_gb ?? 0}/${m?.memory_total_gb ?? 0}GB`} />
        </div>
        {/* Disk */}
        <div className="card" style={{ padding: 20 }}>
          <GaugeRing value={m?.disk_percent ?? 0} color="dynamic" label="Disk C:" sublabel={`${m?.disk_used_gb ?? 0}GB used`} />
        </div>
        {/* Anomaly Score */}
        <div className="card" style={{ padding: 20, borderLeft: `3px solid ${anomalyScore >= 70 ? '#ef4444' : anomalyScore >= 50 ? '#f97316' : '#22c55e'}` }}>
          <GaugeRing
            value={anomalyScore}
            color={anomalyScore >= 70 ? '#ef4444' : anomalyScore >= 50 ? '#f97316' : '#22c55e'}
            label="Anomaly Score"
            sublabel="AI risk"
            size={110}
          />
        </div>
        {/* Connections */}
        <div className="card" style={{ padding: 20 }}>
          <div style={{ textAlign: 'center' }}>
            <Network size={24} color="var(--accent-blue)" style={{ marginBottom: 8 }} />
            <div style={{ fontSize: 28, fontWeight: 900, fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>
              {m?.active_connections ?? '—'}
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginTop: 4 }}>Active Connections</div>
            {(m?.suspicious_connections ?? 0) > 0 && (
              <div style={{ fontSize: 12, color: '#ef4444', fontWeight: 700, marginTop: 4 }}>
                ⚠ {m.suspicious_connections} suspicious
              </div>
            )}
          </div>
        </div>
        {/* Processes */}
        <div className="card" style={{ padding: 20 }}>
          <div style={{ textAlign: 'center' }}>
            <Terminal size={24} color="var(--accent-purple)" style={{ marginBottom: 8 }} />
            <div style={{ fontSize: 28, fontWeight: 900, fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>
              {m?.total_processes ?? '—'}
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginTop: 4 }}>Running Processes</div>
            {(m?.suspicious_processes ?? 0) > 0 && (
              <div style={{ fontSize: 12, color: '#ef4444', fontWeight: 700, marginTop: 4 }}>
                🚨 {m.suspicious_processes} flagged
              </div>
            )}
          </div>
        </div>
        {/* Failed Logins */}
        <div className="card" style={{ padding: 20, borderLeft: (m?.failed_logins_1h ?? 0) >= 10 ? '3px solid #ef4444' : 'none' }}>
          <div style={{ textAlign: 'center' }}>
            <Shield size={24} color={(m?.failed_logins_1h ?? 0) >= 10 ? '#ef4444' : 'var(--accent-green)'} style={{ marginBottom: 8 }} />
            <div style={{ fontSize: 28, fontWeight: 900, fontFamily: 'var(--font-mono)', color: (m?.failed_logins_1h ?? 0) >= 10 ? '#ef4444' : 'var(--text-primary)' }}>
              {m?.failed_logins_1h ?? '—'}
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginTop: 4 }}>Failed Logins/hr</div>
          </div>
        </div>
      </div>

      {/* CPU/Memory History Chart */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: 20, marginBottom: 20 }}>
        <div className="card">
          <div className="card-header">
            <span className="card-title"><TrendingUp size={16} /> Real-time CPU & Memory</span>
            <span style={{ fontSize: 12, color: connected ? 'var(--accent-green)' : 'var(--critical)', fontWeight: 600 }}>
              {connected ? '● LIVE' : '○ Disconnected'}
            </span>
          </div>
          <div className="card-body">
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={cpuHistory} margin={{ top: 5, right: 5, bottom: 0, left: -25 }}>
                <defs>
                  <linearGradient id="gradCPU" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="gradMEM" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                <XAxis dataKey="time" tick={{ fill: 'var(--text-muted)', fontSize: 10 }} tickLine={false} interval={4} />
                <YAxis domain={[0, 100]} tick={{ fill: 'var(--text-muted)', fontSize: 10 }} tickLine={false} axisLine={false} />
                <Tooltip content={<CUSTOM_TT />} />
                <Area type="monotone" dataKey="cpu" name="CPU" stroke="#3b82f6" fill="url(#gradCPU)" strokeWidth={2} dot={false} />
                <Area type="monotone" dataKey="mem" name="Memory" stroke="#8b5cf6" fill="url(#gradMEM)" strokeWidth={2} dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Top CPU Processes */}
        <div className="card">
          <div className="card-header">
            <span className="card-title"><Activity size={16} /> Top Processes by CPU</span>
          </div>
          <div className="card-body" style={{ padding: '8px 0' }}>
            {(m?.top_cpu_procs || []).length === 0 ? (
              <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 20 }}>Loading…</div>
            ) : (m?.top_cpu_procs || []).map((proc, i) => {
              const suspicious = m?.suspicious_procs_list?.find(s => s.pid === proc.pid);
              return (
                <div key={i} style={{
                  padding: '8px 16px', display: 'flex', alignItems: 'center', gap: 10,
                  borderBottom: '1px solid var(--border)',
                  background: suspicious ? 'rgba(239,68,68,0.05)' : 'transparent',
                }}>
                  <span style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', width: 16 }}>{i + 1}</span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 13, fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: suspicious ? '#ef4444' : 'var(--text-primary)' }}>
                      {suspicious ? '🚨 ' : ''}{proc.name}
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>PID {proc.pid}</div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: 13, fontFamily: 'var(--font-mono)', fontWeight: 700, color: proc.cpu_percent > 50 ? '#ef4444' : 'var(--text-primary)' }}>
                      {(proc.cpu_percent || 0).toFixed(1)}%
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{(proc.memory_percent || 0).toFixed(1)}% mem</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Network Connections + Live Events */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 20 }}>
        {/* Suspicious Connections */}
        <div className="card">
          <div className="card-header">
            <span className="card-title"><Wifi size={16} /> Network Connections</span>
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{m?.active_connections ?? 0} active</span>
          </div>
          <div style={{ maxHeight: 280, overflowY: 'auto' }}>
            {(m?.suspicious_conns_list || []).length > 0 ? (
              (m.suspicious_conns_list).map((conn, i) => (
                <div key={i} style={{ padding: '10px 16px', borderBottom: '1px solid var(--border)', display: 'flex', gap: 12 }}>
                  <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#ef4444', marginTop: 5, flexShrink: 0, boxShadow: '0 0 6px #ef4444' }} />
                  <div>
                    <div style={{ fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--text-primary)', marginBottom: 3 }}>
                      {conn.local} → {conn.remote}
                    </div>
                    <div style={{ fontSize: 11, color: '#fca5a5' }}>{conn.reason}</div>
                  </div>
                </div>
              ))
            ) : (
              <div style={{ padding: '30px 16px', textAlign: 'center' }}>
                <div style={{ fontSize: 24, marginBottom: 8 }}>✅</div>
                <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>No suspicious connections detected</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>{m?.active_connections ?? 0} clean connections active</div>
              </div>
            )}
          </div>
        </div>

        {/* Live Event Stream */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">
              <Radio size={16} />
              Live Event Stream
            </span>
            <span style={{
              fontSize: 11, padding: '2px 8px', borderRadius: 10, fontWeight: 700,
              background: 'rgba(59,130,246,0.15)', color: '#93c5fd', border: '1px solid rgba(59,130,246,0.3)',
            }}>
              {events.length} events
            </span>
          </div>
          <div style={{ maxHeight: 280, overflowY: 'auto' }}>
            {events.length === 0 ? (
              <div style={{ padding: '30px 16px', textAlign: 'center', color: 'var(--text-muted)' }}>
                <div style={{ fontSize: 24, marginBottom: 8 }}>📡</div>
                <div style={{ fontSize: 13 }}>Listening for events…</div>
              </div>
            ) : (
              events.map((ev, i) => <EventRow key={i} ev={ev} />)
            )}
          </div>
        </div>
      </div>

      {/* Windows Event Log Threats */}
      {threats.length > 0 && (
        <div className="card">
          <div className="card-header">
            <span className="card-title"><AlertTriangle size={16} /> Detected Threats</span>
            <button className="btn btn-primary btn-sm" onClick={handleAutoIngest} disabled={autoIngesting}>
              <Zap size={13} /> Convert to Incidents
            </button>
          </div>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Alert ID</th>
                  <th>Source</th>
                  <th>Type</th>
                  <th>Description</th>
                  <th>Severity</th>
                  <th>Score</th>
                </tr>
              </thead>
              <tbody>
                {threats.slice(0, 20).map((t, i) => (
                  <tr key={i}>
                    <td><span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--accent-cyan)' }}>{t.alert_id || t.threat?.alert_id || '—'}</span></td>
                    <td style={{ fontSize: 12, color: 'var(--text-muted)' }}>{t.source || '—'}</td>
                    <td style={{ fontSize: 12 }}>{t.incident_type || t.event_type || '—'}</td>
                    <td style={{ fontSize: 12, maxWidth: 240, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: 'var(--text-secondary)' }}>
                      {t.description || t.classification_hint || '—'}
                    </td>
                    <td>
                      <span className={`severity-badge ${(t.severity || 'medium').toLowerCase()}`}>
                        {t.severity || 'Medium'}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: 13,
                        color: (t.severity_score ?? 0) >= 80 ? '#ef4444' : (t.severity_score ?? 0) >= 60 ? '#f97316' : '#eab308'
                      }}>
                        {(t.severity_score ?? t.threat?.severity_score ?? 0).toFixed(0)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
