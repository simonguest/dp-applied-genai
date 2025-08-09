import asyncio

import json

from typing_extensions import TypedDict, Any

from agents import Agent, Runner, FunctionTool, RunContextWrapper, function_tool


class Location(TypedDict):
    lat: float
    long: float

@function_tool  
async def fetch_weather(location: Location) -> str:
    
    """Fetch the weather for a given location.

    Args:
        location: The location to fetch the weather for.
    """
    # In real life, we'd fetch the weather from a weather API
    return "sunny"


@function_tool(name_override="fetch_data")  
def read_file(ctx: RunContextWrapper[Any], path: str, directory: str | None = None) -> str:
    """Read the contents of a file.

    Args:
        path: The path to the file to read.
        directory: The directory to read the file from.
    """
    # In real life, we'd read the file from the file system
    return "<file contents>"


async def main():
    agent = Agent(
        name="Assistant",
        tools=[fetch_weather, read_file],  
    )

    for tool in agent.tools:
        if isinstance(tool, FunctionTool):
            print(tool.name)
            print(tool.description)
            print(json.dumps(tool.params_json_schema, indent=2))
            print()

    result = Runner.run_streamed(
        agent,
        "What is the weather in Seattle?"
    )
    async for event in result.stream_events():
        print(event.type)
        if event.type == "run_item_stream_event":
          if event.item.type == "message_output_item":
              print(event.item.raw_item.content[0].text)

    #print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())