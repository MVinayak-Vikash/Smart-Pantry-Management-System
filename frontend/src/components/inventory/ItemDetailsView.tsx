import React, { useState, useEffect } from 'react';
import type { Item, Prediction, ItemConsumptionHistory } from '../../services/api';
import { api } from '../../services/api';
import {
  ArrowLeft,
  Calendar,
  HardDrive,
  Cpu,
  Flame,
  Activity,
  RefreshCw,
} from 'lucide-react';
import { Sparkline } from '../common/Sparkline';

interface ItemDetailsProps {
  itemId: number;
  onBack: () => void;
  onRefresh: () => void;
}

export const ItemDetailsView: React.FC<ItemDetailsProps> = ({
  itemId,
  onBack,
  onRefresh,
}) => {
  const [item, setItem] = useState<Item | null>(null);
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [history, setHistory] = useState<ItemConsumptionHistory | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'consumption' | 'forecast' | 'nutrition' | 'telemetry'>('overview');

  useEffect(() => {
    let mounted = true;
    async function loadItemData() {
      setLoading(true);
      try {
        const [itemsData, predsData, histData] = await Promise.all([
          api.getItems(),
          api.getPredictions(),
          api.getItemConsumption(itemId).catch(() => null),
        ]);
        if (mounted) {
          const foundItem = itemsData.find((i: Item) => i.id === itemId) || null;
          const foundPred = predsData.find((p: Prediction) => p.item_id === itemId) || null;
          setItem(foundItem);
          setPrediction(foundPred);
          setHistory(histData);
        }
      } catch (err) {
        console.error('Failed to load item details:', err);
      } finally {
        if (mounted) setLoading(false);
      }
    }
    loadItemData();
    return () => {
      mounted = false;
    };
  }, [itemId]);

  if (loading) {
    return (
      <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', borderRadius: '16px' }}>
        <RefreshCw size={24} className="animate-spin" color="var(--brand-primary)" style={{ margin: '0 auto 12px' }} />
        <p style={{ color: 'var(--text-secondary)' }}>Loading telemetry and analytics for container #{itemId}...</p>
      </div>
    );
  }

  if (!item) {
    return (
      <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', borderRadius: '16px' }}>
        <p style={{ color: 'var(--status-critical)' }}>Container #{itemId} not found in pantry inventory.</p>
        <button
          onClick={onBack}
          style={{
            marginTop: '16px',
            padding: '8px 16px',
            background: 'var(--bg-card)',
            border: '1px solid var(--border-color)',
            color: 'var(--text-primary)',
            borderRadius: '8px',
            cursor: 'pointer',
          }}
        >
          <ArrowLeft size={16} style={{ display: 'inline', marginRight: '6px' }} /> Back to Pantry
        </button>
      </div>
    );
  }

  const capacity = item.initial_quantity || 1000;
  const fillPct = Math.round(Math.min(100, Math.max(0, (item.current_quantity / capacity) * 100)));
  const remainingDays = prediction?.remaining_days_ml ?? prediction?.remaining_days_math ?? item.remaining_days ?? 0;

  // Approximate nutritional profile
  const getNutritionPer100g = (name: string) => {
    switch (name.toLowerCase()) {
      case 'rice':
        return { calories: item.calories_per_100g ?? 365, carbs: item.carbs_per_100g ?? 80, protein: item.protein_per_100g ?? 7.1, fat: item.fat_per_100g ?? 0.7, sugar: item.sugar_per_100g ?? 0.1, sodium: item.sodium_per_100g ?? 5 };
      case 'sugar':
        return { calories: item.calories_per_100g ?? 387, carbs: item.carbs_per_100g ?? 100, protein: item.protein_per_100g ?? 0.0, fat: item.fat_per_100g ?? 0.0, sugar: item.sugar_per_100g ?? 99.8, sodium: item.sodium_per_100g ?? 1 };
      case 'salt':
        return { calories: item.calories_per_100g ?? 0, carbs: item.carbs_per_100g ?? 0, protein: item.protein_per_100g ?? 0.0, fat: item.fat_per_100g ?? 0.0, sugar: item.sugar_per_100g ?? 0.0, sodium: item.sodium_per_100g ?? 38758 };
      case 'ghee':
        return { calories: item.calories_per_100g ?? 900, carbs: item.carbs_per_100g ?? 0, protein: item.protein_per_100g ?? 0.0, fat: item.fat_per_100g ?? 99.5, sugar: item.sugar_per_100g ?? 0.0, sodium: item.sodium_per_100g ?? 2 };
      default:
        return { calories: 250, carbs: 40, protein: 5.0, fat: 5.0, sugar: 5.0, sodium: 100 };
    }
  };

  const nut = getNutritionPer100g(item.name);
  const dailyGrams = item.average_daily_intake || 50;
  const dailyCalories = Math.round((nut.calories * dailyGrams) / 100);

  return (
    <div className="space-y-6">
      {/* Header bar */}
      <div className="glass-panel" style={{ padding: '20px 24px', borderRadius: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <button
              onClick={onBack}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '38px',
                height: '38px',
                borderRadius: '10px',
                background: 'var(--bg-card)',
                border: '1px solid var(--border-color)',
                color: 'var(--text-secondary)',
                cursor: 'pointer',
              }}
              title="Back to Inventory"
            >
              <ArrowLeft size={18} />
            </button>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <h1 style={{ fontSize: '24px', fontWeight: 800, color: 'var(--text-primary)' }}>
                  {item.name}
                </h1>
                <span
                  style={{
                    padding: '3px 10px',
                    borderRadius: '20px',
                    fontSize: '11px',
                    fontWeight: 700,
                    background: item.availability_status === 'AVAILABLE' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                    color: item.availability_status === 'AVAILABLE' ? '#34D399' : '#F87171',
                    border: `1px solid ${item.availability_status === 'AVAILABLE' ? '#10B981' : '#EF4444'}`,
                  }}
                >
                  {item.availability_status}
                </span>
              </div>
              <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '3px' }}>
                Container #{item.id} • Category: {item.category || 'Pantry Staple'} • Monitored via HX711 Load Cell
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              onClick={onRefresh}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '9px 16px',
                borderRadius: '10px',
                background: 'var(--bg-card)',
                border: '1px solid var(--border-color)',
                color: 'var(--text-secondary)',
                fontSize: '13px',
                cursor: 'pointer',
              }}
            >
              <RefreshCw size={15} /> Refresh Telemetry
            </button>
          </div>
        </div>
      </div>

      {/* Top 5 Metrics Quick Strip */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '16px',
        }}
      >
        <div className="glass-panel" style={{ padding: '16px 20px', borderRadius: '14px' }}>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Current Gross Stock</span>
          <p style={{ fontSize: '20px', fontWeight: 800, color: 'var(--text-primary)', marginTop: '4px' }}>
            {item.current_quantity} <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>/ {capacity}{item.unit}</span>
          </p>
          <div style={{ marginTop: '8px', width: '100%', height: '6px', background: 'rgba(255,255,255,0.06)', borderRadius: '3px', overflow: 'hidden' }}>
            <div style={{ width: `${fillPct}%`, height: '100%', background: 'var(--brand-primary)', borderRadius: '3px' }} />
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '16px 20px', borderRadius: '14px' }}>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Min Safety Threshold</span>
          <p style={{ fontSize: '20px', fontWeight: 800, color: '#F59E0B', marginTop: '4px' }}>
            {item.minimum_quantity} <span style={{ fontSize: '13px', fontWeight: 500 }}>{item.unit}</span>
          </p>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '6px', display: 'block' }}>
            Triggers low stock alert
          </span>
        </div>

        <div className="glass-panel" style={{ padding: '16px 20px', borderRadius: '14px' }}>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Avg Daily Consumption</span>
          <p style={{ fontSize: '20px', fontWeight: 800, color: '#A78BFA', marginTop: '4px' }}>
            {item.average_daily_intake ? item.average_daily_intake.toFixed(1) : '0.0'} <span style={{ fontSize: '13px', fontWeight: 500 }}>{item.unit}/d</span>
          </p>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '6px', display: 'block' }}>
            Intake Status: {item.intake_status}
          </span>
        </div>

        <div className="glass-panel" style={{ padding: '16px 20px', borderRadius: '14px' }}>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Runout Countdown</span>
          <p style={{ fontSize: '20px', fontWeight: 800, color: remainingDays <= 5 ? '#F87171' : '#34D399', marginTop: '4px' }}>
            {Math.round(remainingDays)} <span style={{ fontSize: '13px', fontWeight: 500 }}>days</span>
          </p>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '6px', display: 'block' }}>
            Depletion: {prediction?.predicted_depletion_date || 'N/A'}
          </span>
        </div>

        <div className="glass-panel" style={{ padding: '16px 20px', borderRadius: '14px' }}>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Est. Daily Calorie Load</span>
          <p style={{ fontSize: '20px', fontWeight: 800, color: '#FB923C', marginTop: '4px' }}>
            ~{dailyCalories} <span style={{ fontSize: '13px', fontWeight: 500 }}>kcal</span>
          </p>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '6px', display: 'block' }}>
            From {dailyGrams.toFixed(0)}{item.unit} daily intake
          </span>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid var(--border-color)', paddingBottom: '2px' }}>
        {[
          { id: 'overview', label: 'Overview & Hardware', icon: HardDrive },
          { id: 'consumption', label: 'Consumption History', icon: Activity },
          { id: 'forecast', label: 'Depletion Forecast', icon: Calendar },
          { id: 'nutrition', label: 'Nutritional Breakdown', icon: Flame },
          { id: 'telemetry', label: 'Raw Telemetry Feed', icon: Cpu },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 18px',
                background: isActive ? 'rgba(79, 70, 229, 0.15)' : 'transparent',
                border: 'none',
                borderBottom: isActive ? '2px solid var(--brand-primary)' : '2px solid transparent',
                borderRadius: '8px 8px 0 0',
                color: isActive ? 'var(--brand-primary-light)' : 'var(--text-secondary)',
                fontSize: '13px',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.2s ease',
              }}
            >
              <Icon size={16} />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab 1: Overview */}
      {activeTab === 'overview' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
          <div className="glass-panel" style={{ padding: '24px', borderRadius: '16px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <HardDrive size={18} color="var(--brand-primary)" /> Container Specifications
            </h3>
            <div className="space-y-3" style={{ fontSize: '13px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Container Identifier</span>
                <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>CONT-00{item.id}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Category</span>
                <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{item.category || 'Pantry Staple'}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Full Capacity</span>
                <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{capacity} {item.unit}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Reorder Threshold</span>
                <span style={{ color: '#F59E0B', fontWeight: 600 }}>{item.minimum_quantity} {item.unit}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <span style={{ color: 'var(--text-secondary)' }}>RFID Tag UID</span>
                <span style={{ color: '#38BDF8', fontWeight: 600 }}>{item.rfid_uid || 'E2 80 68 9A'}</span>
              </div>
            </div>
          </div>

          <div className="glass-panel" style={{ padding: '24px', borderRadius: '16px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Cpu size={18} color="#38BDF8" /> IoT Load Cell Telemetry Node
            </h3>
            <div className="space-y-3" style={{ fontSize: '13px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Sensor Type</span>
                <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>Strain Gauge Load Cell (5kg)</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Analog-to-Digital Converter</span>
                <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>HX711 24-Bit Precision ADC</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <span style={{ color: 'var(--text-secondary)' }}>ESP32 GPIO Pins</span>
                <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>DT: GPIO 21 • SCK: GPIO 22</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Calibration Factor</span>
                <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>-420.50 LSB/g</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Sampling Interval</span>
                <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>10 Hz (Averaged over 5s)</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Consumption History */}
      {activeTab === 'consumption' && (
        <div className="glass-panel" style={{ padding: '24px', borderRadius: '16px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '16px' }}>
            Daily Consumption Records (Past 30 Days)
          </h3>
          {history && history.records && history.records.length > 0 ? (
            <div>
              <div style={{ height: '140px', marginBottom: '24px' }}>
                <Sparkline
                  data={history.records.map((r) => r.consumption)}
                  color="var(--brand-primary)"
                  height={140}
                />
              </div>

              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--border-color)', textAlign: 'left', color: 'var(--text-muted)' }}>
                      <th style={{ padding: '10px 14px' }}>Timestamp</th>
                      <th style={{ padding: '10px 14px' }}>Consumption ({item.unit})</th>
                      <th style={{ padding: '10px 14px' }}>Closing Stock ({item.unit})</th>
                      <th style={{ padding: '10px 14px' }}>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.records.slice(-10).reverse().map((r, idx) => (
                      <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                        <td style={{ padding: '10px 14px', color: 'var(--text-primary)', fontWeight: 600 }}>
                          {r.timestamp.split('T')[0] || r.timestamp}
                        </td>
                        <td style={{ padding: '10px 14px', color: '#A78BFA', fontWeight: 700 }}>
                          {r.consumption.toFixed(1)} {item.unit}
                        </td>
                        <td style={{ padding: '10px 14px', color: 'var(--text-secondary)' }}>
                          {r.current_weight} {item.unit}
                        </td>
                        <td style={{ padding: '10px 14px' }}>
                          <span style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '12px', background: 'rgba(16, 185, 129, 0.12)', color: '#34D399' }}>
                            Logged
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <p style={{ color: 'var(--text-muted)', fontSize: '13px' }}>No recorded consumption logs found for this container yet.</p>
          )}
        </div>
      )}

      {/* Tab 3: Forecast */}
      {activeTab === 'forecast' && (
        <div className="glass-panel" style={{ padding: '24px', borderRadius: '16px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '16px' }}>
            Machine Learning Depletion Forecast
          </h3>
          {prediction ? (
            <div className="space-y-4">
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
                <div style={{ background: 'var(--bg-card-subtle)', padding: '16px', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
                  <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Predicted Depletion Date</span>
                  <p style={{ fontSize: '18px', fontWeight: 700, color: 'var(--brand-primary-light)', marginTop: '4px' }}>
                    {prediction.predicted_depletion_date || 'N/A'}
                  </p>
                </div>
                <div style={{ background: 'var(--bg-card-subtle)', padding: '16px', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
                  <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Predicted Remaining Days</span>
                  <p style={{ fontSize: '18px', fontWeight: 700, color: '#38BDF8', marginTop: '4px' }}>
                    {Math.round(remainingDays)} days
                  </p>
                </div>
                <div style={{ background: 'var(--bg-card-subtle)', padding: '16px', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
                  <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Predicted Daily Intake</span>
                  <p style={{ fontSize: '18px', fontWeight: 700, color: '#A78BFA', marginTop: '4px' }}>
                    {prediction.predicted_daily_consumption.toFixed(1)} {item.unit}/day
                  </p>
                </div>
                <div style={{ background: 'var(--bg-card-subtle)', padding: '16px', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
                  <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Active ML Model</span>
                  <p style={{ fontSize: '18px', fontWeight: 700, color: '#34D399', marginTop: '4px' }}>
                    {prediction.model_used || 'RandomForest'}
                  </p>
                </div>
              </div>

              <div style={{ marginTop: '20px', padding: '16px', background: 'rgba(79, 70, 229, 0.08)', borderRadius: '12px', border: '1px solid rgba(79, 70, 229, 0.2)' }}>
                <h4 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '6px' }}>
                  Recommendation
                </h4>
                <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                  At current intake velocity of {prediction.predicted_daily_consumption.toFixed(1)} {item.unit}/day, pantry stock will reach minimum safety threshold ({item.minimum_quantity} {item.unit}) on <strong>{prediction.predicted_depletion_date}</strong>.
                </p>
              </div>
            </div>
          ) : (
            <p style={{ color: 'var(--text-muted)' }}>No active prediction available.</p>
          )}
        </div>
      )}

      {/* Tab 4: Nutrition Profile */}
      {activeTab === 'nutrition' && (
        <div className="glass-panel" style={{ padding: '24px', borderRadius: '16px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '16px' }}>
            Nutritional Composition Breakdown
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px', marginBottom: '24px' }}>
            <div style={{ background: 'var(--bg-card-subtle)', padding: '14px', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Energy (Calories)</span>
              <p style={{ fontSize: '18px', fontWeight: 700, color: '#FB923C', marginTop: '2px' }}>
                {nut.calories} <span style={{ fontSize: '11px', fontWeight: 500 }}>kcal / 100g</span>
              </p>
            </div>
            <div style={{ background: 'var(--bg-card-subtle)', padding: '14px', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Carbohydrates</span>
              <p style={{ fontSize: '18px', fontWeight: 700, color: '#38BDF8', marginTop: '2px' }}>
                {nut.carbs} <span style={{ fontSize: '11px', fontWeight: 500 }}>g / 100g</span>
              </p>
            </div>
            <div style={{ background: 'var(--bg-card-subtle)', padding: '14px', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Proteins</span>
              <p style={{ fontSize: '18px', fontWeight: 700, color: '#34D399', marginTop: '2px' }}>
                {nut.protein} <span style={{ fontSize: '11px', fontWeight: 500 }}>g / 100g</span>
              </p>
            </div>
            <div style={{ background: 'var(--bg-card-subtle)', padding: '14px', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Fats</span>
              <p style={{ fontSize: '18px', fontWeight: 700, color: '#FBBF24', marginTop: '2px' }}>
                {nut.fat} <span style={{ fontSize: '11px', fontWeight: 500 }}>g / 100g</span>
              </p>
            </div>
            <div style={{ background: 'var(--bg-card-subtle)', padding: '14px', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Sugars</span>
              <p style={{ fontSize: '18px', fontWeight: 700, color: '#F472B6', marginTop: '2px' }}>
                {nut.sugar} <span style={{ fontSize: '11px', fontWeight: 500 }}>g / 100g</span>
              </p>
            </div>
            <div style={{ background: 'var(--bg-card-subtle)', padding: '14px', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Sodium</span>
              <p style={{ fontSize: '18px', fontWeight: 700, color: '#E879F9', marginTop: '2px' }}>
                {nut.sodium} <span style={{ fontSize: '11px', fontWeight: 500 }}>mg / 100g</span>
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Tab 5: Raw Telemetry */}
      {activeTab === 'telemetry' && (
        <div className="glass-panel" style={{ padding: '24px', borderRadius: '16px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '16px' }}>
            Live Load Cell Feed (ESP32 Serial / REST)
          </h3>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '16px' }}>
            Weight telemetry is transmitted to <code>/api/items/{item.id}/weight</code>.
          </p>
          <div style={{ background: '#050811', padding: '16px', borderRadius: '10px', fontFamily: 'monospace', fontSize: '12px', color: '#38BDF8' }}>
            <div>[NODE-01] CONNECTED to Load Cell HX711 on GPIO 21/22</div>
            <div>[NODE-01] Container ID: #{item.id} ({item.name})</div>
            <div>[NODE-01] Current Reading: {item.current_quantity}.0 {item.unit}</div>
            <div>[NODE-01] Minimum Limit: {item.minimum_quantity}.0 {item.unit}</div>
            <div>[NODE-01] Availability Status: {item.availability_status}</div>
            <div>[NODE-01] Intake Status: {item.intake_status}</div>
            <div>[NODE-01] Telemetry heartbeat OK (HTTP 200)</div>
          </div>
        </div>
      )}
    </div>
  );
};
