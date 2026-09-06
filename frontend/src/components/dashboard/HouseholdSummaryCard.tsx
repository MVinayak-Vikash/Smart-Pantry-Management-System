import React from 'react';
import { Users, Flame, Award } from 'lucide-react';
import type { HouseholdProfile, Item, DietSummary } from '../../services/api';

interface HouseholdSummaryProps {
  household: HouseholdProfile | null;
  items: Item[];
  dietSummary: DietSummary | null;
  onEditProfile: () => void;
}

export const HouseholdSummaryCard: React.FC<HouseholdSummaryProps> = ({
  household,
  items,
  dietSummary,
  onEditProfile,
}) => {
  const familySize = household?.family_size ?? 4;
  const adults = household?.adults ?? 2;
  const children = household?.children ?? 1;
  const elderly = household?.elderly ?? 1;

  // Estimated calories from tracked pantry foods
  const pantryCalories = Math.round(
    dietSummary?.tracked_pantry_intake?.calories_kcal ??
    items.reduce((acc, it) => acc + ((it.average_daily_intake || 0) * (it.calories_per_100g || 130)) / 100, 0)
  );

  return (
    <div style={containerStyle}>
      <div style={headerStyle}>
        <div style={titleWrapStyle}>
          <Users size={20} color="#818CF8" />
          <h2 style={titleStyle}>Household Demographics & Profile</h2>
        </div>
        <button style={editBtnStyle} onClick={onEditProfile}>
          Edit Profile
        </button>
      </div>

      <div style={contentGridStyle}>
        {/* Headcount Card */}
        <div style={boxStyle}>
          <span style={labelStyle}>Total Family Size</span>
          <div style={valStyle}>{familySize} Members</div>
          <div style={breakdownStyle}>
            <span>Adults: <strong>{adults}</strong></span> •{' '}
            <span>Children: <strong>{children}</strong></span> •{' '}
            <span>Elderly: <strong>{elderly}</strong></span>
          </div>
        </div>

        {/* Tracked Pantry Items */}
        <div style={boxStyle}>
          <span style={labelStyle}>Tracked Containers</span>
          <div style={{ ...valStyle, color: '#38BDF8' }}>{items.length} Staples</div>
          <div style={subStyle}>Rice, Sugar, Salt, Ghee on IoT scales</div>
        </div>

        {/* Estimated Tracked Calories */}
        <div style={boxStyle}>
          <span style={labelStyle}>Pantry Energy Output</span>
          <div style={{ ...valStyle, color: '#F59E0B' }}>
            <Flame size={18} color="#F59E0B" style={{ display: 'inline', marginRight: '4px' }} />
            {pantryCalories.toLocaleString()} kcal/day
          </div>
          <div style={disclaimerSubStyle}>
            Estimated calories from tracked pantry foods
          </div>
        </div>

        {/* Dietary Goal */}
        <div style={boxStyle}>
          <span style={labelStyle}>Dietary Objective</span>
          <div style={{ ...valStyle, color: '#10B981', fontSize: '1.05rem' }}>
            <Award size={16} color="#10B981" style={{ display: 'inline', marginRight: '4px' }} />
            {household?.dietary_goal || 'BALANCED'}
          </div>
          <div style={subStyle}>
            Scale Multiplier: <strong>x{(familySize / 4).toFixed(2)}</strong> (Base: 4)
          </div>
        </div>
      </div>
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
  marginBottom: '1rem',
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

const editBtnStyle: React.CSSProperties = {
  fontSize: '0.78rem',
  fontWeight: 600,
  color: '#818CF8',
  backgroundColor: 'rgba(129, 140, 248, 0.1)',
  border: '1px solid rgba(129, 140, 248, 0.25)',
  borderRadius: '6px',
  padding: '0.35rem 0.75rem',
  cursor: 'pointer',
};

const contentGridStyle: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
  gap: '1rem',
};

const boxStyle: React.CSSProperties = {
  backgroundColor: 'rgba(8, 12, 20, 0.5)',
  border: '1px solid var(--border-muted)',
  borderRadius: '10px',
  padding: '0.9rem 1rem',
};

const labelStyle: React.CSSProperties = {
  fontSize: '0.72rem',
  color: 'var(--text-muted)',
  marginBottom: '0.25rem',
  display: 'block',
};

const valStyle: React.CSSProperties = {
  fontFamily: 'var(--font-display)',
  fontSize: '1.35rem',
  fontWeight: 800,
  color: 'var(--text-primary)',
  marginBottom: '0.2rem',
};

const breakdownStyle: React.CSSProperties = {
  fontSize: '0.72rem',
  color: 'var(--text-secondary)',
};

const subStyle: React.CSSProperties = {
  fontSize: '0.72rem',
  color: 'var(--text-muted)',
};

const disclaimerSubStyle: React.CSSProperties = {
  fontSize: '0.68rem',
  color: 'var(--text-muted)',
  fontStyle: 'italic',
};
