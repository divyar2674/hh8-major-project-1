import { createContext, useContext, useState, useCallback } from 'react';

const ToastContext = createContext(null);

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((message, type = 'info') => {
    const id = Date.now();
    setToasts(t => [...t, { id, message, type }]);
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 4000);
  }, []);

  const COLORS = { success:'#10b981', error:'#ef4444', warning:'#f59e0b', info:'#3b82f6' };

  return (
    <ToastContext.Provider value={{ addToast }}>
      {children}
      <div style={{ position:'fixed', bottom:24, right:24, zIndex:9999, display:'flex', flexDirection:'column', gap:8 }}>
        {toasts.map(t => (
          <div key={t.id} style={{
            background:'var(--bg-2)', border:`1px solid ${COLORS[t.type]}40`,
            borderLeft:`4px solid ${COLORS[t.type]}`, borderRadius:8,
            padding:'12px 16px', fontSize:13, color:'var(--text-primary)',
            boxShadow:'0 8px 24px rgba(0,0,0,0.4)', minWidth:260, maxWidth:360,
            animation:'slideUp 0.3s ease',
          }}>
            {t.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export const useToast = () => useContext(ToastContext);
