import React from 'react';
import { RefreshCw, Radio, Sun, Moon } from 'lucide-react';

interface HeaderProps {
  householdName?: string;
  isRefreshing: boolean;
  onRefresh: () => void;
  lastUpdated: string;
  theme: 'light' | 'dark';
  onToggleTheme: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  householdName = 'Primary Residence',
  isRefreshing,
  onRefresh,
  lastUpdated,
  theme,
  onToggleTheme,
}) => {
  // Determine time-based greeting
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  };

  return (
    <header style={headerStyle}>
      {/* Left: Personalized Greeting & Subtitle */}
      <div>
        <h1 style={titleStyle}>
          {getGreeting()}, <span style={highlightStyle}>{householdName}</span>
        </h1>
        <p style={subtitleStyle}>
          Real-time IoT load cell telemetry and AI consumption trajectory.
        </p>
      </div>

      {/* Right: Telemetry Badge, Theme Toggle & Refresh Action */}
      <div style={actionsStyle}>
        <div style={telemetryPillStyle}>
          <span style={pulsingDotStyle} />
          <Radio size={14} color="#10B981" />
          <span>4 IoT Scales Active</span>
        </div>

        <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
          Synced: {lastUpdated || 'Just now'}
        </div>

        {/* Theme Toggle Button */}
        <button
          onClick={onToggleTheme}
          style={themeToggleButtonStyle}
          title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} mode`}
          aria-label="Toggle theme"
        >
          {theme === 'dark' ? (
            <>
              <Sun size={15} color="#FBBF24" />
              <span>Light</span>
            </>
          ) : (
            <>
              <Moon size={15} color="#4F46E5" />
              <span>Dark</span>
            </>
          )}
        </button>

        {/* Refresh Button */}
        <button
          style={refreshButtonStyle}
          onClick={onRefresh}
          disabled={isRefreshing}
          title="Sync with FastAPI backend"
        >
          <RefreshCw
            size={15}
            style={{
              animation: isRefreshing ? 'spin 1s linear infinite' : 'none',
            }}
          />
          <span>{isRefreshing ? 'Syncing...' : 'Refresh'}</span>
        </button>
      </div>
    </header>
  );
};

// ==========================================
// Inline CSS Styles
// ==========================================

const headerStyle: React.CSSProperties = {
  height: 'var(--header-height)',
  backgroundColor: 'var(--bg-header)',
  backdropFilter: 'blur(16px)',
  borderBottom: '1px solid var(--border-subtle)',
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  padding: '0 2.5rem',
  position: 'sticky',
  top: 0,
  zIndex: 90,
};

const titleStyle: React.CSSProperties = {
  fontFamily: 'var(--font-display)',
  fontSize: '1.4rem',
  fontWeight: 700,
  color: 'var(--text-primary)',
  letterSpacing: '-0.02em',
};

const highlightStyle: React.CSSProperties = {
  background: 'linear-gradient(135deg, #38BDF8 0%, #818CF8 100%)',
  WebkitBackgroundClip: 'text',
  WebkitTextFillColor: 'transparent',
};

const subtitleStyle: React.CSSProperties = {
  fontSize: '0.8rem',
  color: 'var(--text-muted)',
  marginTop: '0.1rem',
};

const actionsStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '0.75rem',
};

const telemetryPillStyle: React.CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: '0.45rem',
  padding: '0.35rem 0.85rem',
  backgroundColor: 'rgba(16, 185, 129, 0.08)',
  border: '1px solid rgba(16, 185, 129, 0.25)',
  borderRadius: '9999px',
  fontSize: '0.78rem',
  fontWeight: 600,
  color: '#34D399',
};

const pulsingDotStyle: React.CSSProperties = {
  width: '6px',
  height: '6px',
  backgroundColor: '#10B981',
  borderRadius: '50%',
  boxShadow: '0 0 8px #10B981',
};

const themeToggleButtonStyle: React.CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: '0.4rem',
  padding: '0.45rem 0.85rem',
  backgroundColor: 'var(--bg-card)',
  border: '1px solid var(--border-subtle)',
  borderRadius: '8px',
  color: 'var(--text-primary)',
  fontSize: '0.82rem',
  fontWeight: 600,
  cursor: 'pointer',
  transition: 'all 0.2s ease',
  boxShadow: 'var(--shadow-sm)',
};

const refreshButtonStyle: React.CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: '0.45rem',
  padding: '0.45rem 0.95rem',
  backgroundColor: 'var(--bg-card)',
  border: '1px solid var(--border-subtle)',
  borderRadius: '8px',
  color: 'var(--text-secondary)',
  fontSize: '0.82rem',
  fontWeight: 600,
  cursor: 'pointer',
  transition: 'all 0.15s ease',
  boxShadow: 'var(--shadow-sm)',
};
