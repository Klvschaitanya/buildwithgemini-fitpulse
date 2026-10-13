#!/usr/bin/env python3
"""Seed initial exercises and meal plans into Firestore."""

from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-03-ec7c06914539"

EXERCISES = [
    {
        "id": "barbell-squat",
        "name": "Barbell Back Squat",
        "category": "strength",
        "target_muscles": ["quadriceps", "glutes", "core"],
        "difficulty": "intermediate",
        "default_sets": 4,
        "default_reps": "8-10",
        "instructions": "Place barbell across upper traps, brace core, squat down until hips break parallel, drive back up.",
    },
    {
        "id": "push-ups",
        "name": "Push-Ups",
        "category": "bodyweight",
        "target_muscles": ["chest", "triceps", "anterior deltoids", "core"],
        "difficulty": "beginner",
        "default_sets": 3,
        "default_reps": "12-15",
        "instructions": "Keep hands shoulder-width apart, maintain a straight neutral spine, lower chest to floor and push up.",
    },
    {
        "id": "romanian-deadlift",
        "name": "Romanian Deadlift (RDL)",
        "category": "strength",
        "target_muscles": ["hamstrings", "glutes", "lower back"],
        "difficulty": "intermediate",
        "default_sets": 3,
        "default_reps": "10-12",
        "instructions": "Hinge at the hips keeping a soft knee bend, lower weight down the shins until hamstrings stretch, return to lockout.",
    },
    {
        "id": "hiit-sprints",
        "name": "HIIT Treadmill Sprints",
        "category": "cardio",
        "target_muscles": ["calves", "quadriceps", "cardiovascular"],
        "difficulty": "advanced",
        "default_sets": 8,
        "default_reps": "30s sprint / 60s walk",
        "instructions": "Warm up for 5 mins. Alternate 30 seconds max-effort sprint with 60 seconds walking recovery for 8 intervals.",
    },
]

MEALS = [
    {
        "id": "grilled-chicken-quinoa-bowl",
        "name": "Grilled Chicken & Quinoa Power Bowl",
        "meal_type": "lunch",
        "calories": 520,
        "protein_g": 45,
        "carbs_g": 48,
        "fats_g": 14,
        "tags": ["high-protein", "gluten-free", "meal-prep"],
        "prep_time_minutes": 25,
        "ingredients": ["6 oz grilled chicken breast", "1 cup cooked quinoa", "1 cup steamed broccoli", "1 tbsp olive oil", "lemon & herbs"],
    },
    {
        "id": "overnight-protein-oats",
        "name": "Berry Chia Overnight Protein Oats",
        "meal_type": "breakfast",
        "calories": 410,
        "protein_g": 32,
        "carbs_g": 52,
        "fats_g": 9,
        "tags": ["vegetarian", "high-protein", "quick"],
        "prep_time_minutes": 5,
        "ingredients": ["1/2 cup rolled oats", "1 scoop whey or plant protein", "3/4 cup almond milk", "1 tbsp chia seeds", "1/2 cup blueberries"],
    },
    {
        "id": "salmon-sweet-potato-asparagus",
        "name": "Pan-Seared Salmon with Roasted Sweet Potato",
        "meal_type": "dinner",
        "calories": 580,
        "protein_g": 42,
        "carbs_g": 40,
        "fats_g": 22,
        "tags": ["omega-3", "gluten-free", "nutrient-dense"],
        "prep_time_minutes": 30,
        "ingredients": ["6 oz wild salmon fillet", "1 medium sweet potato cubed", "1 cup asparagus spears", "1 tbsp olive oil", "garlic seasoning"],
    },
]


def seed():
    print(f"Connecting to Firestore for project: {PROJECT_ID}")
    db = firestore.Client(project=PROJECT_ID)

    print("Seeding exercises...")
    for ex in EXERCISES:
        doc_id = ex["id"]
        db.collection("exercises").document(doc_id).set(ex)
        print(f"  ✓ Seeded exercise: {ex['name']} ({doc_id})")

    print("Seeding meals...")
    for meal in MEALS:
        doc_id = meal["id"]
        db.collection("meals").document(doc_id).set(meal)
        print(f"  ✓ Seeded meal: {meal['name']} ({doc_id})")

    print("Firestore seeding completed successfully!")


if __name__ == "__main__":
    seed()
