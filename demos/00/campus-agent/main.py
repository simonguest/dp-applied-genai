import contextlib
import os

import gradio as gr
from event_handler import EventHandlerChain
from gradio import ChatMessage
from openai import AsyncOpenAI

from agents import Agent, ModelSettings, OpenAIChatCompletionsModel, Runner
from agents.mcp import MCPServer, MCPServerSse, MCPServerSseParams

from agents import FunctionTool, RunContextWrapper, function_tool

def create_agent_app(agent: Agent, mcp_servers: list[MCPServer], event_handler_chain: EventHandlerChain):

    # Use closure to create chat function
    async def chat_function_with_agent(user_msg: str, history: list):
        """
        Asynchronous streaming chat function - uses closure to access agent and mcp_servers
        """
        current_message = ChatMessage(role="assistant", content="")

        # Initialize context
        context = {"response_buffer": "", "current_messages": [current_message]}

        async with contextlib.AsyncExitStack() as stack:
            # for server in mcp_servers:
            #     await stack.enter_async_context(server)
            # Use Runner.run_streamed to get streaming results
            result = Runner.run_streamed(agent, user_msg)
            async for event in result.stream_events():
                # Use chain of responsibility to process all events
                if event_handler_chain.process_event(event, history, context):
                    # Get current messages from context and yield
                    current_messages = context.get("current_messages", [])
                    print(current_messages)
                    yield current_messages


    return gr.ChatInterface(
        chat_function_with_agent,
        title="🤖 OpenAI Agent Chat Interface",
        description="Chat with an AI assistant powered by OpenAI Agents SDK",
        theme=gr.themes.Base(
            primary_hue="red",
            secondary_hue="slate"
        ),
        examples=[["using gradio mcp tool for me to explain what's ChatInterface"],
                ["using gradio mcp tool for me to explain what's Route?"]],
        submit_btn=True,
        flagging_mode="manual",
        flagging_options=["Like", "Spam", "Inappropriate", "Other"],
        type="messages",
        save_history=True
    )

# Create a deepseek OpenAI client pointing to DeepSeek
custom_client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)


deepseek_v3_model = OpenAIChatCompletionsModel(
        model="gpt-4o-mini",
        openai_client=custom_client
)

model_settings = ModelSettings(
    temperature=0.0,
    top_p=1.0,
    frequency_penalty=0.0,
    presence_penalty=0.0
)

gradio_mcp = MCPServerSse(
    name="Gradio Server",
    params=MCPServerSseParams(
        url="https://gradio-docs-mcp.hf.space/gradio_api/mcp/sse",
        timeout=180
    )
)

doc_agent = Agent(
    name="Gradio",
    instructions="You are a gradio doc agent that can answer questions and help with tasks. Please be concise and accurate in your responses.",
    mcp_servers=[gradio_mcp],
    model=deepseek_v3_model,
    model_settings=model_settings
)

@function_tool
async def fetch_weather(location: str) -> int:
    return 80

plan_agent = Agent(
    name="Planner",
    instructions="You are a planner that can plan and execute tasks. Please be concise and accurate in distributing each question.",
    model=deepseek_v3_model,
    tools=[fetch_weather]
)

event_handler_chain = EventHandlerChain()

demo = create_agent_app(plan_agent, [gradio_mcp], event_handler_chain)

if __name__ == "__main__":
    demo.launch()


