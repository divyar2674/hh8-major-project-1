import { useNavigate, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, AlertTriangle, BookOpen, Bell,
  Brain, FileText, Shield, LogOut, Activity,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const NAV = [
  { section: 'OVERVIEW', items: [
    { to:'/',          label:'Dashboard',      icon:LayoutDashboard },
    { to:'/incidents', label:'Incidents',      icon:AlertTriangle   },
    { to:'/alerts',    label:'Alert Intake',   icon:Bell            },
  ]},
  { section: 'RESPONSE', items: [
    { to:'/playbooks', label:'Playbooks',      icon:BookOpen        },
    { to:'/analyze',   label:'AI Analyzer',   icon:Brain           },
  ]},
  { section: 'MONITORING', items: [
    { to:'/audit',     label:'Audit Log',      icon:FileText        },
  ]},
];

export default function Sidebar() {
  const navigate   = useNavigate();
  const { pathname } = useLocation();
  const { user, logout } = useAuth();

  const isActive = (to) => to === '/' ? pathname === '/' : pathname.startsWith(to);

  return (
    <aside className="sidebar">
      {/* Brand */}
      <div className="sidebar-brand">
        <div className="sidebar-brand-icon">🛡️</div>
        <div>
          <div className="sidebar-brand-title">T10 — AIRPS</div>
          <div className="sidebar-brand-sub">AI Incident Response</div>
        </div>
      </div>

      {/* Nav */}
      <nav className="sidebar-nav">
        {NAV.map(({ section, items }) => (
          <div key={section} className="sidebar-section">
            <div className="sidebar-section-label">{section}</div>
            {items.map(({ to, label, icon: Icon }) => (
              <button
                key={to}
                className={`nav-item ${isActive(to) ? 'active' : ''}`}
                onClick={() => navigate(to)}
                id={`nav-${label.toLowerCase().replace(/ /g,'-')}`}
              >
                <Icon size={17} className="nav-icon" />
                {label}
              </button>
            ))}
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className="sidebar-footer">
        <div className="user-info-card">
          <div className="user-avatar">{user?.username?.[0]?.toUpperCase() || 'U'}</div>
          <div style={{ flex:1, minWidth:0 }}>
            <div className="user-name">{user?.full_name || user?.username}</div>
            <div className="user-role">{user?.role}</div>
          </div>
          <button onClick={logout} data-tooltip="Logout" style={{ background:'none', border:'none', color:'var(--text-muted)', cursor:'pointer', padding:4 }}>
            <LogOut size={15} />
          </button>
        </div>
      </div>
    </aside>
  );
}
