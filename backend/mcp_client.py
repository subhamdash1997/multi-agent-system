import os
import asyncio
import certifi
from pathlib import Path
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
import sys
from langchain_groq import ChatGroq

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
AVIATIONSTACK_API_KEY = os.getenv("AVIATIONSTACK_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

WEATHER_SERVER_PATH = Path(__file__).resolve().with_name(
    "custom_weather_mcp.py"
)

llm = ChatGroq(
    model=os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b"),
    api_key=os.getenv("GROQ_API_KEY")
)

client = MultiServerMCPClient(
    {
        "tavily":{
            "transport":"streamable_http",
            "url":f"https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY}"
        },
        "aviationstack": {
            "transport": "stdio",
            "command": "uvx",
            "args": [
                "aviationstack-mcp"
            ],
            "env": {
                "AVIATIONSTACK_API_KEY":AVIATIONSTACK_API_KEY
            }
        },
        "weather": {
            "transport": "stdio",
            "command": sys.executable,
            "args": [
                str(WEATHER_SERVER_PATH)
            ],
            "env": {
                "OPENWEATHER_API_KEY": OPENWEATHER_API_KEY or ""
            }
        }
    }
)


# TAKING REQUIRED TOOLS
async def get_tavily_search_tool():
    tools = await client.get_tools()
    return next(tool for tool in tools if tool.name == "tavily_search")


async def get_aviation_tool(tool_name: str):
    tools = await client.get_tools()
    return next(tool for tool in tools if tool.name == tool_name)




# Tavily MCP search
async def tavily_mcp_search(query: str):
    tavily_search_tool = await get_tavily_search_tool()
    result = await tavily_search_tool.ainvoke({"query": query})
    return result


# AviationStack MCP tool caller
async def aviation_mcp_call(tool_name: str, tool_args: dict = None):
    aviation_tool = await get_aviation_tool(tool_name)
    return await aviation_tool.ainvoke(tool_args or {})


# ==========================================
# Weather MCP tools
# ==========================================

weather_tool = None
forecast_tool = None


async def initialize_weather_tools():
    global weather_tool
    global forecast_tool

    if (
        weather_tool is not None
        and forecast_tool is not None
    ):
        return

    if not OPENWEATHER_API_KEY:
        raise RuntimeError(
            "OPENWEATHER_API_KEY is not configured."
        )

    if not WEATHER_SERVER_PATH.is_file():
        raise FileNotFoundError(
            "Weather MCP server file was not found: "
            f"{WEATHER_SERVER_PATH}"
        )

    # Load only Weather.
    # Tavily and AviationStack will not be started.
    tools = await client.get_tools(
        server_name="weather"
    )

    tools_by_name = {
        tool.name: tool
        for tool in tools
    }

    weather_tool = tools_by_name.get(
        "get_current_weather"
    )

    forecast_tool = tools_by_name.get(
        "get_forecast"
    )

    missing_tools = []

    if weather_tool is None:
        missing_tools.append(
            "get_current_weather"
        )

    if forecast_tool is None:
        missing_tools.append(
            "get_forecast"
        )

    if missing_tools:
        available_tools = ", ".join(
            tools_by_name.keys()
        )

        raise RuntimeError(
            "Missing Weather MCP tools: "
            f"{', '.join(missing_tools)}. "
            f"Available tools: "
            f"{available_tools or 'none'}"
        )


async def weather_mcp_search(city: str):
    await initialize_weather_tools()

    result = await weather_tool.ainvoke(
        {
            "city": city
        }
    )

    return result


async def forecast_mcp_search(city: str):
    await initialize_weather_tools()

    result = await forecast_tool.ainvoke(
        {
            "city": city
        }
    )

    return result



# ==========================================
# Destination extractor
# ==========================================

def extract_destination(query: str):
    prompt = f"""
    Extract only the destination city or country.

    Query:
    {query}

    Return only destination name.
    """

    response = llm.invoke(prompt)

    return response.content.strip()


if __name__ == "__main__":
    print(asyncio.run(tavily_mcp_search("When the next fifa world cup will host?")))