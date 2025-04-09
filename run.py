import uuid
from graph import personal_assistant_graph
from langchain_core.messages.tool import ToolMessage
from util import _print_event

thread_id = str(uuid.uuid4())
print("THREAD ID", thread_id)

config = {
    "configurable": {
        "thread_id": thread_id,
    }
}

print("Welcome to the personal assistant. Type 'exit' to end the conversation.")

while True:
    user_input = input("You: ").strip()

    if user_input.lower() == 'exit':
        print("Goodbye!")
        break

    events = personal_assistant_graph.stream(
        {"messages": {"user", user_input}}, config, stream_mode="values"
    )

    _printed = set()
    print(events)
    for event in events:
        _print_event(event, _printed)
    
    snapshot = personal_assistant_graph.get_state(config)
    while snapshot.next:
        try:
            user_approval = input(
                "Do you approve of the above action? Type 'y' to continue;"
                "otherwise, explain your requested changes.\n\n"
            )
        except:
            user_approval = "y"

        if user_approval.strip().lower == "y":
            result = personal_assistant_graph.stream(
                None,
                config,
                stream_mode="values"
            )
        else:
            result = personal_assistant_graph.stream(
                {
                    "messages": [
                        ToolMessage(
                            tool_call_id=event["messages"][-1].tool_calls[0]["id"],
                            content=f"API call denied by user. Reasoning: '{user_approval}. Continue assisting, accounting for the  "
                        )
                    ]
                },
                config,
                stream_mode="values"
            )

        for event in result:
            _print_event(event, _printed)

        snapshot = personal_assistant_graph.get_state(config)