"""
Recipe database definitions and nutritional benchmarks.
"""

from typing import List, Dict, Any

STANDARD_RECIPES: List[Dict[str, Any]] = [
    {
        "name": "Classic Khichdi",
        "description": "Comforting one-pot wholesome dish of soft cooked rice enriched with golden ghee and balanced salt.",
        "category": "Main Course",
        "prep_time_minutes": 25,
        "base_servings": 4,
        "instructions": (
            "1. Rinse rice thoroughly until water runs clear.\n"
            "2. In a heavy pan, simmer rice with 3.5 parts water and salt on medium heat for 20 minutes.\n"
            "3. Once soft and porridge-like, fold in warm melted ghee and serve steaming hot."
        ),
        "estimated_calories_per_serving": 285.0,
        "tags": ["Comfort", "Quick", "Staple", "Hearty", "Easy Digest"],
        "dietary_attributes": ["Vegetarian", "Gluten-Free"],
        "ingredients": [
            {"item_name": "Rice", "quantity_per_serving": 60.0, "unit": "g", "is_pantry_item": True},
            {"item_name": "Ghee", "quantity_per_serving": 10.0, "unit": "g", "is_pantry_item": True},
            {"item_name": "Salt", "quantity_per_serving": 2.5, "unit": "g", "is_pantry_item": True},
        ],
    },
    {
        "name": "Cardamom Rice Kheer",
        "description": "Traditional sweet pudding made by gently simmering rice, sugar, and fragrant ghee.",
        "category": "Dessert",
        "prep_time_minutes": 35,
        "base_servings": 4,
        "instructions": (
            "1. Simmer rice in milk or hot water until grains break down.\n"
            "2. Stir in sugar until completely dissolved.\n"
            "3. Drizzle with warm ghee and crushed cardamom before serving chilled or warm."
        ),
        "estimated_calories_per_serving": 270.0,
        "tags": ["Sweet", "Festive", "Dessert", "Comfort"],
        "dietary_attributes": ["Vegetarian"],
        "ingredients": [
            {"item_name": "Rice", "quantity_per_serving": 40.0, "unit": "g", "is_pantry_item": True},
            {"item_name": "Sugar", "quantity_per_serving": 25.0, "unit": "g", "is_pantry_item": True},
            {"item_name": "Ghee", "quantity_per_serving": 5.0, "unit": "g", "is_pantry_item": True},
        ],
    },
    {
        "name": "Fragrant Ghee Rice",
        "description": "Fluffy long-grain rice delicately tempered with clarified butter (ghee) and sea salt.",
        "category": "Main Course",
        "prep_time_minutes": 20,
        "base_servings": 4,
        "instructions": (
            "1. Cook rice until individual grains are separate and fluffy.\n"
            "2. Melt ghee in a skillet with salt and gently toss warm rice until glossy."
        ),
        "estimated_calories_per_serving": 380.0,
        "tags": ["Aromatic", "Quick", "Comfort", "Dinner"],
        "dietary_attributes": ["Vegetarian", "Gluten-Free"],
        "ingredients": [
            {"item_name": "Rice", "quantity_per_serving": 70.0, "unit": "g", "is_pantry_item": True},
            {"item_name": "Ghee", "quantity_per_serving": 15.0, "unit": "g", "is_pantry_item": True},
            {"item_name": "Salt", "quantity_per_serving": 2.5, "unit": "g", "is_pantry_item": True},
        ],
    },
    {
        "name": "Salted Rice Porridge (Congee)",
        "description": "Gentle, easily digestible soothing rice soup seasoned with mineral salt.",
        "category": "Breakfast",
        "prep_time_minutes": 30,
        "base_servings": 2,
        "instructions": (
            "1. Simmer rice in 6 cups of water on low heat for 30 minutes until broken down into a silky soup.\n"
            "2. Stir in salt to taste and serve warm."
        ),
        "estimated_calories_per_serving": 185.0,
        "tags": ["Light", "Recovery", "Easy Digest", "Lower Fat"],
        "dietary_attributes": ["Vegan", "Low Fat", "Gluten-Free"],
        "ingredients": [
            {"item_name": "Rice", "quantity_per_serving": 50.0, "unit": "g", "is_pantry_item": True},
            {"item_name": "Salt", "quantity_per_serving": 2.0, "unit": "g", "is_pantry_item": True},
        ],
    },
    {
        "name": "Sweet Rice Halwa",
        "description": "Rich golden rice sweet caramelized with clarified butter and sugar.",
        "category": "Dessert",
        "prep_time_minutes": 25,
        "base_servings": 4,
        "instructions": (
            "1. Toast ground rice in melted ghee until nutty and golden brown.\n"
            "2. Slowly pour in hot sugar syrup and stir vigorously until smooth and glossy."
        ),
        "estimated_calories_per_serving": 360.0,
        "tags": ["Rich", "Traditional", "Sweet", "Dessert"],
        "dietary_attributes": ["Vegetarian"],
        "ingredients": [
            {"item_name": "Rice", "quantity_per_serving": 50.0, "unit": "g", "is_pantry_item": True},
            {"item_name": "Sugar", "quantity_per_serving": 30.0, "unit": "g", "is_pantry_item": True},
            {"item_name": "Ghee", "quantity_per_serving": 20.0, "unit": "g", "is_pantry_item": True},
        ],
    },
    {
        "name": "Low-Sodium Steamed Rice Bowl",
        "description": "Steamed white rice finished with a light touch of pure ghee without added sodium.",
        "category": "Healthy / Special",
        "prep_time_minutes": 20,
        "base_servings": 2,
        "instructions": (
            "1. Steam rice with fresh spring water until tender.\n"
            "2. Fold in a gentle drizzle of ghee for aroma without adding any salt."
        ),
        "estimated_calories_per_serving": 310.0,
        "tags": ["Lower Sodium", "Clean", "Heart Healthy"],
        "dietary_attributes": ["Vegetarian", "Lower Sodium", "Gluten-Free"],
        "ingredients": [
            {"item_name": "Rice", "quantity_per_serving": 75.0, "unit": "g", "is_pantry_item": True},
            {"item_name": "Ghee", "quantity_per_serving": 5.0, "unit": "g", "is_pantry_item": True},
        ],
    },
    {
        "name": "Sugar-Free Rice & Ghee Snack",
        "description": "Savory crunchy toasted rice snack tossed with a touch of ghee and fine salt.",
        "category": "Snack",
        "prep_time_minutes": 15,
        "base_servings": 2,
        "instructions": (
            "1. Warm ghee in a heavy skillet.\n"
            "2. Add cooked rice and salt; saute on high heat until crispy."
        ),
        "estimated_calories_per_serving": 270.0,
        "tags": ["Lower Sugar", "Quick", "Savory"],
        "dietary_attributes": ["Vegetarian", "Lower Sugar", "Gluten-Free"],
        "ingredients": [
            {"item_name": "Rice", "quantity_per_serving": 60.0, "unit": "g", "is_pantry_item": True},
            {"item_name": "Ghee", "quantity_per_serving": 8.0, "unit": "g", "is_pantry_item": True},
            {"item_name": "Salt", "quantity_per_serving": 1.5, "unit": "g", "is_pantry_item": True},
        ],
    },
    {
        "name": "Lemon Turmeric Rice",
        "description": "Bright golden rice infused with warming turmeric, melted ghee, and balanced salt.",
        "category": "Lunch",
        "prep_time_minutes": 20,
        "base_servings": 4,
        "instructions": (
            "1. Boil rice until firm.\n"
            "2. Heat ghee, add a pinch of turmeric and salt, and stir in warm rice."
        ),
        "estimated_calories_per_serving": 310.0,
        "tags": ["Tangy", "Colorful", "Quick", "Antioxidant"],
        "dietary_attributes": ["Vegetarian", "Gluten-Free"],
        "ingredients": [
            {"item_name": "Rice", "quantity_per_serving": 65.0, "unit": "g", "is_pantry_item": True},
            {"item_name": "Ghee", "quantity_per_serving": 10.0, "unit": "g", "is_pantry_item": True},
            {"item_name": "Salt", "quantity_per_serving": 2.5, "unit": "g", "is_pantry_item": True},
        ],
    },
]
