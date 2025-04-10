from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from state import State
from tools import create_event, read_events, update_event, delete_event, read_sheet, update_sheet, delete_row
from dotenv import load_dotenv
import os

load_dotenv()

class Assistant:
    def __init__(self, runnable:Runnable):
        self.runnable = runnable

    def __call__(self, state: State):
        while True:
            result = self.runnable.invoke(state)

            if not result.tool_calls and (
                not result.content
                or isinstance(result.content, list)
                and not result.content[0].get("text")
            ):
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
            else:
                break
        return {"messages": result}

llm = ChatOpenAI(
    model="openai/gpt-3.5-turbo",  # or other OpenRouter-supported model
    base_url="https://openrouter.ai/api/v1",  # <--- NEW!
    api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0.5
)



primary_assistant_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful personal assistant. "
            "Use the provided tools to manage Google Calendar for scheduling meetings "
            "and Google Sheets for personal finance management. "
            "When using these tools, be precise and efficient. "
            "If a task requires multiple steps, break it down and use the appropriate tools for each step."
            "\nFor google sheets, you should grab from column A to E"
            "\nCurrent time: {time}, timezone: {timezone}.",
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now(), timezone="Indonesia/Jakarta")

# personal_assistant_tools = [
#     create_event,
#     read_events,
#     update_event,
#     delete_event,
#     read_sheet,
#     update_sheet,
#     delete_row
# ]

safe_tools = [
    read_events,
    read_sheet
]

sensitive_tools = [
    create_event,
    update_event,
    delete_event,
    update_sheet,
    delete_row
]

sensitive_tool_names = {tool.name for tool in sensitive_tools}

personal_assistant_runnable = primary_assistant_prompt | llm.bind_tools(safe_tools + sensitive_tools)

assistant = Assistant(personal_assistant_runnable)