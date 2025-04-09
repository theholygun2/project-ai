from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import tools_condition
from state import State
from assistant import assistant, sensitive_tool_names, sensitive_tools, safe_tools
from util import create_tool_node_with_fallback

def route_tools(state:State):
    next_node = tools_condition(State)
    if next_node == END:
        return END
    ai_message = state["messages"][-1]
    first_tool_call = ai_message.tool_calls[0]
    if first_tool_call["name"] in sensitive_tool_names:
        return "sensitive_tools"
    return "safe_tools"

builder = StateGraph(State)

builder.add_node("assistant", assistant)
builder.add_node("safe_tools", create_tool_node_with_fallback(safe_tools))
builder.add_node("sensitive_tools", create_tool_node_with_fallback(sensitive_tools))

builder.add_edge(START, "assistant")
builder.add_conditional_edges(
    "assistant",
    route_tools, ["safe_tools", "sensitive_tools", END]
)
builder.add_edge("safe_tools", "assistant")
builder.add_edge("sensitive_tools", "assistant")

memory = MemorySaver()
personal_assistant_graph = builder.compile(checkpointer=memory, interrupt_before=["sensitive_tools"])