from pprint import pprint


def build_request(stored_history, new_question, max_previous_turns=2):
    selected_history = stored_history[-max_previous_turns:]
    return [
        {"role": "system", "content": "You are a concise delivery-support assistant."},
        *selected_history,
        {"role": "user", "content": new_question},
    ]


if __name__ == "__main__":
    stored_history = [
        {"role": "user", "content": "I moved from Pune to Mumbai."},
        {"role": "assistant", "content": "I can update your delivery address."},
        {"role": "user", "content": "Please use my Mumbai address for future orders."},
        {"role": "assistant", "content": "Done. Your future-order address is Mumbai."},
    ]

    print("Stored history has", len(stored_history), "messages.")
    print("\nThe application chooses only the latest two for this request:")
    pprint(build_request(stored_history, "Where will my next order go?"))
