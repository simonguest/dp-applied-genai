from typing_extensions import TypedDict

import gradio as gr
from gradio import ChatMessage

from agents import Agent, Runner, function_tool


class Location(TypedDict):
    lat: float
    long: float


@function_tool
async def fetch_weather(location: Location) -> str:
    return "sunny"


@function_tool
def add_two_numbers(x: int, y: int) -> int:
    return x + y


agent = Agent(
    name="Planner",
    instructions="You are a planner that can plan and execute tasks. Please be concise and accurate in distributing each question.",
    tools=[fetch_weather],
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
        yield context.get("current_messages", [])


demo = gr.ChatInterface(
    chat_with_agent,
    title="DigiPen Campus AI Agent",
    theme=gr.themes.Base(primary_hue="red", secondary_hue="slate"),
    examples=[
        ["What's the weather in Seattle?"],
    ],
    submit_btn=True,
    flagging_mode="manual",
    flagging_options=["Like", "Spam", "Inappropriate", "Other"],
    type="messages",
    save_history=False,
)

if __name__ == "__main__":
    demo.launch()