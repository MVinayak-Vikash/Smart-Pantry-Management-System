import React, { useState } from 'react';
import type { Item, Prediction } from '../../services/api';
import { api } from '../../services/api';
import {
  Boxes,
  Search,
  ArrowRight,
  Calendar,
  PlusCircle,
  RefreshCw,
  CheckCircle2,
} from 'lucide-react';

interface InventoryViewProps {
  items: Item[];
  predictions: Prediction[];
  onSelectItem: (itemId: number) => void;
  onRefresh: () => void;
}

export const InventoryView: React.FC<InventoryViewProps> = ({
  items,
  predictions,
  onSelectItem,
  onRefresh,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'AVAILABLE' | 'LOW' | 'UNAVAILABLE'>('all');
  const [restockModalItem, setRestockModalItem] = useState<Item | null>(null);
  const [restockWeight, setRestockWeight] = useState<number>(1000);
  const [isRestocking, setIsRestocking] = useState(false);
  const [restockSuccess, setRestockSuccess] = useState<string | null>(null);

  const predMap = new Map<number, Prediction>();
  predictions.forEach((p) => predMap.set(p.item_id, p));

  const filteredItems = items.filter((item) => {
    const matchesSearch = item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (item.category && item.category.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesStatus = statusFilter === 'all' || item.availability_status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const handleQuickRestock = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!restockModalItem) return;
    setIsRestocking(true);
    try {
      const newWeight = Math.min(
        restockModalItem.initial_quantity,
        restockModalItem.current_quantity + restockWeight
      );
      await api.postWeightReading(restockModalItem.id, newWeight);
      setRestockSuccess(`Successfully restocked ${restockModalItem.name} to ${newWeight}${restockModalItem.unit}!`);
      setTimeout(() => {
        setRestockSuccess(null);
        setRestockModalItem(null);
        onRefresh();
      }, 1200);
    } catch (err) {
      alert(`Restock failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsRestocking(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'AVAILABLE':
        return { bg: 'rgba(16, 185, 129, 0.12)', border: '#10B981', text: '#34D399', label: 'Optimal Stock' };
      case 'LOW':
        return { bg: 'rgba(245, 158, 11, 0.12)', border: '#F59E0B', text: '#FBBF24', label: 'Low Stock' };
      case 'UNAVAILABLE':
        return { bg: 'rgba(239, 68, 68, 0.12)', border: '#EF4444', text: '#F87171', label: 'Refill Required' };
      default:
        return { bg: 'rgba(148, 163, 184, 0.12)', border: '#94A3B8', text: '#CBD5E1', label: status };
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Controls */}
      <div className="glass-panel" style={{ padding: '20px 24px', borderRadius: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <h2 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Boxes size={22} color="var(--brand-primary)" />
              Smart Pantry Inventory
            </h2>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Real-time telemetry from continuous weight sensors & load cells
            </p>
          </div>

          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            {/* Search Input */}
            <div style={{ position: 'relative', minWidth: '220px' }}>
              <Search
                size={16}
                color="var(--text-muted)"
                style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }}
              />
              <input
                type="text"
                placeholder="Search items..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                style={{
                  width: '100%',
                  padding: '9px 12px 9px 36px',
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '10px',
                  color: 'var(--text-primary)',
                  fontSize: '13px',
                  outline: 'none',
                }}
              />
            </div>

            {/* Status Filter */}
            <div style={{ display: 'flex', gap: '6px' }}>
              {(['all', 'AVAILABLE', 'LOW', 'UNAVAILABLE'] as const).map((st) => (
                <button
                  key={st}
                  onClick={() => setStatusFilter(st)}
                  style={{
                    padding: '8px 14px',
                    borderRadius: '8px',
                    fontSize: '12px',
                    fontWeight: 600,
                    border: '1px solid',
                    borderColor: statusFilter === st ? 'var(--brand-primary)' : 'var(--border-color)',
                    background: statusFilter === st ? 'rgba(79, 70, 229, 0.15)' : 'var(--bg-card)',
                    color: statusFilter === st ? 'var(--brand-primary-light)' : 'var(--text-secondary)',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                  }}
                >
                  {st === 'all' ? 'All Containers' : st === 'AVAILABLE' ? 'Optimal' : st === 'LOW' ? 'Low' : 'Needs Refill'}
                </button>
              ))}
            </div>

            <button
              onClick={onRefresh}
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
              <RefreshCw size={14} /> Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Grid of Inventory Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))',
          gap: '20px',
        }}
      >
        {filteredItems.map((item) => {
          const pred = predMap.get(item.id);
          const capacity = item.initial_quantity || 1000;
          const fillPct = Math.round(Math.min(100, Math.max(0, (item.current_quantity / capacity) * 100)));
          const statusStyle = getStatusColor(item.availability_status);
          const remainingDays = pred?.remaining_days_ml ?? pred?.remaining_days_math ?? item.remaining_days ?? 0;

          return (
            <div
              key={item.id}
              className="glass-panel"
              style={{
                borderRadius: '18px',
                padding: '24px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                transition: 'all 0.25s ease',
                cursor: 'pointer',
                position: 'relative',
                overflow: 'hidden',
              }}
              onClick={() => onSelectItem(item.id)}
            >
              {/* Card Header */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                  <div>
                    <span
                      style={{
                        fontSize: '11px',
                        textTransform: 'uppercase',
                        letterSpacing: '0.06em',
                        color: 'var(--text-muted)',
                        fontWeight: 600,
                      }}
                    >
                      Container #{item.id} • {item.category || 'Pantry Staple'}
                    </span>
                    <h3 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)', marginTop: '2px' }}>
                      {item.name}
                    </h3>
                  </div>
                  <span
                    style={{
                      padding: '4px 10px',
                      borderRadius: '20px',
                      fontSize: '11px',
                      fontWeight: 600,
                      background: statusStyle.bg,
                      color: statusStyle.text,
                      border: `1px solid ${statusStyle.border}`,
                    }}
                  >
                    {statusStyle.label}
                  </span>
                </div>

                {/* Fill Gauge */}
                <div style={{ marginBottom: '20px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px', fontSize: '13px' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Capacity Fill Level</span>
                    <span style={{ fontWeight: 700, color: statusStyle.text }}>{fillPct}%</span>
                  </div>
                  <div
                    style={{
                      width: '100%',
                      height: '10px',
                      background: 'rgba(255, 255, 255, 0.06)',
                      borderRadius: '5px',
                      overflow: 'hidden',
                    }}
                  >
                    <div
                      style={{
                        width: `${fillPct}%`,
                        height: '100%',
                        background: `linear-gradient(90deg, ${statusStyle.border}aa, ${statusStyle.border})`,
                        borderRadius: '5px',
                        transition: 'width 0.4s ease-out',
                      }}
                    />
                  </div>
                </div>

                {/* Metrics Breakdown Grid */}
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr',
                    gap: '12px',
                    background: 'var(--bg-card-subtle)',
                    padding: '14px',
                    borderRadius: '12px',
                    marginBottom: '18px',
                    border: '1px solid var(--border-color)',
                  }}
                >
                  <div>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Current Stock</span>
                    <p style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)', marginTop: '2px' }}>
                      {item.current_quantity} <span style={{ fontSize: '11px', fontWeight: 500 }}>{item.unit}</span>
                    </p>
                  </div>
                  <div>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Max Capacity</span>
                    <p style={{ fontSize: '15px', fontWeight: 700, color: '#38BDF8', marginTop: '2px' }}>
                      {capacity} <span style={{ fontSize: '11px', fontWeight: 500 }}>{item.unit}</span>
                    </p>
                  </div>
                  <div>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Min Safety Threshold</span>
                    <p style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-secondary)', marginTop: '2px' }}>
                      {item.minimum_quantity} {item.unit}
                    </p>
                  </div>
                  <div>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Avg Daily Intake</span>
                    <p style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-secondary)', marginTop: '2px' }}>
                      {item.average_daily_intake ? `${item.average_daily_intake.toFixed(1)} ${item.unit}/d` : 'Computing...'}
                    </p>
                  </div>
                </div>

                {/* Depletion Forecast Box */}
                {pred && (
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '10px 14px',
                      background: 'rgba(79, 70, 229, 0.08)',
                      borderRadius: '10px',
                      border: '1px solid rgba(79, 70, 229, 0.2)',
                      marginBottom: '16px',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Calendar size={15} color="var(--brand-primary-light)" />
                      <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                        Predicted Depletion
                      </span>
                    </div>
                    <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--brand-primary-light)' }}>
                      {pred.predicted_depletion_date || 'N/A'} ({Math.round(remainingDays)}d left)
                    </span>
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div style={{ display: 'flex', gap: '8px', paddingTop: '10px', borderTop: '1px solid var(--border-color)' }}>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setRestockModalItem(item);
                    setRestockWeight(Math.max(200, Math.round(capacity - item.current_quantity)));
                  }}
                  style={{
                    flex: 1,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '6px',
                    padding: '8px 12px',
                    borderRadius: '8px',
                    background: 'rgba(16, 185, 129, 0.12)',
                    border: '1px solid rgba(16, 185, 129, 0.3)',
                    color: '#34D399',
                    fontSize: '12px',
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  <PlusCircle size={14} /> Quick Refill
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onSelectItem(item.id);
                  }}
                  style={{
                    flex: 1,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '6px',
                    padding: '8px 12px',
                    borderRadius: '8px',
                    background: 'rgba(79, 70, 229, 0.15)',
                    border: '1px solid rgba(79, 70, 229, 0.3)',
                    color: 'var(--brand-primary-light)',
                    fontSize: '12px',
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  Inspect <ArrowRight size={14} />
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Restock Modal */}
      {restockModalItem && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.75)',
            backdropFilter: 'blur(6px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '20px',
          }}
          onClick={() => !isRestocking && setRestockModalItem(null)}
        >
          <div
            className="glass-panel"
            style={{
              maxWidth: '460px',
              width: '100%',
              borderRadius: '20px',
              padding: '28px',
              background: '#0B1120',
              border: '1px solid var(--border-color)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '8px' }}>
              Refill Container: {restockModalItem.name}
            </h3>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '20px' }}>
              Current level is {restockModalItem.current_quantity}{restockModalItem.unit} / {restockModalItem.initial_quantity}{restockModalItem.unit} capacity.
            </p>

            {restockSuccess ? (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  padding: '16px',
                  background: 'rgba(16, 185, 129, 0.15)',
                  border: '1px solid rgba(16, 185, 129, 0.3)',
                  borderRadius: '12px',
                  color: '#34D399',
                  fontSize: '14px',
                  fontWeight: 600,
                }}
              >
                <CheckCircle2 size={20} />
                {restockSuccess}
              </div>
            ) : (
              <form onSubmit={handleQuickRestock} className="space-y-4">
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                    Added Amount ({restockModalItem.unit})
                  </label>
                  <input
                    type="number"
                    min={50}
                    max={restockModalItem.initial_quantity - restockModalItem.current_quantity + 500}
                    value={restockWeight}
                    onChange={(e) => setRestockWeight(Number(e.target.value))}
                    required
                    style={{
                      width: '100%',
                      padding: '10px 14px',
                      background: 'var(--bg-card)',
                      border: '1px solid var(--border-color)',
                      borderRadius: '10px',
                      color: 'var(--text-primary)',
                      fontSize: '15px',
                      fontWeight: 600,
                      outline: 'none',
                    }}
                  />
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px', display: 'block' }}>
                    New total stock will become:{' '}
                    <strong>
                      {Math.min(
                        restockModalItem.initial_quantity,
                        restockModalItem.current_quantity + restockWeight
                      )}
                      {restockModalItem.unit}
                    </strong>
                  </span>
                </div>

                <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end', marginTop: '24px' }}>
                  <button
                    type="button"
                    disabled={isRestocking}
                    onClick={() => setRestockModalItem(null)}
                    style={{
                      padding: '10px 18px',
                      borderRadius: '10px',
                      background: 'var(--bg-card)',
                      border: '1px solid var(--border-color)',
                      color: 'var(--text-secondary)',
                      fontSize: '13px',
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isRestocking}
                    style={{
                      padding: '10px 20px',
                      borderRadius: '10px',
                      background: 'var(--brand-primary)',
                      border: 'none',
                      color: '#FFF',
                      fontSize: '13px',
                      fontWeight: 600,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                    }}
                  >
                    {isRestocking ? 'Sending Telemetry...' : 'Confirm Refill'}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
