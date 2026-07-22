def select_newest_messages(messages, input_budget):
    selected = []
    remaining = input_budget

    for message in reversed(messages):
        if message["tokens"] <= remaining:
            selected.append(message)
            remaining -= message["tokens"]

    return list(reversed(selected)), remaining


if __name__ == "__main__":
    messages = [
        {"role": "user", "tokens": 12, "content": "I prefer email updates."},
        {"role": "assistant", "tokens": 14, "content": "I will use email updates."},
        {"role": "user", "tokens": 11, "content": "My order is delayed."},
        {"role": "assistant", "tokens": 13, "content": "I will check the order status."},
        {"role": "user", "tokens": 10, "content": "What is the latest status?"},
    ]

    selected, remaining = select_newest_messages(messages, input_budget=35)
    print("Selected messages:")
    for message in selected:
        print(f"- {message['role']}: {message['content']} ({message['tokens']} toy tokens)")
    print("Unused toy-token budget:", remaining)
