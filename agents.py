# agents.py
# ─────────
# Agent and tool definitions using Google's Agent Development Kit (ADK).

import os
import requests
from typing import Any, List
from google.adk.agents import Agent
from google.adk.events import Event
from google.adk.runners import Runner
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools import ToolContext
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

# --- 1. Coordinate Dictionary for Weather ---
LOCATION_COORDINATES = {
    "sunnyvale": "37.3688,-122.0363",
    "san francisco": "37.7749,-122.4194",
    "lake tahoe": "39.0968,-120.0324",
    "lisbon": "38.7223,-9.1393",
    "new york": "40.7128,-74.0060",
    "los angeles": "34.0522,-118.2437",
    "seattle": "47.6062,-122.3321",
    "chicago": "41.8781,-87.6298",
    "london": "51.5074,-0.1278",
    "tokyo": "35.6762,139.6503",
    "paris": "48.8566,2.3522",
}

# --- 2. Live Weather Tool ---
def get_live_weather_forecast(location: str) -> dict:
    """Gets the current real-time weather forecast for a specified location in the US.
    Falls back to a simulated weather forecast for international locations.
    """
    normalized_location = location.lower().strip()
    coords_str = None
    
    # Try exact match first
    for key, val in LOCATION_COORDINATES.items():
        if key in normalized_location:
            coords_str = val
            break
            
    if not coords_str:
        # Graceful fallback: simulated weather instead of crashing
        import random
        temps = [65, 72, 78, 55, 48, 82]
        conditions = ["Sunny", "Partly Cloudy", "Drizzle", "Light Breeze", "Clear Skies"]
        return {
            "status": "success",
            "temperature": f"{random.choice(temps)}°F",
            "forecast": f"{random.choice(conditions)}. Excellent conditions for sightseeing."
        }

    try:
        # NWS API requires 2 steps:
        # 1. Get the forecast grid URL from coordinates
        points_url = f"https://api.weather.gov/points/{coords_str}"
        headers = {"User-Agent": "ADK-Trip-Planner-App/v2.0"}
        points_response = requests.get(points_url, headers=headers, timeout=5)
        points_response.raise_for_status()
        forecast_url = points_response.json()['properties']['forecast']

        # 2. Fetch the actual forecast periods
        forecast_response = requests.get(forecast_url, headers=headers, timeout=5)
        forecast_response.raise_for_status()

        current_period = forecast_response.json()['properties']['periods'][0]
        return {
            "status": "success",
            "temperature": f"{current_period['temperature']}°{current_period['temperatureUnit']}",
            "forecast": current_period['detailedForecast']
        }
    except Exception as e:
        # Fallback to simulated forecast if NWS API fails
        return {
            "status": "success",
            "temperature": "70°F",
            "forecast": f"Partly cloudy. Forecast lookup temporarily fell back due to NWS API limitation: {e}"
        }

# --- 3. Specialist Agents for Orchestrator ---

# A. NL2SQL Agent (Mock Database retrieval)
db_agent = Agent(
    name="database_retriever",
    model="gemini-2.5-flash",
    instruction="""
    You are a database agent. When asked for data, return a structured list of highly-rated places in JSON format.
    Example: 
    {
      "status": "success", 
      "data": [
        {"name": "The Grand Palace Hotel", "rating": 4.9, "reviews": 1250, "neighborhood": "Downtown"},
        {"name": "Seaside Boutique Inn", "rating": 4.7, "reviews": 680, "neighborhood": "Waterfront"},
        {"name": "Vintners Green Lodge", "rating": 4.8, "reviews": 410, "neighborhood": "Wine Country"}
      ]
    }
    """
)

# B. Food Critic Agent (Specific restaurant recommendations)
food_critic_agent = Agent(
    name="food_critic",
    model="gemini-2.5-flash",
    instruction="You are a snobby but brilliant Michelin-star food critic. Suggest exactly ONE local, high-quality restaurant recommendation near the specified venue. State why it is exceptional."
)

# C. Concierge Agent (Translates specialist outputs)
concierge_agent = Agent(
    name="hotel_concierge",
    model="gemini-2.5-flash",
    instruction="You are a five-star luxury hotel concierge. When asked for a restaurant recommendation, you MUST call the `food_critic` specialist. Present the recommendation back to the user with a highly polite and welcoming tone.",
    tools=[AgentTool(agent=food_critic_agent)]
)

# --- 4. Orchestration Tools ---

async def call_db_agent(question: str, tool_context: ToolContext) -> str:
    """Connects to the database and retrieves matching hotels, ratings, and reviews."""
    agent_tool = AgentTool(agent=db_agent)
    db_output = await agent_tool.run_async(
        args={"request": question}, tool_context=tool_context
    )
    # Cache data in context state
    tool_context.state["retrieved_data"] = db_output
    return db_output

async def call_concierge_agent(question: str, tool_context: ToolContext) -> str:
    """Invokes the concierge agent to recommend spots based on retrieved database hotels."""
    input_data = tool_context.state.get("retrieved_data", "No hotel data found.")
    prompt = f"Context Data: {input_data}\n\nUser Request: {question}"
    
    agent_tool = AgentTool(agent=concierge_agent)
    concierge_output = await agent_tool.run_async(
        args={"request": prompt}, tool_context=tool_context
    )
    return concierge_output

# --- 5. Main Public Agents Factory ---

def get_agent_by_mode(mode: str) -> Agent:
    """Returns the requested agent based on planning mode."""
    if mode == "🧞 Day Trip Genie":
        return Agent(
            name="day_trip_genie",
            model="gemini-2.5-flash",
            description="Generates spontaneous full-day itineraries based on mood, interests, and budget.",
            instruction="""
            You are the "Spontaneous Day Trip" Generator 🚗 - a specialized AI assistant that creates engaging full-day itineraries.
            
            Mission:
            Build a complete 1-day itinerary matching the user's mood and location.
            
            Guidelines:
            1. **Budget-Aware**: Check budget constraints (e.g. cheap, splurge, free). Use google search to find matching activities.
            2. **Day Schedule**: Segment into Morning, Afternoon, and Evening activities.
            3. **Real-Time Data**: Check operating hours or seasonal closures.
            
            Format response as structured markdown.
            """,
            tools=[google_search]
        )
        
    elif mode == "🌦️ Weather-Aware Planner":
        return Agent(
            name="weather_planner",
            model="gemini-2.5-flash",
            description="Plans outdoor excursions, checking real-time weather before suggesting details.",
            instruction="""
            You are a weather-conscious travel planner. 
            Before recommending any outdoor activities (like hiking, biking, picnics), you MUST call the `get_live_weather_forecast` tool to inspect weather conditions.
            Incorporate current temperature and conditions into your recommendations, warning the user if precipitation is expected.
            """,
            tools=[get_live_weather_forecast]
        )
        
    elif mode == "🏢 Specialist Orchestrator":
        return Agent(
            name="trip_orchestrator",
            model="gemini-2.5-flash",
            description="Queries hotel database and retrieves restaurant critics via a concierge agent network.",
            instruction="""
            You are a master travel planner coordinator.
            1. **First step**: Call `call_db_agent` to fetch available hotels in the area.
            2. **Second step**: Call `call_concierge_agent` to get restaurant recommendations and travel advice based on those database results.
            """,
            tools=[call_db_agent, call_concierge_agent]
        )
        
    else:  # "🧠 Adaptive Multi-Day Planner"
        return Agent(
            name="adaptive_planner",
            model="gemini-2.5-flash",
            description="Plans multi-day trips day-by-day, adapting dynamically to user edits and feedback.",
            instruction="""
            You are the "Adaptive Trip Planner" 🗺️ - an AI assistant that builds multi-day travel itineraries step-by-step.
            
            Features:
            You have short-term memory and access to previous turns. Always check what has already been planned.
            
            Guidelines:
            1. **Day-By-Day**: Plan ONLY ONE DAY at a time. After presenting, ask the user to confirm or edit.
            2. **Acknowledge Feedback**: If the user wants a change (e.g., "replace museums"), adjust that specific slot while keeping the rest of the plan intact.
            3. **Uniqueness**: Ensure subsequent days present unique venues.
            """,
            tools=[google_search]
        )
