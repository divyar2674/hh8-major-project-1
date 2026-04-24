import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ToastProvider } from './context/ToastContext';
import Sidebar from './components/Sidebar';
import Topbar from './components/Topbar';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import IncidentsPage from './pages/IncidentsPage';
import IncidentDetailPage from './pages/IncidentDetailPage';
import PlaybooksPage from './pages/PlaybooksPage';
import AlertsPage from './pages/AlertsPage';
import AuditPage from './pages/AuditPage';
import AIAnalyzePage from './pages/AIAnalyzePage';
import useMonitorWebSocket from './hooks/useMonitorWebSocket';

function ProtectedLayout() {
  const { user } = useAuth();
  const { connected } = useMonitorWebSocket();
  if (!user) return <Navigate to="/login" replace />;
  return (
    <div className="app-layout">
      <Sidebar />
      <div className="main-content">
        <Topbar wsConnected={connected} />
        <Routes>
          <Route path="/"               element={<DashboardPage />} />
          <Route path="/incidents"      element={<IncidentsPage />} />
          <Route path="/incidents/:id"  element={<IncidentDetailPage />} />
          <Route path="/playbooks"      element={<PlaybooksPage />} />
          <Route path="/alerts"         element={<AlertsPage />} />
          <Route path="/analyze"        element={<AIAnalyzePage />} />
          <Route path="/audit"          element={<AuditPage />} />
          <Route path="*"              element={<Navigate to="/" />} />
        </Routes>
      </div>
    </div>
  );
}

function LoginGate() {
  const { user } = useAuth();
  if (user) return <Navigate to="/" replace />;
  return <LoginPage />;
}

export default function App() {
  return (
    <AuthProvider>
      <ToastProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginGate />} />
            <Route path="/*"    element={<ProtectedLayout />} />
          </Routes>
        </BrowserRouter>
      </ToastProvider>
    </AuthProvider>
  );
}
