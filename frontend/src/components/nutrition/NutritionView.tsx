import React, { useState } from 'react';
import type { DietSummary, HouseholdProfile } from '../../services/api';
import { api } from '../../services/api';
import {
  Flame,
  PlusCircle,
  Info,
  CheckCircle2,
  Award,
} from 'lucide-react';

interface NutritionViewProps {
  dietSummary: DietSummary | null;
  household: HouseholdProfile | null;
  onRefresh: () => void;
}

export const NutritionView: React.FC<NutritionViewProps> = ({
  dietSummary,
  household,
  onRefresh,
}) => {
  const [mealName, setMealName] = useState('');
  const [mealType, setMealType] = useState('Lunch');
  const [calories, setCalories] = useState<number>(450);
  const [carbs, setCarbs] = useState<number>(55);
  const [protein, setProtein] = useState<number>(18);
  const [fat, setFat] = useState<number>(14);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [logSuccess, setLogSuccess] = useState<string | null>(null);

  const handleLogMeal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!mealName.trim()) return;
    setIsSubmitting(true);
    try {
      await api.logMeal({
        meal_name: mealName,
        meal_type: mealType,
        calories: Number(calories),
        carbohydrates: Number(carbs),
        protein: Number(protein),
        fat: Number(fat),
        sugar: 2,
        sodium: 350,
        fiber: 0,
      });
      setLogSuccess(`Logged "${mealName}" successfully!`);
      setMealName('');
      setTimeout(() => {
        setLogSuccess(null);
        onRefresh();
      }, 1200);
    } catch (err) {
      alert(`Failed to log meal: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const pantry = dietSummary?.tracked_pantry_intake;
  const manual = dietSummary?.manual_logged_intake;
  const total = dietSummary?.total_combined_intake;

  const targetCalories = household?.daily_calorie_target || 8000;
  const currentTotalCalories = total?.calories_kcal || (pantry?.calories_kcal || 0) + (manual?.calories_kcal || 0);
  const caloriePct = Math.min(100, Math.round((currentTotalCalories / targetCalories) * 100));

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="glass-panel" style={{ padding: '20px 24px', borderRadius: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <h2 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Flame size={22} color="#FB923C" />
              Nutritional Intake & Dietary Intelligence
            </h2>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Multi-source dietary analysis: Tracked Pantry Staples + Manual Food Logs
            </p>
          </div>
          {household && (
            <div style={{ background: 'rgba(79, 70, 229, 0.12)', padding: '8px 16px', borderRadius: '10px', border: '1px solid rgba(79, 70, 229, 0.25)' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Household Target ({household.family_size} Members)</span>
              <p style={{ fontSize: '15px', fontWeight: 700, color: 'var(--brand-primary-light)', marginTop: '2px' }}>
                {targetCalories.toLocaleString()} kcal / day
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Honest Scientific Disclaimer */}
      <div
        style={{
          display: 'flex',
          alignItems: 'flex-start',
          gap: '12px',
          padding: '16px 20px',
          background: 'rgba(56, 189, 248, 0.08)',
          borderRadius: '12px',
          border: '1px solid rgba(56, 189, 248, 0.25)',
        }}
      >
        <Info size={20} color="#38BDF8" style={{ flexShrink: 0, marginTop: '2px' }} />
        <div style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
          <strong style={{ color: '#38BDF8' }}>Scientific Scope Note:</strong> Smart Pantry load cells measure intake from connected staples (Rice, Sugar, Salt, Ghee). Complete daily dietary totals require logging additional off-pantry meals (vegetables, proteins, beverages) using the form below.
        </div>
      </div>

      {/* Energy & Macro Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
        <div className="glass-panel" style={{ padding: '20px', borderRadius: '14px' }}>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Total Daily Energy</span>
          <p style={{ fontSize: '24px', fontWeight: 800, color: '#FB923C', marginTop: '4px' }}>
            {currentTotalCalories.toFixed(0)} <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>/ {targetCalories} kcal</span>
          </p>
          <div style={{ marginTop: '10px', width: '100%', height: '6px', background: 'rgba(255,255,255,0.06)', borderRadius: '3px', overflow: 'hidden' }}>
            <div style={{ width: `${caloriePct}%`, height: '100%', background: '#FB923C', borderRadius: '3px' }} />
          </div>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '6px', display: 'block' }}>
            {caloriePct}% of household target
          </span>
        </div>

        <div className="glass-panel" style={{ padding: '20px', borderRadius: '14px' }}>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Carbohydrates</span>
          <p style={{ fontSize: '24px', fontWeight: 800, color: '#38BDF8', marginTop: '4px' }}>
            {(total?.carbohydrates_g ?? 0).toFixed(0)} <span style={{ fontSize: '13px', fontWeight: 500 }}>g</span>
          </p>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '6px', display: 'block' }}>
            Pantry: {(pantry?.carbohydrates_g ?? 0).toFixed(0)}g • Logged: {(manual?.carbohydrates_g ?? 0).toFixed(0)}g
          </span>
        </div>

        <div className="glass-panel" style={{ padding: '20px', borderRadius: '14px' }}>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Protein</span>
          <p style={{ fontSize: '24px', fontWeight: 800, color: '#34D399', marginTop: '4px' }}>
            {(total?.protein_g ?? 0).toFixed(0)} <span style={{ fontSize: '13px', fontWeight: 500 }}>g</span>
          </p>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '6px', display: 'block' }}>
            Pantry: {(pantry?.protein_g ?? 0).toFixed(0)}g • Logged: {(manual?.protein_g ?? 0).toFixed(0)}g
          </span>
        </div>

        <div className="glass-panel" style={{ padding: '20px', borderRadius: '14px' }}>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Total Fats</span>
          <p style={{ fontSize: '24px', fontWeight: 800, color: '#FBBF24', marginTop: '4px' }}>
            {(total?.fat_g ?? 0).toFixed(0)} <span style={{ fontSize: '13px', fontWeight: 500 }}>g</span>
          </p>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '6px', display: 'block' }}>
            Pantry (Ghee): {(pantry?.fat_g ?? 0).toFixed(0)}g • Logged: {(manual?.fat_g ?? 0).toFixed(0)}g
          </span>
        </div>

        <div className="glass-panel" style={{ padding: '20px', borderRadius: '14px' }}>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Free Sugar Intake</span>
          <p style={{ fontSize: '24px', fontWeight: 800, color: '#F472B6', marginTop: '4px' }}>
            {(total?.sugar_g ?? 0).toFixed(0)} <span style={{ fontSize: '13px', fontWeight: 500 }}>g</span>
          </p>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '6px', display: 'block' }}>
            WHO Limit: &lt;50g/day per adult
          </span>
        </div>

        <div className="glass-panel" style={{ padding: '20px', borderRadius: '14px' }}>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Sodium Level</span>
          <p style={{ fontSize: '24px', fontWeight: 800, color: (total?.sodium_mg ?? 0) > 8000 ? '#F87171' : '#A78BFA', marginTop: '4px' }}>
            {(total?.sodium_mg ?? 0).toFixed(0)} <span style={{ fontSize: '13px', fontWeight: 500 }}>mg</span>
          </p>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '6px', display: 'block' }}>
            WHO Limit: &lt;2000mg/day per person
          </span>
        </div>
      </div>

      {/* Two Column Layout: Manual Meal Logger + Dietary Pattern Profile */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '20px' }}>
        {/* Form to log meals */}
        <div className="glass-panel" style={{ padding: '24px', borderRadius: '16px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <PlusCircle size={18} color="var(--brand-primary)" /> Log Outside / Cooked Meal
          </h3>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '18px' }}>
            Add non-pantry foods to maintain accurate 24-hour nutritional tracking.
          </p>

          {logSuccess && (
            <div style={{ padding: '12px', background: 'rgba(16, 185, 129, 0.15)', border: '1px solid rgba(16, 185, 129, 0.3)', borderRadius: '8px', color: '#34D399', fontSize: '13px', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <CheckCircle2 size={16} /> {logSuccess}
            </div>
          )}

          <form onSubmit={handleLogMeal} className="space-y-4">
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                Meal or Dish Name
              </label>
              <input
                type="text"
                placeholder="e.g. Mixed Veg Salad with Chickpeas"
                value={mealName}
                onChange={(e) => setMealName(e.target.value)}
                required
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
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                  Meal Type
                </label>
                <select
                  value={mealType}
                  onChange={(e) => setMealType(e.target.value)}
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
                  <option value="Breakfast">Breakfast</option>
                  <option value="Lunch">Lunch</option>
                  <option value="Dinner">Dinner</option>
                  <option value="Snack">Snack</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                  Calories (kcal)
                </label>
                <input
                  type="number"
                  value={calories}
                  onChange={(e) => setCalories(Number(e.target.value))}
                  min={0}
                  required
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
                />
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '10px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>
                  Carbs (g)
                </label>
                <input
                  type="number"
                  value={carbs}
                  onChange={(e) => setCarbs(Number(e.target.value))}
                  min={0}
                  style={{
                    width: '100%',
                    padding: '8px 10px',
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border-color)',
                    borderRadius: '8px',
                    color: 'var(--text-primary)',
                    fontSize: '13px',
                    outline: 'none',
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>
                  Protein (g)
                </label>
                <input
                  type="number"
                  value={protein}
                  onChange={(e) => setProtein(Number(e.target.value))}
                  min={0}
                  style={{
                    width: '100%',
                    padding: '8px 10px',
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border-color)',
                    borderRadius: '8px',
                    color: 'var(--text-primary)',
                    fontSize: '13px',
                    outline: 'none',
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>
                  Fat (g)
                </label>
                <input
                  type="number"
                  value={fat}
                  onChange={(e) => setFat(Number(e.target.value))}
                  min={0}
                  style={{
                    width: '100%',
                    padding: '8px 10px',
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border-color)',
                    borderRadius: '8px',
                    color: 'var(--text-primary)',
                    fontSize: '13px',
                    outline: 'none',
                  }}
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              style={{
                width: '100%',
                marginTop: '12px',
                padding: '11px 16px',
                background: 'var(--brand-primary)',
                border: 'none',
                borderRadius: '10px',
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
              {isSubmitting ? 'Recording Meal...' : 'Save Meal to Diary'}
            </button>
          </form>
        </div>

        {/* Dietary Pattern Profile */}
        <div className="glass-panel" style={{ padding: '24px', borderRadius: '16px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Award size={18} color="#34D399" /> Dietary Pattern Analysis
            </h3>
            <div style={{ background: 'var(--bg-card-subtle)', padding: '16px', borderRadius: '12px', marginBottom: '16px', border: '1px solid var(--border-color)' }}>
              <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Classified Dietary Pattern</span>
              <p style={{ fontSize: '18px', fontWeight: 800, color: 'var(--brand-primary-light)', marginTop: '4px' }}>
                {dietSummary?.dietary_pattern || 'Balanced Mixed Diet'}
              </p>
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '6px', lineHeight: '1.4' }}>
                {dietSummary?.dietary_pattern_description || 'Staple grain consumption with controlled lipids and low refined sugars.'}
              </p>
            </div>

            <div className="space-y-3" style={{ fontSize: '13px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Carbohydrate Energy Share</span>
                <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>
                  {total && total.calories_kcal > 0 ? `${Math.round(((total.carbohydrates_g * 4) / total.calories_kcal) * 100)}%` : '58%'}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Protein Energy Share</span>
                <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>
                  {total && total.calories_kcal > 0 ? `${Math.round(((total.protein_g * 4) / total.calories_kcal) * 100)}%` : '16%'}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <span style={{ color: 'var(--text-secondary)' }}>Fat Energy Share</span>
                <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>
                  {total && total.calories_kcal > 0 ? `${Math.round(((total.fat_g * 9) / total.calories_kcal) * 100)}%` : '26%'}
                </span>
              </div>
            </div>
          </div>

          <div style={{ marginTop: '16px', padding: '12px 14px', background: 'rgba(16, 185, 129, 0.08)', borderRadius: '10px', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
            <span style={{ fontSize: '12px', color: '#34D399', fontWeight: 600 }}>
              Macro Distribution Recommendation:
            </span>
            <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
              ICMR guidelines recommend 50-60% Carbohydrates, 10-15% Protein, and 20-30% Fats for an Indian household diet.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
