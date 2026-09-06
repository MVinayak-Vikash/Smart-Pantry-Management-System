import React, { useState, useEffect } from 'react';
import type { AlertLog } from '../../services/api';
import { api } from '../../services/api';
import {
  Bell,
  AlertTriangle,
  AlertOctagon,
  Info,
  CheckCircle2,
  RefreshCw,
  Check,
} from 'lucide-react';

interface AlertsViewProps {
  onRefresh: () => void;
}

export const AlertsView: React.FC<AlertsViewProps> = ({ onRefresh }) => {
  const [alerts, setAlerts] = useState<AlertLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [unresolvedOnly, setUnresolvedOnly] = useState(false);
  const [severityFilter, setSeverityFilter] = useState<'ALL' | 'CRITICAL' | 'WARNING' | 'INFO'>('ALL');
  const [resolvingId, setResolvingId] = useState<number | null>(null);

  const fetchAlerts = async () => {
    setLoading(true);
    try {
      const data = await api.getAlerts(unresolvedOnly);
      setAlerts(data);
    } catch (err) {
      console.error('Failed to load alerts:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, [unresolvedOnly]);

  const handleResolve = async (id: number) => {
    setResolvingId(id);
    try {
      await api.resolveAlert(id);
      await fetchAlerts();
      onRefresh();
    } catch (err) {
      alert(`Failed to resolve alert: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setResolvingId(null);
    }
  };

  const filteredAlerts = alerts.filter((a) => {
    if (severityFilter === 'ALL') return true;
    return a.severity === severityFilter;
  });

  const criticalCount = alerts.filter((a) => a.severity === 'CRITICAL' && !a.is_resolved).length;
  const warningCount = alerts.filter((a) => a.severity === 'WARNING' && !a.is_resolved).length;
  const unresolvedCount = alerts.filter((a) => !a.is_resolved).length;

  const getSeverityStyle = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
        return { bg: 'rgba(239, 68, 68, 0.15)', text: '#F87171', border: '#EF4444', icon: AlertOctagon };
      case 'WARNING':
        return { bg: 'rgba(245, 158, 11, 0.15)', text: '#FBBF24', border: '#F59E0B', icon: AlertTriangle };
      default:
        return { bg: 'rgba(56, 189, 248, 0.15)', text: '#38BDF8', border: '#38BDF8', icon: Info };
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="glass-panel" style={{ padding: '20px 24px', borderRadius: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <h2 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Bell size={22} color="var(--brand-primary)" />
              Smart Alerts & Anomaly Center
            </h2>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Proactive notifications for low stock, high intake velocity, and hardware anomalies
            </p>
          </div>

          <button
            onClick={fetchAlerts}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 14px',
              borderRadius: '8px',
              background: 'var(--bg-card)',
              border: '1px solid var(--border-color)',
              color: 'var(--text-secondary)',
              fontSize: '13px',
              cursor: 'pointer',
            }}
          >
            <RefreshCw size={14} /> Refresh Alerts
          </button>
        </div>
      </div>

      {/* Triage KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
        <div className="glass-panel" style={{ padding: '20px', borderRadius: '14px' }}>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Unresolved Incidents</span>
          <p style={{ fontSize: '24px', fontWeight: 800, color: unresolvedCount > 0 ? '#F87171' : '#34D399', marginTop: '4px' }}>
            {unresolvedCount}
          </p>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '6px', display: 'block' }}>
            Requires attention or review
          </span>
        </div>

        <div className="glass-panel" style={{ padding: '20px', borderRadius: '14px' }}>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Critical Incidents</span>
          <p style={{ fontSize: '24px', fontWeight: 800, color: '#EF4444', marginTop: '4px' }}>
            {criticalCount}
          </p>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '6px', display: 'block' }}>
            Stock near runout or severe anomaly
          </span>
        </div>

        <div className="glass-panel" style={{ padding: '20px', borderRadius: '14px' }}>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Warnings</span>
          <p style={{ fontSize: '24px', fontWeight: 800, color: '#F59E0B', marginTop: '4px' }}>
            {warningCount}
          </p>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '6px', display: 'block' }}>
            Intake velocity above baseline
          </span>
        </div>

        <div className="glass-panel" style={{ padding: '20px', borderRadius: '14px' }}>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Total Incident History</span>
          <p style={{ fontSize: '24px', fontWeight: 800, color: '#38BDF8', marginTop: '4px' }}>
            {alerts.length}
          </p>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '6px', display: 'block' }}>
            Total logged alerts
          </span>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div style={{ display: 'flex', gap: '8px' }}>
          {(['ALL', 'CRITICAL', 'WARNING', 'INFO'] as const).map((sev) => (
            <button
              key={sev}
              onClick={() => setSeverityFilter(sev)}
              style={{
                padding: '7px 14px',
                borderRadius: '8px',
                fontSize: '12px',
                fontWeight: 600,
                cursor: 'pointer',
                border: '1px solid',
                borderColor: severityFilter === sev ? 'var(--brand-primary)' : 'var(--border-color)',
                background: severityFilter === sev ? 'rgba(79, 70, 229, 0.15)' : 'var(--bg-card)',
                color: severityFilter === sev ? 'var(--brand-primary-light)' : 'var(--text-secondary)',
              }}
            >
              {sev}
            </button>
          ))}
        </div>

        <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', color: 'var(--text-secondary)', cursor: 'pointer' }}>
          <input
            type="checkbox"
            checked={unresolvedOnly}
            onChange={(e) => setUnresolvedOnly(e.target.checked)}
            style={{ cursor: 'pointer' }}
          />
          Show unresolved only
        </label>
      </div>

      {/* Alerts Table */}
      <div className="glass-panel" style={{ padding: '24px', borderRadius: '16px' }}>
        {loading ? (
          <div style={{ padding: '40px', textAlign: 'center' }}>
            <RefreshCw size={24} className="animate-spin" color="var(--brand-primary)" style={{ margin: '0 auto 12px' }} />
            <p style={{ color: 'var(--text-secondary)' }}>Loading alerts list...</p>
          </div>
        ) : filteredAlerts.length === 0 ? (
          <div style={{ padding: '40px', textAlign: 'center' }}>
            <CheckCircle2 size={36} color="#34D399" style={{ margin: '0 auto 12px' }} />
            <h4 style={{ fontSize: '16px', color: 'var(--text-primary)', fontWeight: 600 }}>All Systems Nominal</h4>
            <p style={{ color: 'var(--text-muted)', fontSize: '13px', marginTop: '4px' }}>
              No active alerts matching your filter criteria.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredAlerts.map((alert) => {
              const sStyle = getSeverityStyle(alert.severity);
              const Icon = sStyle.icon;

              return (
                <div
                  key={alert.id}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '16px 20px',
                    borderRadius: '12px',
                    background: alert.is_resolved ? 'transparent' : 'var(--bg-card-subtle)',
                    border: alert.is_resolved ? '1px solid var(--border-color)' : `1px solid ${sStyle.border}44`,
                    gap: '16px',
                    flexWrap: 'wrap',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: '14px', flex: 1, minWidth: '260px' }}>
                    <div
                      style={{
                        padding: '8px',
                        borderRadius: '10px',
                        background: sStyle.bg,
                        color: sStyle.text,
                        flexShrink: 0,
                      }}
                    >
                      <Icon size={18} />
                    </div>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <h4 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)' }}>
                          {alert.title}
                        </h4>
                        <span
                          style={{
                            padding: '2px 8px',
                            borderRadius: '10px',
                            fontSize: '10px',
                            fontWeight: 700,
                            background: sStyle.bg,
                            color: sStyle.text,
                            border: `1px solid ${sStyle.border}`,
                          }}
                        >
                          {alert.severity}
                        </span>
                        {alert.is_resolved && (
                          <span style={{ fontSize: '11px', color: '#34D399', display: 'flex', alignItems: 'center', gap: '3px' }}>
                            <CheckCircle2 size={12} /> Resolved
                          </span>
                        )}
                      </div>
                      <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                        {alert.message}
                      </p>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '6px', display: 'block' }}>
                        {alert.created_at ? new Date(alert.created_at).toLocaleString() : 'Recent'} {alert.item_name && `• Container: ${alert.item_name}`}
                      </span>
                    </div>
                  </div>

                  <div>
                    {!alert.is_resolved && (
                      <button
                        onClick={() => handleResolve(alert.id)}
                        disabled={resolvingId === alert.id}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                          padding: '7px 14px',
                          borderRadius: '8px',
                          background: 'rgba(16, 185, 129, 0.15)',
                          border: '1px solid rgba(16, 185, 129, 0.3)',
                          color: '#34D399',
                          fontSize: '12px',
                          fontWeight: 600,
                          cursor: 'pointer',
                        }}
                      >
                        <Check size={14} />
                        {resolvingId === alert.id ? 'Resolving...' : 'Acknowledge & Resolve'}
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
