from typing_extensions import TypedDict

import gradio as gr
from gradio import ChatMessage

from agents import Agent, Runner, function_tool, FileSearchTool

VECTOR_STORE_ID = "vs_6896d8c959008191981d645850b42313"


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
    instructions="You help students locate and provide information about rooms and buildings on campus. Be descriptive when giving locations.",
    tools=[
        FileSearchTool(
            max_num_results=3,
            vector_store_ids=[VECTOR_STORE_ID],
            include_search_results=True,
        )
    ],
)

course_agent = Agent(
    name="Course Agent",
    instructions="You help students find out information about courses held at DigiPen.",
    tools=[
        FileSearchTool(
            max_num_results=5,
            vector_store_ids=[VECTOR_STORE_ID],
            include_search_results=True,
        )
    ],
)

handbook_agent = Agent(
    name="Handbook Agent",
    instructions="You help students navigate the school handbook, providing information about campus policies and student conduct.",
    tools=[
        FileSearchTool(
            max_num_results=5,
            vector_store_ids=[VECTOR_STORE_ID],
            include_search_results=True,
        )
    ],
)

agent = Agent(
    name="DigiPen Campus Assistant",
    instructions="You are a helpful campus assistant that can plan and execute tasks for students at DigiPen. Please be concise and accurate in handing off tasks to other agents as needed.",
    handoffs=[building_agent, course_agent, handbook_agent],
    tools=[],
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
        "Where is the 'Hopper' room located?",
        "I'm trying to find the WANIC classrooms. Can you help?",
        "What's the policy for eating in auditoriums?",
        "Where do I pickup my parking pass?",
        "Tell me more about CS 205...",
        "What are the prerequisites for FLM201?",
        "Which courses should I consider if I'm interested in audio mixing techniques?",
    ],
    submit_btn=True,
    flagging_mode="manual",
    flagging_options=["Like", "Spam", "Inappropriate", "Other"],
    type="messages",
    save_history=False,
)

if __name__ == "__main__":
    demo.launch()
