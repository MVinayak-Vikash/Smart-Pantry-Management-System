import React from 'react';
import { Boxes, CheckCircle2, AlertTriangle, Hourglass, BellRing } from 'lucide-react';
import type { DashboardSummary, Prediction, AlertLog } from '../../services/api';

interface KpiRowProps {
  summary: DashboardSummary | null;
  predictions: Prediction[];
  alerts: AlertLog[];
}

export const KpiRow: React.FC<KpiRowProps> = ({ summary, predictions, alerts }) => {
  const totalItems = summary?.total_items ?? 4;
  const availableCount = summary?.available_count ?? 4;
  const lowCount = summary?.low_count ?? 0;

  // Count items predicted to run out in <= 5 days
  const predictedStockouts = predictions.filter(
    (p) => p.remaining_days_ml !== null && p.remaining_days_ml <= 5.0
  ).length;

  // Active (unresolved) alerts
  const activeAlerts = alerts.filter((a) => !a.is_resolved).length;

  const kpis = [
    {
      label: 'TOTAL ITEMS',
      value: totalItems,
      icon: <Boxes size={18} color="#38BDF8" />,
      color: '#38BDF8',
      sub: 'Monitored smart containers',
    },
    {
      label: 'AVAILABLE',
      value: availableCount,
      icon: <CheckCircle2 size={18} color="#10B981" />,
      color: '#10B981',
      sub: 'Stock levels healthy',
    },
    {
      label: 'LOW STOCK',
      value: lowCount,
      icon: <AlertTriangle size={18} color="#F59E0B" />,
      color: '#F59E0B',
      sub: lowCount === 0 ? 'No low stock' : `${lowCount} near minimum`,
    },
    {
      label: 'PREDICTED STOCKOUTS',
      value: predictedStockouts,
      icon: <Hourglass size={18} color="#F43F5E" />,
      color: '#F43F5E',
      sub: 'Runout in ≤ 5 days',
    },
    {
      label: 'ACTIVE ALERTS',
      value: activeAlerts,
      icon: <BellRing size={18} color="#A855F7" />,
      color: '#A855F7',
      sub: activeAlerts === 0 ? 'All systems optimal' : 'Requires review',
    },
  ];

  return (
    <div style={containerStyle}>
      {kpis.map((kpi, idx) => (
        <div key={idx} style={cardStyle}>
          <div style={headerStyle}>
            <span style={labelStyle}>{kpi.label}</span>
            <div style={{ ...iconWrapperStyle, backgroundColor: `${kpi.color}18` }}>
              {kpi.icon}
            </div>
          </div>
          <div style={{ ...valueStyle, color: kpi.color }}>{kpi.value}</div>
          <div style={subTextStyle}>{kpi.sub}</div>
        </div>
      ))}
    </div>
  );
};

const containerStyle: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
  gap: '1rem',
  marginBottom: '1.75rem',
  width: '100%',
};

const cardStyle: React.CSSProperties = {
  backgroundColor: 'var(--bg-card)',
  border: '1px solid var(--border-subtle)',
  borderRadius: '12px',
  padding: '1.15rem 1.25rem',
  display: 'flex',
  flexDirection: 'column',
  transition: 'border-color 0.15s ease',
};

const headerStyle: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  marginBottom: '0.4rem',
};

const labelStyle: React.CSSProperties = {
  fontSize: '0.72rem',
  fontWeight: 700,
  letterSpacing: '0.06em',
  color: 'var(--text-muted)',
  whiteSpace: 'nowrap',
};

const iconWrapperStyle: React.CSSProperties = {
  width: '32px',
  height: '32px',
  borderRadius: '8px',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
};

const valueStyle: React.CSSProperties = {
  fontFamily: 'var(--font-display)',
  fontSize: '1.9rem',
  fontWeight: 800,
  letterSpacing: '-0.03em',
  lineHeight: 1.1,
  margin: '0.2rem 0',
};

const subTextStyle: React.CSSProperties = {
  fontSize: '0.75rem',
  color: 'var(--text-secondary)',
  whiteSpace: 'nowrap',
  overflow: 'hidden',
  textOverflow: 'ellipsis',
};
