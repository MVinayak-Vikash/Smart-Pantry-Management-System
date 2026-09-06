import React, { useState, useEffect } from 'react';
import type { ShoppingItem } from '../../services/api';
import { api } from '../../services/api';
import {
  ShoppingCart,
  CheckCircle2,
  PlusCircle,
  RefreshCw,
  Sparkles,
  PackageCheck,
  Check,
} from 'lucide-react';

interface ShoppingListViewProps {
  onRefresh: () => void;
}

export const ShoppingListView: React.FC<ShoppingListViewProps> = ({ onRefresh }) => {
  const [items, setItems] = useState<ShoppingItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'PENDING' | 'PURCHASED'>('all');
  const [actionNotice, setActionNotice] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [restockingId, setRestockingId] = useState<number | null>(null);

  const fetchList = async () => {
    setLoading(true);
    try {
      const data = await api.getShoppingList();
      setItems(data);
    } catch (err) {
      console.error('Failed to load shopping list:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchList();
  }, []);

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      const res = await api.generateShoppingList();
      setActionNotice(`Generated smart restock list: ${res.count} items evaluated.`);
      await fetchList();
      onRefresh();
      setTimeout(() => setActionNotice(null), 3000);
    } catch (err) {
      alert(`Failed to generate list: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsGenerating(false);
    }
  };

  // CORRECT BUSINESS LOGIC: Mark as Purchased changes list status only
  const handleMarkPurchased = async (item: ShoppingItem) => {
    try {
      await api.markShoppingItemPurchased(item.id);
      setActionNotice(`Marked ${item.item_name} as Purchased! (Container weight untouched per inventory protocol).`);
      await fetchList();
      setTimeout(() => setActionNotice(null), 3500);
    } catch (err) {
      alert(`Failed to mark as purchased: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  // SEPARATE ACTION: Physical refill pouring into pantry container
  const handleRestockContainer = async (item: ShoppingItem) => {
    setRestockingId(item.id);
    try {
      await api.restockPantryFromShopping(item.item_id, item.suggested_quantity);
      setActionNotice(`Container #${item.item_id} (${item.item_name}) successfully restocked with +${item.suggested_quantity}${item.unit}!`);
      await fetchList();
      onRefresh();
      setTimeout(() => setActionNotice(null), 4000);
    } catch (err) {
      alert(`Failed to restock container: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setRestockingId(null);
    }
  };

  const filteredItems = items.filter((item) => {
    if (filter === 'all') return true;
    return item.status === filter;
  });

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case 'URGENT':
        return { bg: 'rgba(239, 68, 68, 0.15)', text: '#F87171', border: '#EF4444' };
      case 'HIGH':
        return { bg: 'rgba(245, 158, 11, 0.15)', text: '#FBBF24', border: '#F59E0B' };
      default:
        return { bg: 'rgba(56, 189, 248, 0.15)', text: '#38BDF8', border: '#38BDF8' };
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="glass-panel" style={{ padding: '20px 24px', borderRadius: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <h2 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <ShoppingCart size={22} color="var(--brand-primary)" />
              Smart Grocery Restock List
            </h2>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Automated reorder triggers derived from ML runout predictions and safety thresholds
            </p>
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              onClick={handleGenerate}
              disabled={isGenerating}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '9px 16px',
                borderRadius: '10px',
                background: 'var(--brand-primary)',
                border: 'none',
                color: '#FFF',
                fontSize: '13px',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              <Sparkles size={15} />
              {isGenerating ? 'Analyzing Stock...' : 'Auto-Generate Restock List'}
            </button>
            <button
              onClick={fetchList}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '9px 14px',
                borderRadius: '10px',
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

      {/* Protocol Banner */}
      {actionNotice && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            padding: '14px 18px',
            background: 'rgba(16, 185, 129, 0.15)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            borderRadius: '12px',
            color: '#34D399',
            fontSize: '13px',
            fontWeight: 600,
          }}
        >
          <CheckCircle2 size={18} />
          {actionNotice}
        </div>
      )}

      {/* Filter Tabs */}
      <div style={{ display: 'flex', gap: '8px' }}>
        {(['all', 'PENDING', 'PURCHASED'] as const).map((st) => (
          <button
            key={st}
            onClick={() => setFilter(st)}
            style={{
              padding: '8px 16px',
              borderRadius: '8px',
              fontSize: '13px',
              fontWeight: 600,
              cursor: 'pointer',
              border: '1px solid',
              borderColor: filter === st ? 'var(--brand-primary)' : 'var(--border-color)',
              background: filter === st ? 'rgba(79, 70, 229, 0.15)' : 'var(--bg-card)',
              color: filter === st ? 'var(--brand-primary-light)' : 'var(--text-secondary)',
              transition: 'all 0.2s ease',
            }}
          >
            {st === 'all' ? `All Items (${items.length})` : st === 'PENDING' ? `To Buy (${items.filter(i => i.status === 'PENDING').length})` : `Purchased (${items.filter(i => i.status === 'PURCHASED').length})`}
          </button>
        ))}
      </div>

      {/* Shopping List Table */}
      <div className="glass-panel" style={{ padding: '24px', borderRadius: '16px' }}>
        {loading ? (
          <div style={{ padding: '40px', textAlign: 'center' }}>
            <RefreshCw size={24} className="animate-spin" color="var(--brand-primary)" style={{ margin: '0 auto 12px' }} />
            <p style={{ color: 'var(--text-secondary)' }}>Loading shopping list items...</p>
          </div>
        ) : filteredItems.length === 0 ? (
          <div style={{ padding: '40px', textAlign: 'center' }}>
            <PackageCheck size={36} color="var(--text-muted)" style={{ margin: '0 auto 12px' }} />
            <h4 style={{ fontSize: '16px', color: 'var(--text-primary)', fontWeight: 600 }}>Pantry Stock is Healthy</h4>
            <p style={{ color: 'var(--text-muted)', fontSize: '13px', marginTop: '4px' }}>
              No items require restocking at this moment. Click "Auto-Generate Restock List" to force a replenishment check.
            </p>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-color)', textAlign: 'left', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '12px 14px' }}>Item & Reason</th>
                  <th style={{ padding: '12px 14px' }}>Priority</th>
                  <th style={{ padding: '12px 14px' }}>Current Stock</th>
                  <th style={{ padding: '12px 14px' }}>Suggested Order</th>
                  <th style={{ padding: '12px 14px' }}>Status</th>
                  <th style={{ padding: '12px 14px', textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredItems.map((item) => {
                  const pStyle = getPriorityBadge(item.priority);
                  const isPurchased = item.status === 'PURCHASED';

                  return (
                    <tr key={item.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                      <td style={{ padding: '14px' }}>
                        <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{item.item_name}</div>
                        <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>{item.reason}</div>
                      </td>
                      <td style={{ padding: '14px' }}>
                        <span
                          style={{
                            padding: '3px 8px',
                            borderRadius: '12px',
                            fontSize: '11px',
                            fontWeight: 700,
                            background: pStyle.bg,
                            color: pStyle.text,
                            border: `1px solid ${pStyle.border}`,
                          }}
                        >
                          {item.priority}
                        </span>
                      </td>
                      <td style={{ padding: '14px', color: 'var(--text-secondary)' }}>
                        {item.current_quantity} {item.unit}
                      </td>
                      <td style={{ padding: '14px', color: 'var(--brand-primary-light)', fontWeight: 700 }}>
                        {item.suggested_quantity} {item.unit}
                      </td>
                      <td style={{ padding: '14px' }}>
                        <span
                          style={{
                            padding: '3px 8px',
                            borderRadius: '12px',
                            fontSize: '11px',
                            fontWeight: 600,
                            background: isPurchased ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                            color: isPurchased ? '#34D399' : '#FBBF24',
                          }}
                        >
                          {item.status}
                        </span>
                      </td>
                      <td style={{ padding: '14px', textAlign: 'right' }}>
                        <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                          {!isPurchased ? (
                            <button
                              onClick={() => handleMarkPurchased(item)}
                              title="Mark as purchased in grocery list (does not change container weight)"
                              style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '5px',
                                padding: '6px 12px',
                                borderRadius: '8px',
                                background: 'rgba(56, 189, 248, 0.12)',
                                border: '1px solid rgba(56, 189, 248, 0.3)',
                                color: '#38BDF8',
                                fontSize: '12px',
                                fontWeight: 600,
                                cursor: 'pointer',
                              }}
                            >
                              <Check size={13} /> Mark Purchased
                            </button>
                          ) : (
                            <span style={{ fontSize: '12px', color: '#34D399', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}>
                              <CheckCircle2 size={14} /> Bought
                            </span>
                          )}

                          {/* Separate container restock button */}
                          <button
                            onClick={() => handleRestockContainer(item)}
                            disabled={restockingId === item.id}
                            title="Physical container refill action"
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: '5px',
                              padding: '6px 12px',
                              borderRadius: '8px',
                              background: 'rgba(16, 185, 129, 0.15)',
                              border: '1px solid rgba(16, 185, 129, 0.3)',
                              color: '#34D399',
                              fontSize: '12px',
                              fontWeight: 600,
                              cursor: 'pointer',
                            }}
                          >
                            <PlusCircle size={13} />
                            {restockingId === item.id ? 'Restocking...' : 'Restock Pantry'}
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
