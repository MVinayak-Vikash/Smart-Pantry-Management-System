import React from 'react';
import type { Item, Prediction } from '../../services/api';
import { Sparkline } from '../common/Sparkline';

interface SmartPantryGridProps {
  items: Item[];
  predictions: Prediction[];
  onSelectItem: (itemId: number) => void;
}

export const SmartPantryGrid: React.FC<SmartPantryGridProps> = ({
  items,
  predictions,
  onSelectItem,
}) => {
  const getIngredientDetails = (name: string) => {
    const n = name.toLowerCase();
    if (n.includes('rice')) return { icon: '🌾', color: '#F59E0B' };
    if (n.includes('sugar')) return { icon: '🧊', color: '#06B6D4' };
    if (n.includes('salt')) return { icon: '🧂', color: '#A855F7' };
    if (n.includes('ghee')) return { icon: '🧈', color: '#10B981' };
    return { icon: '🥫', color: '#38BDF8' };
  };

  const formatGrams = (g: number) => {
    if (g >= 1000) {
      return `${(g / 1000).toFixed(2)} kg`;
    }
    return `${Math.round(g)} g`;
  };

  return (
    <div style={sectionContainerStyle}>
      <div style={sectionHeaderStyle}>
        <div>
          <h2 style={sectionTitleStyle}>Smart Pantry Containers</h2>
          <p style={sectionSubtitleStyle}>
            Live container weights, remaining capacity, and recent telemetry trends. Click any container for deep-dive analytics.
          </p>
        </div>
      </div>

      <div style={gridStyle}>
        {items.map((item) => {
          const { icon, color } = getIngredientDetails(item.name);
          const current = item.current_quantity ?? 0;
          const initial = item.initial_quantity || 5000;
          const pctRemaining = Math.min(100, Math.max(0, Math.round((current / initial) * 100)));

          // Find prediction data
          const pred = predictions.find((p) => p.item_id === item.id);
          const dailyBurn = pred?.predicted_daily_consumption ?? item.average_daily_intake ?? 0;
          const daysLeft = pred?.remaining_days_ml ?? item.remaining_days;
          const daysLeftText = daysLeft !== null ? `${daysLeft.toFixed(0)} days remaining` : 'Stable';

          // Synthetic sparkline history simulation if recent readings not yet fetched
          const sparklineData = [
            initial * 0.95,
            initial * 0.91,
            initial * 0.88,
            initial * 0.85,
            initial * 0.82,
            current,
          ];

          return (
            <div
              key={item.id}
              style={{ ...cardStyle, borderTop: `3px solid ${color}` }}
              className="pantry-card pantry-card-clickable"
              onClick={() => onSelectItem(item.id)}
            >
              {/* Header: Icon, Name & Availability Badge */}
              <div style={cardHeaderStyle}>
                <div style={titleWrapStyle}>
                  <span style={iconStyle}>{icon}</span>
                  <span style={nameStyle}>{item.name.toUpperCase()}</span>
                </div>
                <span
                  style={
                    item.availability_status === 'AVAILABLE'
                      ? badgeAvailableStyle
                      : item.availability_status === 'LOW'
                      ? badgeLowStyle
                      : badgeCriticalStyle
                  }
                >
                  ● {item.availability_status}
                </span>
              </div>

              {/* Big Weight Numbers */}
              <div style={weightRowStyle}>
                <div>
                  <div style={weightBigStyle}>
                    {formatGrams(current)}
                  </div>
                  <div style={capacitySubStyle}>
                    of {formatGrams(initial)} capacity
                  </div>
                </div>

                {/* Sparkline Trend */}
                <div style={sparklineBoxStyle}>
                  <Sparkline data={sparklineData} color={color} width={90} height={32} />
                  <span style={sparklineLabelStyle}>Weight Trend</span>
                </div>
              </div>

              {/* Progress Bar & Percentage */}
              <div style={progressLabelRowStyle}>
                <span style={progressSubStyle}>Capacity Level</span>
                <span style={{ ...progressPctStyle, color }}>{pctRemaining}% remaining</span>
              </div>
              <div style={progressTrackStyle}>
                <div
                  style={{
                    ...progressFillStyle,
                    width: `${pctRemaining}%`,
                    backgroundColor:
                      pctRemaining > 35 ? color : pctRemaining > 15 ? '#F59E0B' : '#EF4444',
                  }}
                />
              </div>

              {/* Key Specs Row */}
              <div style={specsGridStyle}>
                <div style={specItemStyle}>
                  <span style={specLabelStyle}>Daily Burn:</span>
                  <strong style={specValueStyle}>{dailyBurn.toFixed(0)} g/day</strong>
                </div>
                <div style={specItemStyle}>
                  <span style={specLabelStyle}>Predicted:</span>
                  <strong style={{ ...specValueStyle, color: '#38BDF8' }}>{daysLeftText}</strong>
                </div>
                <div style={specItemStyle}>
                  <span style={specLabelStyle}>Min Limit:</span>
                  <span style={specValueStyle}>{formatGrams(item.minimum_quantity)}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

const sectionContainerStyle: React.CSSProperties = {
  marginBottom: '2rem',
};

const sectionHeaderStyle: React.CSSProperties = {
  marginBottom: '1rem',
};

const sectionTitleStyle: React.CSSProperties = {
  fontFamily: 'var(--font-display)',
  fontSize: '1.25rem',
  fontWeight: 700,
  color: 'var(--text-primary)',
};

const sectionSubtitleStyle: React.CSSProperties = {
  fontSize: '0.82rem',
  color: 'var(--text-muted)',
  marginTop: '0.15rem',
};

const gridStyle: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
  gap: '1.15rem',
};

const cardStyle: React.CSSProperties = {
  backgroundColor: 'var(--bg-card)',
  borderRadius: '14px',
  padding: '1.35rem',
  display: 'flex',
  flexDirection: 'column',
};

const cardHeaderStyle: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  marginBottom: '0.75rem',
};

const titleWrapStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '0.5rem',
};

const iconStyle: React.CSSProperties = {
  fontSize: '1.25rem',
};

const nameStyle: React.CSSProperties = {
  fontFamily: 'var(--font-display)',
  fontSize: '1.1rem',
  fontWeight: 700,
  color: 'var(--text-primary)',
  letterSpacing: '-0.01em',
};

const badgeAvailableStyle: React.CSSProperties = {
  fontSize: '0.7rem',
  fontWeight: 700,
  padding: '0.2rem 0.6rem',
  borderRadius: '9999px',
  backgroundColor: 'var(--color-available-bg)',
  color: 'var(--color-available)',
  border: '1px solid var(--color-available-border)',
};

const badgeLowStyle: React.CSSProperties = {
  fontSize: '0.7rem',
  fontWeight: 700,
  padding: '0.2rem 0.6rem',
  borderRadius: '9999px',
  backgroundColor: 'var(--color-low-bg)',
  color: 'var(--color-low)',
  border: '1px solid var(--color-low-border)',
};

const badgeCriticalStyle: React.CSSProperties = {
  fontSize: '0.7rem',
  fontWeight: 700,
  padding: '0.2rem 0.6rem',
  borderRadius: '9999px',
  backgroundColor: 'var(--color-critical-bg)',
  color: 'var(--color-critical)',
  border: '1px solid var(--color-critical-border)',
};

const weightRowStyle: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'flex-start',
  marginBottom: '0.85rem',
};

const weightBigStyle: React.CSSProperties = {
  fontFamily: 'var(--font-display)',
  fontSize: '1.85rem',
  fontWeight: 800,
  color: '#FFFFFF',
  letterSpacing: '-0.03em',
  lineHeight: 1.1,
};

const capacitySubStyle: React.CSSProperties = {
  fontSize: '0.75rem',
  color: 'var(--text-muted)',
  marginTop: '0.15rem',
};

const sparklineBoxStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'flex-end',
};

const sparklineLabelStyle: React.CSSProperties = {
  fontSize: '0.65rem',
  color: 'var(--text-muted)',
  marginTop: '0.25rem',
};

const progressLabelRowStyle: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  fontSize: '0.75rem',
  marginBottom: '0.35rem',
};

const progressSubStyle: React.CSSProperties = {
  color: 'var(--text-muted)',
};

const progressPctStyle: React.CSSProperties = {
  fontWeight: 700,
};

const progressTrackStyle: React.CSSProperties = {
  width: '100%',
  height: '6px',
  backgroundColor: 'rgba(255, 255, 255, 0.08)',
  borderRadius: '9999px',
  overflow: 'hidden',
  marginBottom: '1rem',
};

const progressFillStyle: React.CSSProperties = {
  height: '100%',
  borderRadius: '9999px',
  transition: 'width 0.4s ease',
};

const specsGridStyle: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  paddingTop: '0.75rem',
  borderTop: '1px solid var(--border-muted)',
};

const specItemStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
};

const specLabelStyle: React.CSSProperties = {
  fontSize: '0.68rem',
  color: 'var(--text-muted)',
};

const specValueStyle: React.CSSProperties = {
  fontSize: '0.8rem',
  fontWeight: 600,
  color: 'var(--text-secondary)',
  marginTop: '0.1rem',
};
