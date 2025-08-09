from typing_extensions import TypedDict

import gradio as gr
from gradio import ChatMessage

from agents import Agent, Runner, function_tool, FileSearchTool


class Location(TypedDict):
    lat: float
    long: float


@function_tool
async def fetch_weather(location: Location) -> str:
    return "sunny"


@function_tool
def add_two_numbers(x: int, y: int) -> int:
    return x + y


building_agent = Agent(
    name="Building Agent",
    instructions="You are a helpful building assistant. You can help students locate rooms on campus.",
    tools=[
        FileSearchTool(
            max_num_results=3,
            vector_store_ids=["vs_6896d8c959008191981d645850b42313"],
            include_search_results=True,
        )
    ],
)

agent = Agent(
    name="Campus Assistant",
    instructions="You are a helpful campus assistant that can plan and execute tasks for students. Please be concise and accurate in handing off tasks to other agents as needed.",
    handoffs=[building_agent],
    tools=[fetch_weather, add_two_numbers],
)


async def chat_with_agent(user_msg: str, history: list):
    current_message = ChatMessage(role="assistant", content="")

    # Initialize context
    context = {"response_buffer": "", "current_messages": [current_message]}

    result = Runner.run_streamed(agent, user_msg)
    async for event in result.stream_events():
        print(event.type)
        if event.type == "raw_response_event":
            # We will support streaming later on
            continue
        else:
            if event.type == "run_item_stream_event":
                print(event.item)
                if event.item.type == "tool_call_item":
                    if event.item.raw_item.type == "file_search_call":
                        context["current_messages"].append(
                            ChatMessage(
                                role="assistant",
                                content="Searching the DigiPen vector store...",
                                metadata={"title": "File Search"},
                            )
                        )
                    else:
                        tool_name = getattr(event.item.raw_item, "name", "unknown_tool")
                        tool_args = getattr(event.item.raw_item, "arguments", {})
                        context["current_messages"].append(
                            ChatMessage(
                                role="assistant",
                                content=f"Calling tool {tool_name} with arguments {tool_args}",
                                metadata={"title": "Tool Call"},
                            )
                        )
                if event.item.type == "tool_call_output_item":
                    context["current_messages"].append(
                        ChatMessage(
                            role="assistant",
                            content=f"Tool output: '{event.item.raw_item['output']}'",
                            metadata={"title": "Tool Output"},
                        )
                    )
                if event.item.type == "message_output_item":
                    context["current_messages"].append(
                        ChatMessage(
                            role="assistant",
                            content=event.item.raw_item.content[0].text,
                        )
                    )
                if event.item.type == "handoff_call_item":
                    context["current_messages"].append(
                        ChatMessage(
                            role="assistant",
                            metadata={"title": "Handing Off Request"},
                            content=f"Name: {event.item.raw_item.name}",
                        )
                    )
        yield context.get("current_messages", [])


demo = gr.ChatInterface(
    chat_with_agent,
    title="DigiPen Campus Assistant",
    theme=gr.themes.Base(primary_hue="red", secondary_hue="slate"),
    examples=[
        ["Where is the 'Hopper' room located?"],
    ],
    submit_btn=True,
    flagging_mode="manual",
    flagging_options=["Like", "Spam", "Inappropriate", "Other"],
    type="messages",
    save_history=False,
)

if __name__ == "__main__":
    demo.launch()
