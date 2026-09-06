import React, { useState, useEffect } from 'react';
import type { HouseholdProfile } from '../../services/api';
import { api } from '../../services/api';
import {
  Users,
  CheckCircle2,
  Flame,
  Save,
} from 'lucide-react';

interface HouseholdViewProps {
  household: HouseholdProfile | null;
  onRefresh: () => void;
}

export const HouseholdView: React.FC<HouseholdViewProps> = ({ household, onRefresh }) => {
  const [name, setName] = useState(household?.household_name || 'Sharma Residence');
  const [adults, setAdults] = useState<number>(household?.adults_count ?? household?.adults ?? 2);
  const [children, setChildren] = useState<number>(household?.children_count ?? household?.children ?? 1);
  const [elderly, setElderly] = useState<number>(household?.elderly_count ?? household?.elderly ?? 1);
  const [goal, setGoal] = useState<string>(household?.dietary_goal || 'Cardiovascular & Balanced Health');
  const [preferences, setPreferences] = useState<string[]>(household?.dietary_preferences || ['Vegetarian', 'Diabetic-Friendly']);
  const [saving, setSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Sync state if household prop updates
  useEffect(() => {
    if (household) {
      setName(household.household_name);
      setAdults(household.adults_count ?? household.adults ?? 2);
      setChildren(household.children_count ?? household.children ?? 1);
      setElderly(household.elderly_count ?? household.elderly ?? 1);
      setGoal(household.dietary_goal || '');
      setPreferences(household.dietary_preferences || []);
    }
  }, [household]);

  // Household invariant
  const totalFamilySize = adults + children + elderly;

  // Recommended calorie target: Adults=2200, Children=1600, Elderly=1900
  const recommendedCalories = adults * 2200 + children * 1600 + elderly * 1900;

  const handlePreferenceToggle = (pref: string) => {
    if (preferences.includes(pref)) {
      setPreferences(preferences.filter((p) => p !== pref));
    } else {
      setPreferences([...preferences, pref]);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.updateHousehold({
        household_name: name,
        family_size: totalFamilySize,
        adults_count: adults,
        children_count: children,
        elderly_count: elderly,
        dietary_preference: preferences[0] || 'BALANCED',
        activity_profile: 'MODERATE',
      });
      setSuccessMsg('Household profile and demographic baselines saved successfully!');
      onRefresh();
      setTimeout(() => setSuccessMsg(null), 3500);
    } catch (err) {
      alert(`Failed to update household: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="glass-panel" style={{ padding: '20px 24px', borderRadius: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <h2 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Users size={22} color="var(--brand-primary)" />
              Household Demographics & Configuration
            </h2>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Defines intake baselines, recipe scaling factors, and nutritional targets
            </p>
          </div>
        </div>
      </div>

      {successMsg && (
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
          {successMsg}
        </div>
      )}

      {/* Main Profile Form */}
      <form onSubmit={handleSave} className="space-y-6">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
          {/* Column 1: Demographics */}
          <div className="glass-panel" style={{ padding: '24px', borderRadius: '16px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Users size={18} color="var(--brand-primary)" /> Family Composition
            </h3>

            <div className="space-y-4">
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                  Household Name
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border-color)',
                    borderRadius: '8px',
                    color: 'var(--text-primary)',
                    fontSize: '13px',
                    outline: 'none',
                  }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>
                    Adults (18-59)
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={15}
                    value={adults}
                    onChange={(e) => setAdults(Math.max(1, Number(e.target.value)))}
                    style={{
                      width: '100%',
                      padding: '9px 10px',
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

                <div>
                  <label style={{ display: 'block', fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>
                    Children (0-17)
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={15}
                    value={children}
                    onChange={(e) => setChildren(Math.max(0, Number(e.target.value)))}
                    style={{
                      width: '100%',
                      padding: '9px 10px',
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

                <div>
                  <label style={{ display: 'block', fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>
                    Elderly (60+)
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={15}
                    value={elderly}
                    onChange={(e) => setElderly(Math.max(0, Number(e.target.value)))}
                    style={{
                      width: '100%',
                      padding: '9px 10px',
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
              </div>

              {/* Total Summary */}
              <div style={{ padding: '14px', background: 'var(--bg-card-subtle)', borderRadius: '10px', border: '1px solid var(--border-color)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Total Household Size:</span>
                  <span style={{ fontWeight: 800, color: 'var(--brand-primary-light)' }}>{totalFamilySize} Members</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginTop: '6px' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Formula Invariant:</span>
                  <span style={{ color: '#34D399', fontWeight: 600 }}>{adults}A + {children}C + {elderly}E = {totalFamilySize}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Column 2: Nutritional & Health Targets */}
          <div className="glass-panel" style={{ padding: '24px', borderRadius: '16px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Flame size={18} color="#FB923C" /> Dietary Objectives & Preferences
            </h3>

            <div className="space-y-4">
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                  Primary Health Goal
                </label>
                <select
                  value={goal}
                  onChange={(e) => setGoal(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border-color)',
                    borderRadius: '8px',
                    color: 'var(--text-primary)',
                    fontSize: '13px',
                    outline: 'none',
                  }}
                >
                  <option value="Cardiovascular & Balanced Health">Cardiovascular & Balanced Health</option>
                  <option value="Low Glycemic & Diabetic Control">Low Glycemic & Diabetic Control</option>
                  <option value="Active Weight Management">Active Weight Management</option>
                  <option value="High-Protein Strength Building">High-Protein Strength Building</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '8px' }}>
                  Dietary Preferences & Restrictions
                </label>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                  {['Vegetarian', 'Vegan', 'Diabetic-Friendly', 'Low Sodium', 'High Protein', 'Gluten-Free'].map((pref) => {
                    const isSelected = preferences.includes(pref);
                    return (
                      <button
                        type="button"
                        key={pref}
                        onClick={() => handlePreferenceToggle(pref)}
                        style={{
                          padding: '6px 12px',
                          borderRadius: '8px',
                          fontSize: '12px',
                          fontWeight: 600,
                          cursor: 'pointer',
                          border: '1px solid',
                          borderColor: isSelected ? 'var(--brand-primary)' : 'var(--border-color)',
                          background: isSelected ? 'rgba(79, 70, 229, 0.2)' : 'var(--bg-card)',
                          color: isSelected ? 'var(--brand-primary-light)' : 'var(--text-secondary)',
                          transition: 'all 0.15s ease',
                        }}
                      >
                        {pref}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Calorie Output Preview */}
              <div style={{ padding: '14px', background: 'rgba(251, 146, 60, 0.08)', borderRadius: '10px', border: '1px solid rgba(251, 146, 60, 0.2)' }}>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Auto-Calculated Recommended Calorie Baseline:</span>
                <p style={{ fontSize: '18px', fontWeight: 800, color: '#FB923C', marginTop: '2px' }}>
                  {recommendedCalories.toLocaleString()} kcal / day
                </p>
                <span style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '4px', display: 'block' }}>
                  Computed via ICMR recommendations for {adults} adults, {children} children, and {elderly} seniors.
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Action Save Button */}
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button
            type="submit"
            disabled={saving}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '12px 28px',
              borderRadius: '10px',
              background: 'var(--brand-primary)',
              border: 'none',
              color: '#FFF',
              fontSize: '14px',
              fontWeight: 700,
              cursor: 'pointer',
              boxShadow: '0 4px 14px rgba(79, 70, 229, 0.35)',
            }}
          >
            <Save size={16} />
            {saving ? 'Saving Demographics...' : 'Save Configuration'}
          </button>
        </div>
      </form>
    </div>
  );
};
