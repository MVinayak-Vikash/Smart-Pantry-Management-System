import React from 'react';
import type { AlertLog } from '../../services/api';
import { Bell, CheckCircle2, AlertOctagon, AlertTriangle, Info, ArrowRight } from 'lucide-react';

interface AlertsSummaryProps {
  alerts: AlertLog[];
  onResolveAlert: (id: number) => void;
  onViewAllAlerts: () => void;
}

export const AlertsSummarySection: React.FC<AlertsSummaryProps> = ({
  alerts,
  onResolveAlert,
  onViewAllAlerts,
}) => {
  const unresolvedAlerts = alerts.filter((a) => !a.is_resolved);

  const getSeverityIcon = (sev: string) => {
    switch (sev) {
      case 'CRITICAL':
        return <AlertOctagon size={16} color="#EF4444" />;
      case 'WARNING':
        return <AlertTriangle size={16} color="#F59E0B" />;
      default:
        return <Info size={16} color="#38BDF8" />;
    }
  };

  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case 'CRITICAL':
        return { label: 'CRITICAL', bg: 'var(--color-critical-bg)', color: 'var(--color-critical)', border: 'var(--color-critical-border)' };
      case 'WARNING':
        return { label: 'WARNING', bg: 'var(--color-low-bg)', color: 'var(--color-low)', border: 'var(--color-low-border)' };
      default:
        return { label: 'INFO', bg: 'var(--color-info-bg)', color: 'var(--color-info)', border: 'var(--color-info-border)' };
    }
  };

  return (
    <div style={containerStyle}>
      <div style={headerStyle}>
        <div style={titleWrapStyle}>
          <Bell size={20} color="#EF4444" />
          <h2 style={titleStyle}>System Alert Center</h2>
          {unresolvedAlerts.length > 0 && (
            <span style={countBadgeStyle}>{unresolvedAlerts.length} Active</span>
          )}
        </div>

        <button style={viewAllBtnStyle} onClick={onViewAllAlerts}>
          <span>View All Alerts</span>
          <ArrowRight size={14} />
        </button>
      </div>

      <p style={subtitleStyle}>
        Autonomous threshold notifications and statistical anomalies deduplicated within 24-hour windows.
      </p>

      {unresolvedAlerts.length === 0 ? (
        <div style={emptyBoxStyle}>
          <CheckCircle2 size={20} color="#10B981" />
          <div>
            <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>All Systems Optimal</div>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              No active stockout or dietary alerts require attention.
            </div>
          </div>
        </div>
      ) : (
        <div style={listStyle}>
          {unresolvedAlerts.slice(0, 4).map((a) => {
            const badge = getSeverityBadge(a.severity);
            const timeStr = a.created_at ? a.created_at.slice(0, 16).replace('T', ' ') : 'Recent';

            return (
              <div key={a.id} style={alertCardStyle}>
                <div style={alertLeftStyle}>
                  <div style={iconWrapStyle}>{getSeverityIcon(a.severity)}</div>
                  <div>
                    <div style={titleRowStyle}>
                      <span style={{ ...badgeStyle, backgroundColor: badge.bg, color: badge.color, borderColor: badge.border }}>
                        {badge.label}
                      </span>
                      {a.item_name && <span style={itemNameStyle}>[{a.item_name}]</span>}
                      <span style={alertTitleStyle}>{a.title}</span>
                    </div>
                    <p style={alertMsgStyle}>{a.message}</p>
                    <div style={timestampStyle}>Logged: {timeStr}</div>
                  </div>
                </div>

                <button
                  style={resolveBtnStyle}
                  onClick={() => onResolveAlert(a.id)}
                  title="Mark this alert as resolved"
                >
                  <CheckCircle2 size={14} />
                  <span>Resolve</span>
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

const containerStyle: React.CSSProperties = {
  backgroundColor: 'var(--bg-card)',
  border: '1px solid var(--border-subtle)',
  borderRadius: '14px',
  padding: '1.5rem',
  marginBottom: '2rem',
};

const headerStyle: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  marginBottom: '0.35rem',
};

const titleWrapStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '0.6rem',
};

const titleStyle: React.CSSProperties = {
  fontFamily: 'var(--font-display)',
  fontSize: '1.25rem',
  fontWeight: 700,
  color: 'var(--text-primary)',
};

const countBadgeStyle: React.CSSProperties = {
  fontSize: '0.72rem',
  fontWeight: 700,
  padding: '0.15rem 0.55rem',
  borderRadius: '9999px',
  backgroundColor: 'rgba(239, 68, 68, 0.15)',
  color: '#F87171',
  border: '1px solid rgba(239, 68, 68, 0.3)',
};

const viewAllBtnStyle: React.CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: '0.35rem',
  fontSize: '0.78rem',
  fontWeight: 600,
  color: '#38BDF8',
  backgroundColor: 'transparent',
  border: 'none',
  cursor: 'pointer',
};

const subtitleStyle: React.CSSProperties = {
  fontSize: '0.8rem',
  color: 'var(--text-muted)',
  marginBottom: '1rem',
};

const emptyBoxStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '0.75rem',
  padding: '1.25rem',
  backgroundColor: 'rgba(16, 185, 129, 0.05)',
  border: '1px solid rgba(16, 185, 129, 0.2)',
  borderRadius: '10px',
};

const listStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: '0.75rem',
};

const alertCardStyle: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  padding: '0.85rem 1.15rem',
  backgroundColor: 'rgba(8, 12, 20, 0.45)',
  border: '1px solid var(--border-muted)',
  borderRadius: '10px',
  gap: '1rem',
};

const alertLeftStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'flex-start',
  gap: '0.75rem',
  flex: 1,
};

const iconWrapStyle: React.CSSProperties = {
  marginTop: '0.15rem',
  flexShrink: 0,
};

const titleRowStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '0.5rem',
  flexWrap: 'wrap',
  marginBottom: '0.2rem',
};

const badgeStyle: React.CSSProperties = {
  fontSize: '0.68rem',
  fontWeight: 700,
  padding: '0.15rem 0.5rem',
  borderRadius: '4px',
  border: '1px solid transparent',
};

const itemNameStyle: React.CSSProperties = {
  fontSize: '0.8rem',
  fontWeight: 700,
  color: 'var(--text-primary)',
};

const alertTitleStyle: React.CSSProperties = {
  fontSize: '0.85rem',
  fontWeight: 600,
  color: 'var(--text-primary)',
};

const alertMsgStyle: React.CSSProperties = {
  fontSize: '0.78rem',
  color: 'var(--text-secondary)',
  lineHeight: 1.4,
};

const timestampStyle: React.CSSProperties = {
  fontSize: '0.68rem',
  color: 'var(--text-muted)',
  marginTop: '0.25rem',
};

const resolveBtnStyle: React.CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: '0.35rem',
  padding: '0.4rem 0.85rem',
  backgroundColor: 'rgba(16, 185, 129, 0.1)',
  border: '1px solid rgba(16, 185, 129, 0.3)',
  borderRadius: '6px',
  color: '#34D399',
  fontSize: '0.75rem',
  fontWeight: 600,
  cursor: 'pointer',
  transition: 'all 0.15s ease',
  flexShrink: 0,
};
