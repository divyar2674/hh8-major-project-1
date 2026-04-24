import { useLocation } from 'react-router-dom';
import { Shield, Wifi, WifiOff } from 'lucide-react';

const PAGE_TITLES = {
  '/':          { title:'Dashboard',      sub:'Security Operations Center' },
  '/incidents': { title:'Incidents',      sub:'Track & manage security incidents' },
  '/alerts':    { title:'Alert Intake',   sub:'Ingest & review security alerts' },
  '/playbooks': { title:'Playbooks',      sub:'Automated response workflows' },
  '/analyze':   { title:'AI Analyzer',   sub:'ML-powered incident classification' },
  '/audit':     { title:'Audit Log',      sub:'Full system activity trail' },
  '/monitor':   { title:'Live Monitor',   sub:'Real-time system health' },
};

export default function Topbar({ wsConnected }) {
  const { pathname } = useLocation();

  const key = Object.keys(PAGE_TITLES).find(k => k !== '/' && pathname.startsWith(k)) || '/';
  const { title, sub } = PAGE_TITLES[key] || PAGE_TITLES['/'];

  return (
    <header className="topbar">
      <div className="topbar-left">
        <div>
          <div className="topbar-title">{title}</div>
          <div className="topbar-subtitle">{sub}</div>
        </div>
      </div>
      <div className="topbar-right">
        <div style={{ display:'flex', alignItems:'center', gap:6, fontSize:12,
          color: wsConnected ? 'var(--accent-green)' : 'var(--text-muted)',
          background: wsConnected ? 'rgba(16,185,129,0.08)' : 'rgba(100,100,100,0.1)',
          border: `1px solid ${wsConnected ? 'rgba(16,185,129,0.2)' : 'rgba(100,100,100,0.2)'}`,
          padding:'5px 12px', borderRadius:20 }}>
          {wsConnected ? <Wifi size={13} /> : <WifiOff size={13} />}
          {wsConnected ? 'Live' : 'Offline'}
        </div>
        <div style={{ display:'flex', alignItems:'center', gap:8, fontSize:12, color:'var(--accent-green)',
          background:'rgba(16,185,129,0.08)', border:'1px solid rgba(16,185,129,0.2)',
          padding:'5px 12px', borderRadius:20 }}>
          <Shield size={13} />
          T10 AIRPS v3.0
        </div>
      </div>
    </header>
  );
}
