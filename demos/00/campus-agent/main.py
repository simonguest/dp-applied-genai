import gradio as gr
from gradio import ChatMessage
from agents import Agent, Runner, function_tool, FileSearchTool

VECTOR_STORE_ID = "vs_6896d8c959008191981d645850b42313"


@function_tool
def get_bytes_cafe_menu(date: str) -> any:
    return {
        f"{date}": {
            "daily byte": {
                "name": "Steak Quesadilla",
                "price": 12,
                "description": "Flank steak, mixed cheese in a flour tortilla served with air fried potatoes, sour cream and salsa",
            },
            "vegetarian": {
                "name": "Impossible Quesadilla",
                "price": 12,
                "description": "Impossible plant based product, mixed cheese in a flour tortilla served with air fried potatoes, sour cream and salsa",
            },
            "international": {
                "name": "Chicken Curry",
                "price": 12,
                "description": "Chicken thighs, onion, carrot, potato, curry sauce served over rice",
            },
        }
    }


cafe_agent = Agent(
    name="Cafe Agent",
    instructions="You help students locate and provide information about the Bytes Cafe.",
    tools=[
        get_bytes_cafe_menu,
    ],
)


building_agent = Agent(
    name="Building Agent",
    instructions="You help students locate and provide information about buildings and rooms on campus. Be descriptive when giving locations.",
    tools=[
        FileSearchTool(
            max_num_results=3,
            vector_store_ids=[VECTOR_STORE_ID],
            include_search_results=True,
        ),
        get_bytes_cafe_menu,
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
    handoffs=[building_agent, course_agent, handbook_agent, cafe_agent],
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
            if event.type == "agent_updated_stream_event":
                print(event)
                context["current_messages"].append(
                    ChatMessage(
                        role="assistant",
                        content=f"{event.new_agent.name}",
                        metadata={"title": "Agent Now Running"},
                    )
                )
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
        "What's today's vegetarian dish at the Bytes Cafe?",
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
