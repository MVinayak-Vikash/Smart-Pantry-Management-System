import React from 'react';
import type {
  DashboardSummary,
  Prediction,
  AlertLog,
  HouseholdProfile,
  ItemConsumptionHistory,
  MLEvaluation,
  DietSummary,
} from '../../services/api';
import { KpiRow } from './KpiRow';
import { PantryHealthSection } from './PantryHealthSection';
import { SmartPantryGrid } from './SmartPantryGrid';
import { ConsumptionChart } from './ConsumptionChart';
import { StockForecastSection } from './StockForecastSection';
import { SmartInsightsSection } from './SmartInsightsSection';
import { AlertsSummarySection } from './AlertsSummarySection';
import { HouseholdSummaryCard } from './HouseholdSummaryCard';

interface DashboardViewProps {
  summary: DashboardSummary | null;
  predictions: Prediction[];
  alerts: AlertLog[];
  household: HouseholdProfile | null;
  histories: Record<number, ItemConsumptionHistory>;
  mlEvaluation: MLEvaluation | null;
  dietSummary: DietSummary | null;
  onSelectItem: (itemId: number) => void;
  onResolveAlert: (id: number) => void;
  onNavigateToAlerts: () => void;
  onNavigateToHousehold: () => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  summary,
  predictions,
  alerts,
  household,
  histories,
  mlEvaluation,
  dietSummary,
  onSelectItem,
  onResolveAlert,
  onNavigateToAlerts,
  onNavigateToHousehold,
}) => {
  const items = summary?.items || [];

  return (
    <div>
      {/* 1. KPI Metric Cards Row */}
      <KpiRow summary={summary} predictions={predictions} alerts={alerts} />

      {/* 2. Pantry Health Composite Score & Gauges */}
      <PantryHealthSection summary={summary} alerts={alerts} mlEvaluation={mlEvaluation} />

      {/* 3. Smart Pantry Container Cards with Sparklines */}
      <SmartPantryGrid items={items} predictions={predictions} onSelectItem={onSelectItem} />

      {/* 4. 30-Day Interactive Consumption Chart */}
      <ConsumptionChart items={items} histories={histories} />

      {/* 5. Stock Depletion Forecast Trajectory */}
      {predictions.length > 0 && <StockForecastSection predictions={predictions} />}

      {/* 6. Smart Analytical Insights */}
      <SmartInsightsSection items={items} predictions={predictions} />

      {/* 7. Lower Split: System Alerts Center & Household Demographics */}
      <div style={lowerSplitGridStyle}>
        <AlertsSummarySection
          alerts={alerts}
          onResolveAlert={onResolveAlert}
          onViewAllAlerts={onNavigateToAlerts}
        />
        <HouseholdSummaryCard
          household={household}
          items={items}
          dietSummary={dietSummary}
          onEditProfile={onNavigateToHousehold}
        />
      </div>
    </div>
  );
};

const lowerSplitGridStyle: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))',
  gap: '1.5rem',
  alignItems: 'start',
};
