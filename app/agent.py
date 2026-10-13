# ruff: noqa
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

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from app.tools import (
    search_exercises,
    search_meals,
    log_workout,
    get_recent_workout_logs,
    calculate_macros_and_tdee,
    search_usda_foods,
    geocode_address,
    find_nearby_places,
    generate_fitness_visual,
)


MODEL = "gemini-3.8-flash"
AGENT_ENGINE_ID = "projects/1003227399589/locations/us-east1/reasoningEngines/5933260512107167744"

INSTRUCTION = """You are FitPulse, an expert fitness and nutrition coach.
You remember the user's stated fitness preferences, dietary restrictions, and personal goals across conversations.

You have access to a full suite of specialized tools:
- `generate_fitness_visual`: Generate an appealing meal presentation, recipe illustration, or exercise form diagram using Gemini image generation, save as an artifact, and upload to public Cloud Storage.
- `geocode_address`: Geocode an address, city, or landmark into latitude/longitude coordinates.
- `find_nearby_places`: Find nearby places of a specific type (e.g. 'gym', 'fitness_center', 'supermarket', 'park') using coordinates.
- `search_usda_foods`: Search real-world branded or raw foods from USDA FoodData Central for accurate nutritional breakdown (protein, carbs, fats, calories).
- `calculate_macros_and_tdee`: Calculate daily calorie targets, BMR, TDEE, and protein/carb/fat targets based on weight, height, age, activity level, and goal (cut, maintain, bulk).
- `search_exercises`: Search the exercise library by keyword, category (e.g. strength, cardio, bodyweight), or target muscle.
- `search_meals`: Search healthy recipes and meal plans by keyword, meal type (breakfast, lunch, dinner), dietary tag (e.g. high-protein, gluten-free), or calorie ceiling.
- `log_workout`: Log a completed exercise session with sets, reps/duration, and notes.
- `get_recent_workout_logs`: Retrieve the user's recent workout activity.

You can also run Python code safely in a sandbox using code execution to perform complex calculations, analysis, or data transformations.

Help users plan effective training sessions, locate nearby gyms, check real food nutrition facts, calculate targets, suggest recipes, and track their fitness progress accurately.
Always provide encouraging, concise, and actionable guidance.
"""


# WRITE: after each turn, send the session to Memory Bank for extraction.
async def generate_memories_callback(callback_context: CallbackContext):
    await callback_context.add_session_to_memory()
    return None


code_executor = AgentEngineSandboxCodeExecutor(
    agent_engine_resource_name=AGENT_ENGINE_ID
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=INSTRUCTION,
    code_executor=code_executor,
    tools=[
        PreloadMemoryTool(),
        calculate_macros_and_tdee,
        generate_fitness_visual,
        search_usda_foods,
        geocode_address,
        find_nearby_places,
        search_exercises,
        search_meals,
        log_workout,
        get_recent_workout_logs,
    ],
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)

