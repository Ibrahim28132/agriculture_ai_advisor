import os
import json
import requests
from typing import TypedDict, Annotated, Sequence
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

load_dotenv()

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], lambda x, y: x + y]
    user_language: str

class WeatherQuery(BaseModel):
    location: str = Field(description="The city and country for weather query")
    days: str = Field(description="Number of days for forecast")

class SoilQuery(BaseModel):
    location: str = Field(description="The location for soil information")
    crop_type: str = Field(description="Type of crop for soil analysis")

@tool(args_schema=WeatherQuery)
def get_weather_forecast(location: str, days: str = "7") -> str:
    """Get weather forecast for agricultural planning"""
    try:
        api_key = os.getenv('OPENWEATHER_API_KEY')
        if not api_key:
            return "OpenWeather API key not configured"
            
        url = "http://api.openweathermap.org/data/2.5/forecast"
        params = {
            'q': location,
            'appid': api_key,
            'units': 'metric',
            'lang': 'en'
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if response.status_code == 200:
            forecasts = []
            for item in data['list'][:int(days)*3]:  # 3 forecasts per day
                forecast = {
                    'date': item['dt_txt'],
                    'temp': item['main']['temp'],
                    'humidity': item['main']['humidity'],
                    'description': item['weather'][0]['description'],
                    'rain': item.get('rain', {}).get('3h', 0),
                    'wind_speed': item['wind']['speed']
                }
                forecasts.append(forecast)
            
            # Summarize the forecast
            summary = {
                'location': location,
                'forecast_days': days,
                'average_temp': sum(f['temp'] for f in forecasts) / len(forecasts),
                'total_rainfall': sum(f['rain'] for f in forecasts),
                'details': forecasts[:5]  # First 5 forecasts
            }
            
            return json.dumps(summary, indent=2)
        else:
            return f"Weather API error: {data.get('message', 'Unknown error')}"
            
    except Exception as e:
        return f"Error fetching weather data: {str(e)}"

@tool(args_schema=SoilQuery)
def get_soil_info(location: str, crop_type: str) -> str:
    """Get soil information and recommendations for specific crops"""
    try:
        # Mock soil data - in production, integrate with soil APIs
        soil_data = {
            "clay": {
                "drainage": "poor", 
                "nutrients": "high", 
                "workability": "hard",
                "recommendations": "Add sand and organic matter to improve drainage"
            },
            "sandy": {
                "drainage": "excellent", 
                "nutrients": "low", 
                "workability": "easy",
                "recommendations": "Add clay and organic matter to improve water retention"
            },
            "loamy": {
                "drainage": "good", 
                "nutrients": "medium", 
                "workability": "good",
                "recommendations": "Ideal soil type, maintain with regular organic matter"
            }
        }
        
        # Simple soil type based on location (mock)
        soil_type = "loamy"
        location_lower = location.lower()
        if any(word in location_lower for word in ['arid', 'desert', 'dry']):
            soil_type = "sandy"
        elif any(word in location_lower for word in ['coastal', 'river', 'delta']):
            soil_type = "clay"
        
        soil_info = soil_data.get(soil_type, soil_data["loamy"])
        
        recommendations = {
            "vegetables": "Well-drained soil with organic matter, pH 6.0-7.0",
            "grains": "Deep, fertile soil with good drainage, pH 6.0-7.5",
            "fruits": "Rich, well-drained soil with pH 6.0-7.0, good organic content",
            "legumes": "Moderately fertile soil with good drainage, pH 6.0-7.5",
            "rice": "Clay-rich soil that retains water, pH 5.0-6.5",
            "wheat": "Well-drained loamy soil, pH 6.0-7.5",
            "tomato": "Well-drained sandy loam, rich in organic matter, pH 6.0-6.8"
        }
        
        return json.dumps({
            "location": location,
            "soil_type": soil_type,
            "characteristics": soil_info,
            "crop_recommendations": recommendations.get(crop_type.lower() if crop_type else "general", "General agricultural soil preparation recommended"),
            "fertilizer_suggestions": "Add organic compost and balanced NPK fertilizer based on soil test",
            "preparation_tips": "Test soil pH, add organic matter, ensure proper drainage"
        })
    except Exception as e:
        return f"Error getting soil information: {str(e)}"

def search_agricultural_info_direct(query: str) -> str:
    """Search for latest agricultural research and information - direct callable version"""
    try:
        api_key = os.getenv('TAVILY_API_KEY')
        if not api_key:
            return "Tavily API key not configured"

        search_tool = TavilySearchResults(max_results=3, tavily_api_key=api_key)
        results = search_tool.invoke({"query": f"agriculture farming {query}"})

        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                'title': result.get('title', 'No title'),
                'content': result.get('content', 'No content'),
                'url': result.get('url', 'No URL')
            })

        return json.dumps(formatted_results, indent=2)
    except Exception as e:
        return f"Search error: {str(e)}"

@tool
def search_agricultural_info(query: str) -> str:
    """Search for latest agricultural research and information"""
    return search_agricultural_info_direct(query)

@tool
def get_crop_advice(location: str, crop: str, season: str) -> str:
    """Get specific crop cultivation advice based on location and season"""
    try:
        # Enhanced crop advice database
        advice_data = {
            "tomato": {
                "planting": "Start indoors 6-8 weeks before last frost, transplant after danger of frost",
                "spacing": "24-36 inches between plants, 48 inches between rows",
                "watering": "1-2 inches per week, consistent moisture, avoid overhead watering",
                "fertilizer": "Balanced 10-10-10 at planting, side dress with nitrogen when fruiting",
                "pest_control": "Watch for hornworms, use companion planting with basil",
                "harvest": "Harvest when fully colored but firm"
            },
            "wheat": {
                "planting": "Plant in fall for winter wheat, spring for spring wheat, 1-2 inches deep",
                "spacing": "6 inches between rows, 1-2 seeds per inch",
                "watering": "Moderate water, avoid waterlogging, critical during heading stage",
                "fertilizer": "Nitrogen-rich fertilizer at tillering and stem extension stages",
                "pest_control": "Monitor for rust and aphids, practice crop rotation",
                "harvest": "Harvest when kernels are hard and moisture is 13-15%"
            },
            "rice": {
                "planting": "Start in nursery, transplant after 25-30 days when seedlings are 6-8 inches",
                "spacing": "6x6 inches between hills, 2-3 seedlings per hill",
                "watering": "Keep flooded with 2-4 inches of water until 2 weeks before harvest",
                "fertilizer": "Split application: basal at transplanting, tillering, panicle initiation",
                "pest_control": "Manage water levels to control weeds, watch for stem borers",
                "harvest": "Harvest when 80-85% of panicles turn yellow"
            },
            "maize": {
                "planting": "Plant after last frost when soil temperature reaches 10°C",
                "spacing": "8-12 inches between plants, 30-36 inches between rows",
                "watering": "1-1.5 inches per week, critical during tasseling and silking",
                "fertilizer": "High nitrogen requirement, side dress when plants are knee-high",
                "pest_control": "Watch for corn borers and armyworms, use Bt varieties",
                "harvest": "Harvest when kernels are milky and silks are brown"
            }
        }
        
        crop_lower = crop.lower()
        crop_advice = advice_data.get(crop_lower, {
            "planting": "Consult local agricultural extension for planting times",
            "spacing": "Standard spacing for crop type based on variety",
            "watering": "Regular irrigation as needed based on soil moisture",
            "fertilizer": "Balanced fertilizer based on soil test results",
            "pest_control": "Implement integrated pest management practices",
            "harvest": "Harvest based on crop maturity indicators"
        })
        
        return json.dumps({
            "crop": crop,
            "location": location,
            "season": season,
            "advice": crop_advice,
            "additional_notes": f"Consider local climate conditions and microclimate in {location}. Consult local agricultural experts for region-specific advice."
        })
    except Exception as e:
        return f"Error getting crop advice: {str(e)}"

class AgriculturalAdvisor:
    def __init__(self):
        self.tools = [
            get_weather_forecast,
            get_soil_info,
            search_agricultural_info,
            get_crop_advice
        ]
        
        self.model = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.7,
            api_key=os.getenv('OPENAI_API_KEY')
        )
        
        self.model_with_tools = self.model.bind_tools(self.tools)
        self.graph = self._create_graph()
    
    def _create_graph(self):
        workflow = StateGraph(AgentState)
        
        # Define nodes
        workflow.add_node("agent", self._call_model)
        workflow.add_node("tools", ToolNode(self.tools))
        
        # Define edges
        workflow.set_entry_point("agent")
        
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {"continue": "tools", "end": END}
        )
        
        workflow.add_edge("tools", "agent")
        
        return workflow.compile()
    
    def _call_model(self, state: AgentState):
        messages = state['messages']
        response = self.model_with_tools.invoke(messages)
        return {"messages": [response]}
    
    def _should_continue(self, state: AgentState):
        messages = state['messages']
        last_message = messages[-1]
        
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "continue"
        return "end"
    
    def get_advice(self, query: str, language: str = "en"):
        try:
            system_prompt = f"""You are an AI Agricultural Advisor. Provide comprehensive, practical farming advice.
            
            Guidelines:
            - Provide advice in {language} language
            - Consider weather, soil conditions, and crop requirements
            - Give specific, actionable recommendations
            - Consider sustainable farming practices
            - Mention potential risks and mitigations
            - Provide step-by-step guidance when appropriate
            - Be culturally appropriate for the region
            - Include both traditional wisdom and modern scientific approaches
            
            Always structure your response clearly with:
            1. Summary of the situation
            2. Specific recommendations
            3. Implementation steps
            4. Potential challenges and solutions
            5. Additional resources or considerations
            
            Use the available tools to gather current weather data, soil information, and agricultural research.
            """
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=query)
            ]
            
            result = self.graph.invoke({
                "messages": messages,
                "user_language": language
            })
            
            return result["messages"][-1].content
            
        except Exception as e:
            return f"I apologize, but I encountered an error while processing your request: {str(e)}. Please try again or contact support if the problem persists."

# Global advisor instance
agricultural_advisor = AgriculturalAdvisor()