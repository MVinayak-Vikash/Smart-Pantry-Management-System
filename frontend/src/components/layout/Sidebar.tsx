import React from 'react';
import {
  LayoutDashboard,
  Boxes,
  Eye,
  LineChart,
  Sparkles,
  Salad,
  ClipboardList,
  ChefHat,
  ShoppingCart,
  Bell,
  Home,
  Sliders,
  Cpu,
} from 'lucide-react';

export type ActivePage =
  | 'dashboard'
  | 'inventory'
  | 'item-details'
  | 'consumption'
  | 'predictions'
  | 'nutrition'
  | 'meal-logs'
  | 'recipes'
  | 'shopping'
  | 'alerts'
  | 'household'
  | 'simulation'
  | 'ml-evaluation';

interface SidebarProps {
  activePage: ActivePage;
  onSelectPage: (page: ActivePage) => void;
  unreadAlertsCount: number;
  isBackendOnline: boolean;
  lastUpdated: string;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activePage,
  onSelectPage,
  unreadAlertsCount,
  isBackendOnline,
  lastUpdated,
}) => {
  return (
    <aside style={sidebarStyle}>
      {/* Brand Header */}
      <div style={brandStyle}>
        <div style={logoIconWrapStyle}>
          <Boxes size={22} color="#38BDF8" />
        </div>
        <div>
          <div style={brandTitleStyle}>Smart Pantry</div>
          <div style={brandSubStyle}>IoT Analytics Platform</div>
        </div>
      </div>

      {/* Navigation Sections */}
      <nav style={navStyle}>
        {/* Main Dashboard */}
        <button
          style={activePage === 'dashboard' ? activeNavItemStyle : navItemStyle}
          onClick={() => onSelectPage('dashboard')}
        >
          <LayoutDashboard size={18} />
          <span>Dashboard</span>
        </button>

        {/* Pantry Section */}
        <div style={sectionHeadingStyle}>PANTRY</div>
        <button
          style={activePage === 'inventory' ? activeNavItemStyle : navItemStyle}
          onClick={() => onSelectPage('inventory')}
        >
          <Boxes size={18} />
          <span>Inventory</span>
        </button>
        <button
          style={activePage === 'item-details' ? activeNavItemStyle : navItemStyle}
          onClick={() => onSelectPage('item-details')}
        >
          <Eye size={18} />
          <span>Item Details</span>
        </button>

        {/* Analytics Section */}
        <div style={sectionHeadingStyle}>ANALYTICS</div>
        <button
          style={activePage === 'consumption' ? activeNavItemStyle : navItemStyle}
          onClick={() => onSelectPage('consumption')}
        >
          <LineChart size={18} />
          <span>Consumption</span>
        </button>
        <button
          style={activePage === 'predictions' ? activeNavItemStyle : navItemStyle}
          onClick={() => onSelectPage('predictions')}
        >
          <Sparkles size={18} />
          <span>Predictions</span>
        </button>

        {/* Nutrition Section */}
        <div style={sectionHeadingStyle}>NUTRITION</div>
        <button
          style={activePage === 'nutrition' ? activeNavItemStyle : navItemStyle}
          onClick={() => onSelectPage('nutrition')}
        >
          <Salad size={18} />
          <span>Diet & Nutrition</span>
        </button>
        <button
          style={activePage === 'meal-logs' ? activeNavItemStyle : navItemStyle}
          onClick={() => onSelectPage('meal-logs')}
        >
          <ClipboardList size={18} />
          <span>Meal Logs</span>
        </button>

        {/* Recommendations Section */}
        <div style={sectionHeadingStyle}>RECOMMENDATIONS</div>
        <button
          style={activePage === 'recipes' ? activeNavItemStyle : navItemStyle}
          onClick={() => onSelectPage('recipes')}
        >
          <ChefHat size={18} />
          <span>Recipes</span>
        </button>
        <button
          style={activePage === 'shopping' ? activeNavItemStyle : navItemStyle}
          onClick={() => onSelectPage('shopping')}
        >
          <ShoppingCart size={18} />
          <span>Shopping List</span>
        </button>

        {/* Alerts */}
        <div style={sectionHeadingStyle}>SYSTEM</div>
        <button
          style={activePage === 'alerts' ? activeNavItemStyle : navItemStyle}
          onClick={() => onSelectPage('alerts')}
        >
          <Bell size={18} />
          <span style={{ flex: 1, textAlign: 'left' }}>Alerts</span>
          {unreadAlertsCount > 0 && (
            <span style={alertCountBadgeStyle}>{unreadAlertsCount}</span>
          )}
        </button>

        <button
          style={activePage === 'household' ? activeNavItemStyle : navItemStyle}
          onClick={() => onSelectPage('household')}
        >
          <Home size={18} />
          <span>Household</span>
        </button>

        {/* Settings Section */}
        <div style={sectionHeadingStyle}>SETTINGS & HARDWARE</div>
        <button
          style={activePage === 'simulation' ? activeNavItemStyle : navItemStyle}
          onClick={() => onSelectPage('simulation')}
        >
          <Sliders size={18} />
          <span>Simulation Bench</span>
        </button>
        <button
          style={activePage === 'ml-evaluation' ? activeNavItemStyle : navItemStyle}
          onClick={() => onSelectPage('ml-evaluation')}
        >
          <Cpu size={18} />
          <span>ML Evaluation</span>
        </button>
      </nav>

      {/* Bottom Status Footer */}
      <div style={footerStatusStyle}>
        <div style={statusRowStyle}>
          <span
            style={{
              ...statusDotStyle,
              backgroundColor: isBackendOnline ? '#10B981' : '#F59E0B',
              boxShadow: isBackendOnline ? '0 0 8px #10B981' : '0 0 8px #F59E0B',
            }}
          />
          <span style={statusTextStyle}>
            {isBackendOnline ? 'FastAPI Online' : 'Backend Disconnected'}
          </span>
        </div>
        <div style={statusSubStyle}>Simulation / Live Mode</div>
        <div style={lastUpdatedStyle}>Updated: {lastUpdated || 'Just now'}</div>
      </div>
    </aside>
  );
};

// ==========================================
// Inline CSS Styles
// ==========================================

const sidebarStyle: React.CSSProperties = {
  width: 'var(--sidebar-width)',
  backgroundColor: 'var(--bg-sidebar)',
  borderRight: '1px solid var(--border-subtle)',
  display: 'flex',
  flexDirection: 'column',
  position: 'fixed',
  top: 0,
  bottom: 0,
  left: 0,
  zIndex: 100,
  userSelect: 'none',
};

const brandStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '0.75rem',
  padding: '1.25rem 1.25rem 1rem 1.25rem',
  borderBottom: '1px solid var(--border-muted)',
};

const logoIconWrapStyle: React.CSSProperties = {
  width: '36px',
  height: '36px',
  borderRadius: '8px',
  backgroundColor: 'rgba(56, 189, 248, 0.12)',
  border: '1px solid rgba(56, 189, 248, 0.3)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
};

const brandTitleStyle: React.CSSProperties = {
  fontFamily: 'var(--font-display)',
  fontSize: '1.05rem',
  fontWeight: 700,
  color: 'var(--text-primary)',
  letterSpacing: '-0.02em',
};

const brandSubStyle: React.CSSProperties = {
  fontSize: '0.72rem',
  color: 'var(--text-muted)',
};

const navStyle: React.CSSProperties = {
  flex: 1,
  padding: '0.75rem 0.65rem',
  overflowY: 'auto',
  display: 'flex',
  flexDirection: 'column',
  gap: '0.15rem',
};

const sectionHeadingStyle: React.CSSProperties = {
  fontSize: '0.68rem',
  fontWeight: 700,
  letterSpacing: '0.08em',
  color: 'var(--text-muted)',
  padding: '0.85rem 0.75rem 0.35rem 0.75rem',
  textTransform: 'uppercase',
};

const navItemStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '0.65rem',
  padding: '0.55rem 0.75rem',
  borderRadius: '8px',
  backgroundColor: 'transparent',
  border: 'none',
  color: 'var(--text-secondary)',
  fontSize: '0.84rem',
  fontWeight: 500,
  cursor: 'pointer',
  transition: 'all 0.15s ease',
  width: '100%',
  textAlign: 'left',
};

const activeNavItemStyle: React.CSSProperties = {
  ...navItemStyle,
  backgroundColor: 'rgba(56, 189, 248, 0.1)',
  color: '#38BDF8',
  fontWeight: 600,
};

const alertCountBadgeStyle: React.CSSProperties = {
  backgroundColor: '#EF4444',
  color: '#FFFFFF',
  fontSize: '0.68rem',
  fontWeight: 700,
  borderRadius: '9999px',
  padding: '0.1rem 0.45rem',
};

const footerStatusStyle: React.CSSProperties = {
  padding: '1rem 1.25rem',
  borderTop: '1px solid var(--border-muted)',
  backgroundColor: 'var(--bg-card-subtle)',
};

const statusRowStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '0.5rem',
  marginBottom: '0.2rem',
};

const statusDotStyle: React.CSSProperties = {
  width: '8px',
  height: '8px',
  borderRadius: '50%',
};

const statusTextStyle: React.CSSProperties = {
  fontSize: '0.78rem',
  fontWeight: 600,
  color: 'var(--text-primary)',
};

const statusSubStyle: React.CSSProperties = {
  fontSize: '0.72rem',
  color: 'var(--text-muted)',
};

const lastUpdatedStyle: React.CSSProperties = {
  fontSize: '0.68rem',
  color: 'var(--text-muted)',
  marginTop: '0.25rem',
};
