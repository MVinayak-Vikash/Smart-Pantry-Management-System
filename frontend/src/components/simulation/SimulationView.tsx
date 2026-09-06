import React, { useState } from 'react';
import type { Item } from '../../services/api';
import { api } from '../../services/api';
import {
  Cpu,
  Play,
  RotateCcw,
  Zap,
  CheckCircle2,
  Send,
  FastForward,
} from 'lucide-react';

interface SimulationViewProps {
  items: Item[];
  onRefresh: () => void;
}

export const SimulationView: React.FC<SimulationViewProps> = ({ items, onRefresh }) => {
  const [selectedItemId, setSelectedItemId] = useState<number>(items[0]?.id || 1);
  const [injectedWeight, setInjectedWeight] = useState<number>(1500);
  const [simDays, setSimDays] = useState<number>(3);
  const [isSendingWeight, setIsSendingWeight] = useState(false);
  const [isSimulatingDays, setIsSimulatingDays] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  // Single weight telemetry injection
  const handleInjectWeight = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSendingWeight(true);
    try {
      await api.postWeightReading(selectedItemId, injectedWeight);
      setStatusMessage(`Injected weight ${injectedWeight}g to container #${selectedItemId} via virtual load cell.`);
      onRefresh();
      setTimeout(() => setStatusMessage(null), 3500);
    } catch (err) {
      alert(`Telemetry injection failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsSendingWeight(false);
    }
  };

  // Preset lifestyle scenario execution
  const handlePresetScenario = async (scenario: 'dinner' | 'festival' | 'refill') => {
    setIsSendingWeight(true);
    try {
      if (scenario === 'dinner') {
        // Deduct 200g from Rice, 20g from Salt
        const rice = items.find((i) => i.name.toLowerCase().includes('rice'));
        const salt = items.find((i) => i.name.toLowerCase().includes('salt'));
        if (rice) await api.postWeightReading(rice.id, Math.max(0, rice.current_quantity - 220));
        if (salt) await api.postWeightReading(salt.id, Math.max(0, salt.current_quantity - 18));
        setStatusMessage('Simulated "Big Family Dinner": Consumed 220g Rice & 18g Salt.');
      } else if (scenario === 'festival') {
        // High spike in Sugar and Ghee
        const sugar = items.find((i) => i.name.toLowerCase().includes('sugar'));
        const ghee = items.find((i) => i.name.toLowerCase().includes('ghee'));
        if (sugar) await api.postWeightReading(sugar.id, Math.max(0, sugar.current_quantity - 350));
        if (ghee) await api.postWeightReading(ghee.id, Math.max(0, ghee.current_quantity - 180));
        setStatusMessage('Simulated "Festival Sweets Preparation": High intake spike triggered in Sugar & Ghee!');
      } else if (scenario === 'refill') {
        // Refill all containers to 85% capacity
        for (const it of items) {
          const refillLevel = Math.round((it.initial_quantity || 2000) * 0.9);
          await api.postWeightReading(it.id, refillLevel);
        }
        setStatusMessage('Simulated "Supermarket Bulk Restock": All pantry containers replenished to 90% capacity.');
      }
      onRefresh();
      setTimeout(() => setStatusMessage(null), 4000);
    } catch (err) {
      alert(`Scenario failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsSendingWeight(false);
    }
  };

  // Multi-day time travel
  const handleAdvanceDays = async () => {
    setIsSimulatingDays(true);
    try {
      const res = await api.simulateAdvanceDays(simDays);
      setStatusMessage(`Advanced timeline by ${res.days_advanced} days. Logged ${res.readings_logged} continuous telemetry readings.`);
      onRefresh();
      setTimeout(() => setStatusMessage(null), 4000);
    } catch (err) {
      alert(`Simulation failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsSimulatingDays(false);
    }
  };

  // Database Reset
  const handleResetDemo = async () => {
    if (!confirm('Are you sure you want to reset demo data back to clean initial states?')) return;
    setIsResetting(true);
    try {
      await api.resetDemoDatabase();
      setStatusMessage('Demo database reset to factory baseline.');
      onRefresh();
      setTimeout(() => setStatusMessage(null), 3000);
    } catch (err) {
      alert(`Reset failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsResetting(false);
    }
  };

  const currentSelectedItem = items.find((i) => i.id === selectedItemId);

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="glass-panel" style={{ padding: '20px 24px', borderRadius: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <h2 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Cpu size={22} color="#38BDF8" />
              Virtual IoT Hardware & Telemetry Simulator
            </h2>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Inject sensor telemetry, trigger synthetic household lifestyle events, and advance simulation time
            </p>
          </div>

          <button
            onClick={handleResetDemo}
            disabled={isResetting}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 14px',
              borderRadius: '8px',
              background: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              color: '#F87171',
              fontSize: '13px',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            <RotateCcw size={14} />
            {isResetting ? 'Resetting...' : 'Reset Demo Database'}
          </button>
        </div>
      </div>

      {statusMessage && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            padding: '14px 18px',
            background: 'rgba(56, 189, 248, 0.15)',
            border: '1px solid rgba(56, 189, 248, 0.3)',
            borderRadius: '12px',
            color: '#38BDF8',
            fontSize: '13px',
            fontWeight: 600,
          }}
        >
          <CheckCircle2 size={18} />
          {statusMessage}
        </div>
      )}

      {/* IoT Node Specifications Bar */}
      <div className="glass-panel" style={{ padding: '20px', borderRadius: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#10B981', boxShadow: '0 0 10px #10B981' }} />
            <div>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>IoT Telemetry Node</span>
              <h4 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)' }}>ESP32-WROOM-32D (Virtual Lab)</h4>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '20px', fontSize: '12px', color: 'var(--text-secondary)' }}>
            <div><span style={{ color: 'var(--text-muted)' }}>Protocol:</span> REST / HTTP 1.1</div>
            <div><span style={{ color: 'var(--text-muted)' }}>ADC:</span> 4x HX711 24-bit</div>
            <div><span style={{ color: 'var(--text-muted)' }}>Sampling:</span> Continuous 10Hz</div>
            <div><span style={{ color: 'var(--text-muted)' }}>Signal:</span> -58 dBm (Active)</div>
          </div>
        </div>
      </div>

      {/* Grid of Simulation Tools */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '20px' }}>
        {/* Tool 1: Single Weight Reading Injection */}
        <div className="glass-panel" style={{ padding: '24px', borderRadius: '16px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Send size={18} color="var(--brand-primary)" /> Inject Live Weight Reading
          </h3>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '18px' }}>
            Simulates a real load cell reading transmitted over WiFi to <code>/api/items/{'{id}'}/weight</code>.
          </p>

          <form onSubmit={handleInjectWeight} className="space-y-4">
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                Target Container
              </label>
              <select
                value={selectedItemId}
                onChange={(e) => setSelectedItemId(Number(e.target.value))}
                style={{
                  width: '100%',
                  padding: '9px 12px',
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '8px',
                  color: 'var(--text-primary)',
                  fontSize: '13px',
                  outline: 'none',
                }}
              >
                {items.map((i) => (
                  <option key={i.id} value={i.id}>
                    Container #{i.id} — {i.name} (Current: {i.current_quantity}{i.unit})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                New Weight Value ({currentSelectedItem?.unit || 'g'})
              </label>
              <input
                type="number"
                min={0}
                max={10000}
                value={injectedWeight}
                onChange={(e) => setInjectedWeight(Number(e.target.value))}
                required
                style={{
                  width: '100%',
                  padding: '9px 12px',
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '8px',
                  color: 'var(--text-primary)',
                  fontSize: '14px',
                  fontWeight: 700,
                  outline: 'none',
                }}
              />
            </div>

            <button
              type="submit"
              disabled={isSendingWeight}
              style={{
                width: '100%',
                padding: '11px',
                background: 'var(--brand-primary)',
                border: 'none',
                borderRadius: '8px',
                color: '#FFF',
                fontSize: '13px',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
              }}
            >
              <Send size={15} />
              {isSendingWeight ? 'Transmitting Reading...' : 'Send Weight Telemetry'}
            </button>
          </form>
        </div>

        {/* Tool 2: Preset Scenarios */}
        <div className="glass-panel" style={{ padding: '24px', borderRadius: '16px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Zap size={18} color="#FBBF24" /> Preset Household Events
            </h3>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '16px' }}>
              Instantly test backend logic for meal cooking, consumption surges, or bulk supermarket restocks.
            </p>

            <div className="space-y-3">
              <button
                onClick={() => handlePresetScenario('dinner')}
                disabled={isSendingWeight}
                style={{
                  width: '100%',
                  padding: '12px 14px',
                  borderRadius: '10px',
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border-color)',
                  textAlign: 'left',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '13px' }}>
                  🍛 Cook Big Family Dinner
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>
                  Deducts ~220g Rice and ~18g Salt to simulate dinner cooking.
                </div>
              </button>

              <button
                onClick={() => handlePresetScenario('festival')}
                disabled={isSendingWeight}
                style={{
                  width: '100%',
                  padding: '12px 14px',
                  borderRadius: '10px',
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border-color)',
                  textAlign: 'left',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                <div style={{ fontWeight: 600, color: '#F87171', fontSize: '13px' }}>
                  ⚡ Festival Preparation (High Intake Anomaly)
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>
                  Deducts 350g Sugar & 180g Ghee to trigger a high consumption alert.
                </div>
              </button>

              <button
                onClick={() => handlePresetScenario('refill')}
                disabled={isSendingWeight}
                style={{
                  width: '100%',
                  padding: '12px 14px',
                  borderRadius: '10px',
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border-color)',
                  textAlign: 'left',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                <div style={{ fontWeight: 600, color: '#34D399', fontSize: '13px' }}>
                  🛒 Supermarket Bulk Restock
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>
                  Refills all containers back to 90% full capacity.
                </div>
              </button>
            </div>
          </div>
        </div>

        {/* Tool 3: Multi-Day Time Advance */}
        <div className="glass-panel" style={{ padding: '24px', borderRadius: '16px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FastForward size={18} color="#A78BFA" /> Timeline Fast-Forward
          </h3>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '18px' }}>
            Simulate realistic multi-day consumption cycles using synthetic household consumption models.
          </p>

          <div className="space-y-4">
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '8px' }}>
                Days to Fast-Forward: <strong style={{ color: 'var(--brand-primary-light)' }}>{simDays} Days</strong>
              </label>
              <div style={{ display: 'flex', gap: '8px' }}>
                {[1, 3, 7, 14].map((d) => (
                  <button
                    type="button"
                    key={d}
                    onClick={() => setSimDays(d)}
                    style={{
                      flex: 1,
                      padding: '8px',
                      borderRadius: '8px',
                      border: '1px solid',
                      borderColor: simDays === d ? 'var(--brand-primary)' : 'var(--border-color)',
                      background: simDays === d ? 'rgba(79, 70, 229, 0.2)' : 'var(--bg-card)',
                      color: simDays === d ? 'var(--brand-primary-light)' : 'var(--text-secondary)',
                      fontSize: '13px',
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    +{d}d
                  </button>
                ))}
              </div>
            </div>

            <div style={{ padding: '12px', background: 'var(--bg-card-subtle)', border: '1px solid var(--border-color)', borderRadius: '10px', fontSize: '12px', color: 'var(--text-secondary)' }}>
              Simulates daily consumption with weekend variance, calculates daily intake stats, and trains ML models automatically.
            </div>

            <button
              onClick={handleAdvanceDays}
              disabled={isSimulatingDays}
              style={{
                width: '100%',
                padding: '11px',
                background: 'linear-gradient(135deg, #4F46E5, #7C3AED)',
                border: 'none',
                borderRadius: '8px',
                color: '#FFF',
                fontSize: '13px',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
              }}
            >
              <Play size={15} />
              {isSimulatingDays ? 'Advancing Time...' : `Fast-Forward ${simDays} Days`}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
