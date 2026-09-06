import React, { useState, useEffect } from 'react';
import type { RecipeRecommendations, Recipe, HouseholdProfile } from '../../services/api';
import { api } from '../../services/api';
import {
  ChefHat,
  Clock,
  Flame,
  Users,
  CheckCircle2,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Sparkles,
  RefreshCw,
  Search,
} from 'lucide-react';

interface RecipesViewProps {
  household: HouseholdProfile | null;
}

export const RecipesView: React.FC<RecipesViewProps> = ({ household }) => {
  const [recommendations, setRecommendations] = useState<RecipeRecommendations | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeCategory, setActiveCategory] = useState<'ready' | 'missing' | 'clearers' | 'healthy'>('ready');
  const [expandedRecipeId, setExpandedRecipeId] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const fetchRecipes = async () => {
    setLoading(true);
    try {
      const data = await api.getRecipeRecommendations();
      setRecommendations(data);
    } catch (err) {
      console.error('Failed to load recipe recommendations:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecipes();
  }, []);

  const getRecipesForCategory = (): Recipe[] => {
    if (!recommendations) return [];
    switch (activeCategory) {
      case 'ready':
        return recommendations.ready_to_cook || [];
      case 'missing':
        return recommendations.missing_ingredients || [];
      case 'clearers':
        return recommendations.pantry_clearers || [];
      case 'healthy':
        return recommendations.healthier_alternatives || [];
    }
  };

  const currentRecipes = getRecipesForCategory().filter((r) =>
    r.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    r.cuisine.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="glass-panel" style={{ padding: '20px 24px', borderRadius: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <h2 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <ChefHat size={22} color="var(--brand-primary)" />
              Smart Recipe Recommendations
            </h2>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Dynamically scaled to your household size ({household?.family_size || 4} Members) based on live pantry inventory
            </p>
          </div>

          <button
            onClick={fetchRecipes}
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
            <RefreshCw size={14} /> Refresh Recipes
          </button>
        </div>
      </div>

      {/* Categories Bar & Search */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {[
            { id: 'ready', label: 'Ready to Cook', count: recommendations?.ready_to_cook?.length ?? 0, icon: CheckCircle2 },
            { id: 'missing', label: 'Missing 1-2 Items', count: recommendations?.missing_ingredients?.length ?? 0, icon: AlertTriangle },
            { id: 'clearers', label: 'Pantry Clearers', count: recommendations?.pantry_clearers?.length ?? 0, icon: Sparkles },
            { id: 'healthy', label: 'Healthier Alternatives', count: recommendations?.healthier_alternatives?.length ?? 0, icon: Flame },
          ].map((cat) => {
            const Icon = cat.icon;
            const isActive = activeCategory === cat.id;
            return (
              <button
                key={cat.id}
                onClick={() => setActiveCategory(cat.id as any)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '9px 16px',
                  borderRadius: '10px',
                  fontSize: '13px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  border: '1px solid',
                  borderColor: isActive ? 'var(--brand-primary)' : 'var(--border-color)',
                  background: isActive ? 'rgba(79, 70, 229, 0.15)' : 'var(--bg-card)',
                  color: isActive ? 'var(--brand-primary-light)' : 'var(--text-secondary)',
                  transition: 'all 0.2s ease',
                }}
              >
                <Icon size={15} />
                {cat.label} ({cat.count})
              </button>
            );
          })}
        </div>

        <div style={{ position: 'relative', minWidth: '220px' }}>
          <Search size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
          <input
            type="text"
            placeholder="Search recipes..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              width: '100%',
              padding: '8px 12px 8px 36px',
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

      {/* Recipes Cards Grid */}
      {loading ? (
        <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', borderRadius: '16px' }}>
          <RefreshCw size={24} className="animate-spin" color="var(--brand-primary)" style={{ margin: '0 auto 12px' }} />
          <p style={{ color: 'var(--text-secondary)' }}>Matching live container stock against recipe database...</p>
        </div>
      ) : currentRecipes.length === 0 ? (
        <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', borderRadius: '16px' }}>
          <p style={{ color: 'var(--text-muted)' }}>No recipes found matching this category or filter.</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: '20px' }}>
          {currentRecipes.map((recipe) => {
            const isExpanded = expandedRecipeId === recipe.id;
            const inStockIngredients = recipe.ingredients.filter((i) => i.is_in_stock).length;
            const allInStock = inStockIngredients === recipe.ingredients.length;

            return (
              <div
                key={recipe.id}
                className="glass-panel"
                style={{
                  borderRadius: '16px',
                  padding: '24px',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  border: allInStock ? '1px solid rgba(16, 185, 129, 0.3)' : '1px solid var(--border-color)',
                  position: 'relative',
                }}
              >
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                    <div>
                      <span style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 600 }}>
                        {recipe.cuisine} Cuisine • {recipe.category}
                      </span>
                      <h3 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)', marginTop: '2px' }}>
                        {recipe.name}
                      </h3>
                    </div>
                    <span
                      style={{
                        padding: '3px 8px',
                        borderRadius: '12px',
                        fontSize: '11px',
                        fontWeight: 600,
                        background: allInStock ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                        color: allInStock ? '#34D399' : '#FBBF24',
                      }}
                    >
                      {inStockIngredients}/{recipe.ingredients.length} in pantry
                    </span>
                  </div>

                  <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '16px', lineHeight: '1.4' }}>
                    {recipe.description}
                  </p>

                  {/* Metadata pills */}
                  <div style={{ display: 'flex', gap: '12px', marginBottom: '16px', fontSize: '12px', color: 'var(--text-muted)' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Clock size={14} /> {recipe.prep_time_minutes + recipe.cook_time_minutes} mins
                    </span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Flame size={14} color="#FB923C" /> ~{recipe.estimated_calories_per_serving} kcal/srv
                    </span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Users size={14} /> {recipe.target_servings} Servings
                    </span>
                  </div>

                  {/* Scaled Ingredients List */}
                  <div style={{ background: 'var(--bg-card-subtle)', border: '1px solid var(--border-color)', padding: '14px', borderRadius: '12px', marginBottom: '14px' }}>
                    <span style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700, display: 'block', marginBottom: '8px' }}>
                      Scaled Ingredients for {recipe.target_servings} People:
                    </span>
                    <div className="space-y-1">
                      {recipe.ingredients.map((ing, idx) => (
                        <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px' }}>
                          <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: ing.is_in_stock ? 'var(--text-primary)' : 'var(--text-muted)' }}>
                            {ing.is_in_stock ? (
                              <CheckCircle2 size={13} color="#34D399" />
                            ) : (
                              <AlertTriangle size={13} color="#F59E0B" />
                            )}
                            {ing.item_name}
                          </span>
                          <span style={{ fontWeight: 600, color: ing.is_in_stock ? 'var(--brand-primary-light)' : '#F59E0B' }}>
                            {ing.scaled_quantity} {ing.unit}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Instructions Accordion */}
                  {isExpanded && (
                    <div style={{ marginTop: '12px', padding: '14px', background: 'rgba(79, 70, 229, 0.08)', borderRadius: '10px', fontSize: '12px', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
                      <strong style={{ color: 'var(--text-primary)', display: 'block', marginBottom: '6px' }}>Cooking Instructions:</strong>
                      {recipe.instructions}
                    </div>
                  )}
                </div>

                <button
                  onClick={() => setExpandedRecipeId(isExpanded ? null : recipe.id)}
                  style={{
                    width: '100%',
                    marginTop: '12px',
                    padding: '8px 12px',
                    borderRadius: '8px',
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border-color)',
                    color: 'var(--text-secondary)',
                    fontSize: '12px',
                    fontWeight: 600,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '6px',
                  }}
                >
                  {isExpanded ? (
                    <>
                      Hide Instructions <ChevronUp size={14} />
                    </>
                  ) : (
                    <>
                      View Step-by-Step Instructions <ChevronDown size={14} />
                    </>
                  )}
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
