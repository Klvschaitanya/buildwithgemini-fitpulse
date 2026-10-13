# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Firestore backend tools for the FitPulse agent."""

import datetime
from typing import Any, Dict, List, Optional
from google.cloud import firestore

# Hardcoded project ID as string to prevent project number resolution issues on Agent Platform.
PROJECT_ID = "qwiklabs-gcp-03-ec7c06914539"

_db_client: Optional[firestore.Client] = None


def get_db() -> firestore.Client:
    """Get or initialize the Firestore client singleton."""
    global _db_client
    if _db_client is None:
        _db_client = firestore.Client(project=PROJECT_ID)
    return _db_client


def search_exercises(query: str = "", category: str = "", muscle: str = "") -> List[Dict[str, Any]]:
    """Search or list exercises from the exercise library.

    Args:
        query: Optional keyword to match against exercise names or instructions (e.g. 'squat', 'push').
        category: Optional category filter (e.g. 'strength', 'cardio', 'bodyweight').
        muscle: Optional target muscle filter (e.g. 'quadriceps', 'chest', 'core', 'hamstrings').

    Returns:
        A list of matching exercise dictionaries.
    """
    db = get_db()
    docs = db.collection("exercises").stream()
    results = []

    q_lower = query.lower().strip()
    cat_lower = category.lower().strip()
    muscle_lower = muscle.lower().strip()

    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id

        if cat_lower and data.get("category", "").lower() != cat_lower:
            continue

        if muscle_lower:
            muscles = [m.lower() for m in data.get("target_muscles", [])]
            if not any(muscle_lower in m for m in muscles):
                continue

        if q_lower:
            name_match = q_lower in data.get("name", "").lower()
            instr_match = q_lower in data.get("instructions", "").lower()
            if not (name_match or instr_match):
                continue

        results.append(data)

    return results


def search_meals(query: str = "", meal_type: str = "", tag: str = "", max_calories: Optional[int] = None) -> List[Dict[str, Any]]:
    """Search or list meals from the meal catalog.

    Args:
        query: Optional keyword to match against meal names or ingredients (e.g. 'salmon', 'chicken', 'oats').
        meal_type: Optional meal type (e.g. 'breakfast', 'lunch', 'dinner', 'snack').
        tag: Optional dietary tag (e.g. 'high-protein', 'gluten-free', 'vegetarian').
        max_calories: Optional maximum calories filter.

    Returns:
        A list of matching meal dictionaries.
    """
    db = get_db()
    docs = db.collection("meals").stream()
    results = []

    q_lower = query.lower().strip()
    type_lower = meal_type.lower().strip()
    tag_lower = tag.lower().strip()

    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id

        if type_lower and data.get("meal_type", "").lower() != type_lower:
            continue

        if tag_lower:
            tags = [t.lower() for t in data.get("tags", [])]
            if not any(tag_lower in t for t in tags):
                continue

        if max_calories is not None and data.get("calories", 0) > max_calories:
            continue

        if q_lower:
            name_match = q_lower in data.get("name", "").lower()
            ingredients = [i.lower() for i in data.get("ingredients", [])]
            ing_match = any(q_lower in i for i in ingredients)
            if not (name_match or ing_match):
                continue

        results.append(data)

    return results


def log_workout(exercise_name: str, sets: int, reps_or_duration: str, notes: str = "") -> Dict[str, Any]:
    """Log a completed workout activity to the user's workout log in Firestore.

    Args:
        exercise_name: Name of the exercise performed (e.g. 'Barbell Back Squat').
        sets: Number of sets completed.
        reps_or_duration: Repetitions or duration per set (e.g. '10 reps', '45 seconds').
        notes: Optional user notes or perceived difficulty.

    Returns:
        A dictionary confirming the logged workout and its entry ID.
    """
    db = get_db()
    now = datetime.datetime.now(datetime.timezone.utc)
    entry = {
        "exercise_name": exercise_name,
        "sets": sets,
        "reps_or_duration": reps_or_duration,
        "notes": notes,
        "timestamp": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
    }
    doc_ref = db.collection("workout_logs").document()
    doc_ref.set(entry)
    entry["id"] = doc_ref.id
    return {"status": "success", "message": f"Logged workout for {exercise_name}", "entry": entry}


def get_recent_workout_logs(limit: int = 5) -> List[Dict[str, Any]]:
    """Retrieve recently logged workouts from Firestore.

    Args:
        limit: Maximum number of recent workout entries to return (default: 5).

    Returns:
        A list of recent workout log entries.
    """
    db = get_db()
    docs = (
        db.collection("workout_logs")
        .order_by("timestamp", direction=firestore.Query.DESCENDING)
        .limit(limit)
        .stream()
    )
    logs = []
    for doc in docs:
        d = doc.to_dict()
        d["id"] = doc.id
        logs.append(d)
    return logs


def calculate_macros_and_tdee(
    weight_kg: float,
    height_cm: float,
    age: int,
    gender: str = "male",
    activity_level: str = "moderate",
    goal: str = "maintain",
) -> Dict[str, Any]:
    """Calculate Basal Metabolic Rate (BMR), Total Daily Energy Expenditure (TDEE), and target macronutrients.

    Args:
        weight_kg: Body weight in kilograms.
        height_cm: Height in centimeters.
        age: Age in years.
        gender: 'male' or 'female'.
        activity_level: 'sedentary' (desk job, little exercise), 'light' (1-3 days/wk), 'moderate' (3-5 days/wk), or 'active' (6-7 days/wk).
        goal: 'cut' (fat loss, -500 kcal), 'maintain' (maintenance), or 'bulk' (muscle gain, +350 kcal).

    Returns:
        A dictionary with BMR, TDEE, target daily calories, and recommended macro split (protein, carbs, fat in grams).
    """
    # Mifflin-St Jeor formula
    if gender.lower().startswith("f"):
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161
    else:
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5

    activity_multipliers = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
    }
    multiplier = activity_multipliers.get(activity_level.lower(), 1.55)
    tdee = round(bmr * multiplier)

    goal_adjustments = {
        "cut": -500,
        "maintain": 0,
        "bulk": 350,
    }
    calorie_target = max(1200, tdee + goal_adjustments.get(goal.lower(), 0))

    # Recommended macros: ~2.0g protein/kg, ~0.9g fat/kg, remainder in carbs
    protein_g = round(weight_kg * 2.0)
    fat_g = round(weight_kg * 0.9)
    protein_cals = protein_g * 4
    fat_cals = fat_g * 9
    carb_cals = max(0, calorie_target - (protein_cals + fat_cals))
    carb_g = round(carb_cals / 4)

    return {
        "bmr_kcal": round(bmr),
        "tdee_kcal": tdee,
        "target_calories_kcal": calorie_target,
        "goal": goal.lower(),
        "activity_level": activity_level.lower(),
        "macros": {
            "protein_g": protein_g,
            "carbs_g": carb_g,
            "fats_g": fat_g,
        },
    }


def search_usda_foods(query: str, page_size: int = 3) -> List[Dict[str, Any]]:
    """Search the USDA FoodData Central database for real-world foods and their nutritional facts.

    Args:
        query: Food search term (e.g., 'greek yogurt', 'chicken breast', 'rolled oats', 'almonds').
        page_size: Number of food items to retrieve (default: 3, max: 10).

    Returns:
        A list of matching foods with calorie and macronutrient details.
    """
    import os
    import urllib.request
    import urllib.parse
    import json

    # Read API key from environment, fallback to USDA's public DEMO_KEY
    api_key = os.environ.get("USDA_API_KEY", "DEMO_KEY")
    encoded_query = urllib.parse.quote(query)
    url = f"https://api.nal.usda.gov/fdc/v1/foods/search?query={encoded_query}&pageSize={min(page_size, 10)}&api_key={api_key}"

    req = urllib.request.Request(url, headers={"User-Agent": "FitPulse/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return [{"error": f"Failed to fetch food data from USDA: {str(e)}"}]

    results = []
    for food in data.get("foods", []):
        nutrients = {}
        for n in food.get("foodNutrients", []):
            name = n.get("nutrientName", "")
            val = n.get("value", 0)
            unit = n.get("unitName", "")
            if name in ["Energy", "Protein", "Total lipid (fat)", "Carbohydrate, by difference", "Fiber, total dietary"]:
                nutrients[name] = f"{val} {unit}"

        results.append({
            "description": food.get("description"),
            "brand": food.get("brandOwner") or food.get("brandName") or "Generic",
            "category": food.get("foodCategory", ""),
            "nutrients": nutrients,
        })

    return results


def geocode_address(address: str) -> Dict[str, Any]:
    """Convert an address or location name into geographic coordinates (latitude and longitude) using the Geocoding API.

    Args:
        address: Street address, city, or landmark (e.g. '1600 Amphitheatre Pkwy, Mountain View, CA' or 'Central Park, NY').

    Returns:
        A dictionary containing formatted address, latitude, longitude, and place_id.
    """
    import os
    import urllib.request
    import urllib.parse
    import json

    api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "")
    if not api_key or api_key == "PASTE_KEY_HERE":
        return {"error": "GOOGLE_MAPS_API_KEY is not configured in environment"}

    encoded_address = urllib.parse.quote(address)
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_address}&key={api_key}"

    req = urllib.request.Request(url, headers={"User-Agent": "FitPulse/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": f"Geocoding request failed: {str(e)}"}

    if data.get("status") != "OK" or not data.get("results"):
        return {"status": data.get("status"), "error": data.get("error_message", "No results found for given address")}

    result = data["results"][0]
    loc = result.get("geometry", {}).get("location", {})
    return {
        "status": "OK",
        "formatted_address": result.get("formatted_address"),
        "latitude": loc.get("lat"),
        "longitude": loc.get("lng"),
        "place_id": result.get("place_id"),
    }


def find_nearby_places(
    latitude: float,
    longitude: float,
    place_type: str = "gym",
    radius_meters: float = 2000.0,
    max_results: int = 5,
) -> List[Dict[str, Any]]:
    """Search for nearby places of a specific type using the Google Places API (New) searchNearby endpoint.

    Args:
        latitude: Latitude coordinate of the search center.
        longitude: Longitude coordinate of the search center.
        place_type: Type of place to search (e.g. 'gym', 'fitness_center', 'supermarket', 'park', 'restaurant').
        radius_meters: Search radius in meters (default: 2000.0, max: 50000.0).
        max_results: Maximum number of places to return (default: 5, max: 20).

    Returns:
        A list of matching places with name, formatted address, coordinates, and types.
    """
    import os
    import urllib.request
    import json

    api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "")
    if not api_key or api_key == "PASTE_KEY_HERE":
        return [{"error": "GOOGLE_MAPS_API_KEY is not configured in environment"}]

    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location,places.types,places.rating",
        "User-Agent": "FitPulse/1.0",
    }

    payload = {
        "includedTypes": [place_type],
        "maxResultCount": min(max(1, max_results), 20),
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": latitude,
                    "longitude": longitude,
                },
                "radius": float(min(radius_meters, 50000.0)),
            }
        },
    }

    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return [{"error": f"Places searchNearby request failed: {str(e)}"}]

    places = []
    for p in data.get("places", []):
        display_name = p.get("displayName", {}).get("text", "")
        formatted_address = p.get("formattedAddress", "")
        location = p.get("location", {})
        places.append({
            "name": display_name,
            "address": formatted_address,
            "location": {
                "latitude": location.get("latitude"),
                "longitude": location.get("longitude"),
            },
            "rating": p.get("rating"),
            "types": p.get("types", []),
        })

    return places


def generate_fitness_visual(prompt: str, tool_context=None) -> Dict[str, Any]:
    """Generate an illustration, recipe visual, or exercise diagram using Gemini image generation, save as an artifact, and upload to public Cloud Storage.

    Args:
        prompt: Description of the visual to generate (e.g. 'A bowl of high protein berry oats with chia seeds' or 'Proper barbell squat technique illustration').
        tool_context: Optional ADK ToolContext to save artifacts in Playground.

    Returns:
        A dictionary containing the public Cloud Storage URL and status.
    """
    import os
    import uuid
    from google.genai import Client
    from google.genai import types
    from google.cloud import storage

    bucket_name = "fitpulse-assets-qwiklabs-gcp-03-ec7c06914539"
    project_id = "qwiklabs-gcp-03-ec7c06914539"

    # 1. Generate image using gemini-3.1-flash-lite-image in global region
    genai_client = Client(vertexai=True, project=project_id, location="global")
    response = genai_client.models.generate_content(
        model="gemini-3.1-flash-lite-image",
        contents=f"Generate a clear, appealing visual for: {prompt}",
    )

    image_bytes = None
    mime_type = "image/jpeg"
    if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.data:
                image_bytes = part.inline_data.data
                if part.inline_data.mime_type:
                    mime_type = part.inline_data.mime_type
                break

    if not image_bytes:
        return {"error": "Failed to generate image bytes from model response"}

    ext = "png" if "png" in mime_type else "jpg"
    filename = f"visual_{uuid.uuid4().hex[:8]}.{ext}"

    # 2. Save artifact to Playground if tool_context is provided
    if tool_context and hasattr(tool_context, "save_artifact"):
        try:
            artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
            tool_context.save_artifact(filename, artifact_part)
        except Exception as e:
            # Continue even if playground artifact saving has an issue
            pass

    # 3. Upload bytes to public Cloud Storage bucket
    storage_client = storage.Client(project=project_id)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(filename)
    blob.upload_from_string(image_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{bucket_name}/{filename}"
    return {
        "status": "success",
        "public_url": public_url,
        "filename": filename,
        "mime_type": mime_type,
    }



