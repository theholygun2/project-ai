import uuid
from graph import personal_assistant_graph
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage
from util import _print_event

thread_id = str(uuid.uuid4())
print("THREAD ID:", thread_id)

config = {
    "configurable": {
        "thread_id": thread_id,
    }
}

print("Welcome to the personal assistant. Type 'exit' to end the conversation.")

event_lookup = {}  # Store recent events for user-friendly delete confirmations

while True:
    user_input = input("You: ").strip()

    if user_input.lower() == 'exit':
        print("Goodbye!")
        break

    events = personal_assistant_graph.stream(
        {"messages": [HumanMessage(content=user_input)]},
        config,
        stream_mode="values"
    )

    _printed = set()
    for event in events:
        _print_event(event, _printed)

        if event.get("type") == "tool_result":
            tool_call_id = None
            tool_response = event.get("output", "No output returned")

            # Save events for later reference
            if isinstance(tool_response, dict) and "events" in tool_response:
                for ev in tool_response["events"]:
                    event_lookup[ev["id"]] = ev  # Save by ID

            if (
                "messages" in event
                and isinstance(event["messages"][-1], AIMessage)
                and event["messages"][-1].tool_calls
            ):
                tool_call_id = event["messages"][-1].tool_calls[0].get("id")

            if tool_call_id:
                if isinstance(tool_response, (dict, list)):
                    tool_response = str(tool_response)

                followup = ToolMessage(
                    tool_call_id=tool_call_id,
                    content=tool_response or "No output returned"
                )
                result = personal_assistant_graph.stream(
                    {"messages": [followup]},
                    config,
                    stream_mode="values"
                )

                for event in result:
                    _print_event(event, _printed)

    snapshot = personal_assistant_graph.get_state(config)

    while snapshot.next:
        try:
            # Try to extract event_id from pending tool call
            tool_call = snapshot.next.get("messages", [])[-1].tool_calls[0]
            event_id = tool_call.get("args", {}).get("event_id")
            if event_id and event_id in event_lookup:
                ev = event_lookup[event_id]
                summary = ev.get("summary", "No Title")
                start = ev.get("start", "").replace("T", " ").replace("+07:00", "")
                print(f"\n📌 You're about to delete this event:\n- **{summary}** on {start}")
        except Exception:
            pass  # No event to display

        try:
            user_approval = input(
                "\n❓ Proceed with the above action? (y = yes, anything else = no)\n> "
            )
        except:
            user_approval = "y"

        if user_approval.strip().lower() == "y":
            result = personal_assistant_graph.stream(
                None,
                config,
                stream_mode="values"
            )
        else:
            print("[INFO] Tool call not approved. Awaiting user follow-up.")
            break

        for event in result:
            _print_event(event, _printed)

        snapshot = personal_assistant_graph.get_state(config)
