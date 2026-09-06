import { useState, useEffect, useCallback } from 'react';
import { Sidebar } from './components/layout/Sidebar';
import type { ActivePage } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { DashboardView } from './components/dashboard/DashboardView';
import { InventoryView } from './components/inventory/InventoryView';
import { ItemDetailsView } from './components/inventory/ItemDetailsView';
import { AnalyticsView } from './components/analytics/AnalyticsView';
import { NutritionView } from './components/nutrition/NutritionView';
import { RecipesView } from './components/recipes/RecipesView';
import { ShoppingListView } from './components/shopping/ShoppingListView';
import { AlertsView } from './components/alerts/AlertsView';
import { HouseholdView } from './components/household/HouseholdView';
import { SimulationView } from './components/simulation/SimulationView';
import { MLEvaluationView } from './components/ml/MLEvaluationView';

import type {
  DashboardSummary,
  Item,
  Prediction,
  AlertLog,
  HouseholdProfile,
  DietSummary,
  MLEvaluation,
  ItemConsumptionHistory,
} from './services/api';
import { api } from './services/api';
import { AlertCircle, RefreshCw } from 'lucide-react';

export function App() {
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    const saved = localStorage.getItem('smart-pantry-theme');
    if (saved === 'light' || saved === 'dark') return saved;
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('smart-pantry-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  };

  const [activePage, setActivePage] = useState<ActivePage>('dashboard');
  const [selectedItemId, setSelectedItemId] = useState<number>(1);

  // Global application data
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [items, setItems] = useState<Item[]>([]);
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [alerts, setAlerts] = useState<AlertLog[]>([]);
  const [household, setHousehold] = useState<HouseholdProfile | null>(null);
  const [dietSummary, setDietSummary] = useState<DietSummary | null>(null);
  const [mlEvaluation, setMLEvaluation] = useState<MLEvaluation | null>(null);
  const [histories, setHistories] = useState<Record<number, ItemConsumptionHistory>>({});

  // Network & UI status
  const [isBackendOnline, setIsBackendOnline] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [lastUpdated, setLastUpdated] = useState<string>('Just now');
  const [networkError, setNetworkError] = useState<string | null>(null);

  // Load all data
  const loadData = useCallback(async () => {
    setIsRefreshing(true);
    try {
      // 1. Core items and summary
      const [sumData, itemsData, predsData, alertsData, hhData, dietData, mlData] = await Promise.all([
        api.getDashboardSummary().catch((e) => {
          console.warn('Dashboard summary fetch failed:', e);
          return null;
        }),
        api.getItems().catch((e) => {
          console.warn('Items fetch failed:', e);
          return [];
        }),
        api.getPredictions().catch((e) => {
          console.warn('Predictions fetch failed:', e);
          return [];
        }),
        api.getAlerts(false).catch((e) => {
          console.warn('Alerts fetch failed:', e);
          return [];
        }),
        api.getHousehold().catch((e) => {
          console.warn('Household fetch failed:', e);
          return null;
        }),
        api.getDietSummary('today').catch((e) => {
          console.warn('Diet summary fetch failed:', e);
          return null;
        }),
        api.getMLEvaluation().catch((e) => {
          console.warn('ML Evaluation fetch failed:', e);
          return null;
        }),
      ]);

      setSummary(sumData);
      setItems(itemsData);
      setPredictions(predsData);
      setAlerts(alertsData);
      setHousehold(hhData);
      setDietSummary(dietData);
      setMLEvaluation(mlData);

      // 2. Fetch consumption history for each item
      if (itemsData.length > 0) {
        const historyMap: Record<number, ItemConsumptionHistory> = {};
        await Promise.all(
          itemsData.map(async (it: Item) => {
            try {
              const hist = await api.getItemConsumption(it.id);
              historyMap[it.id] = hist;
            } catch (err) {
              console.warn(`Failed history for item ${it.id}:`, err);
            }
          })
        );
        setHistories(historyMap);
      }

      setIsBackendOnline(true);
      setNetworkError(null);
      setLastUpdated(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
    } catch (err: any) {
      console.error('Data loading error:', err);
      setIsBackendOnline(false);
      setNetworkError(err?.message || 'Unable to communicate with FastAPI backend.');
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    // Auto-poll telemetry every 30 seconds
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, [loadData]);

  // Navigate to item details
  const handleSelectItem = (itemId: number) => {
    setSelectedItemId(itemId);
    setActivePage('item-details');
  };

  const unreadAlertsCount = alerts.filter((a) => !a.is_resolved).length;

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--bg-primary)' }}>
      {/* Sidebar Navigation */}
      <Sidebar
        activePage={activePage}
        onSelectPage={setActivePage}
        unreadAlertsCount={unreadAlertsCount}
        isBackendOnline={isBackendOnline}
        lastUpdated={lastUpdated}
      />

      {/* Main Content Area */}
      <div style={{ flex: 1, marginLeft: '260px', display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        {/* Top Header */}
        <Header
          householdName={household?.household_name || 'Primary Residence'}
          isRefreshing={isRefreshing}
          onRefresh={loadData}
          lastUpdated={lastUpdated}
          theme={theme}
          onToggleTheme={toggleTheme}
        />

        {/* Network Error / Connection Banner */}
        {!isBackendOnline && (
          <div
            style={{
              margin: '16px 32px 0 32px',
              padding: '12px 18px',
              background: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: '12px',
              color: '#F87171',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              fontSize: '13px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <AlertCircle size={18} />
              <span>
                <strong>Backend Disconnected:</strong> {networkError || 'Cannot connect to API server.'} Please ensure the FastAPI backend is running on <code>127.0.0.1:8000</code>.
              </span>
            </div>
            <button
              onClick={loadData}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 12px',
                background: 'rgba(239, 68, 68, 0.25)',
                border: 'none',
                borderRadius: '6px',
                color: '#FFF',
                fontSize: '12px',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              <RefreshCw size={13} /> Retry Connection
            </button>
          </div>
        )}

        {/* View Switcher Container */}
        <main style={{ flex: 1, padding: '24px 32px 48px 32px' }}>
          {activePage === 'dashboard' && (
            <DashboardView
              summary={summary}
              predictions={predictions}
              alerts={alerts}
              household={household}
              histories={histories}
              mlEvaluation={mlEvaluation}
              dietSummary={dietSummary}
              onSelectItem={handleSelectItem}
              onResolveAlert={async (id) => {
                await api.resolveAlert(id);
                loadData();
              }}
              onNavigateToAlerts={() => setActivePage('alerts')}
              onNavigateToHousehold={() => setActivePage('household')}
            />
          )}

          {activePage === 'inventory' && (
            <InventoryView
              items={items}
              predictions={predictions}
              onSelectItem={handleSelectItem}
              onRefresh={loadData}
            />
          )}

          {activePage === 'item-details' && (
            <ItemDetailsView
              itemId={selectedItemId}
              onBack={() => setActivePage('inventory')}
              onRefresh={loadData}
            />
          )}

          {(activePage === 'consumption' || activePage === 'predictions') && (
            <AnalyticsView
              items={items}
              predictions={predictions}
              histories={histories}
            />
          )}

          {(activePage === 'nutrition' || activePage === 'meal-logs') && (
            <NutritionView
              dietSummary={dietSummary}
              household={household}
              onRefresh={loadData}
            />
          )}

          {activePage === 'recipes' && (
            <RecipesView household={household} />
          )}

          {activePage === 'shopping' && (
            <ShoppingListView onRefresh={loadData} />
          )}

          {activePage === 'alerts' && (
            <AlertsView onRefresh={loadData} />
          )}

          {activePage === 'household' && (
            <HouseholdView
              household={household}
              onRefresh={loadData}
            />
          )}

          {activePage === 'simulation' && (
            <SimulationView
              items={items}
              onRefresh={loadData}
            />
          )}

          {activePage === 'ml-evaluation' && (
            <MLEvaluationView />
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
