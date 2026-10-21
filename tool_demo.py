import json

from llm import MODEL, client

# This is ALL the model will ever know about our search function: a name,
# a description and a JSON schema of its arguments. It never sees our code.
SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "search_documents",
        "description": (
            "Semantic search over Voltway documentation (FAQ, warranty policy, owner manual, "
            "release notes). Returns the most relevant passages with a ref to cite and a score."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Short search query with the key terms, not the whole user message.",
                },
                "doc_type": {
                    "type": "string",
                    "enum": ["faq", "policy", "manual", "release-notes"],
                    "description": "Optional: only search this type of document.",
                },
            },
            "required": ["query"],
        },
    },
}

SYSTEM_PROMPT = (
    "You are the support assistant for Voltway, an e-bike company. "
    "Use search_documents for any question about Voltway. For greetings, just reply."
)

def ask_once(question: str) -> None:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
        tools=[SEARCH_TOOL],
    )
    message = response.choices[0].message

    if message.tool_calls:
        for call in message.tool_calls:
            arguments = json.loads(call.function.arguments)
            print(f" ->, the model asks to call {call.function.name}({arguments})")
    else:
        print(f"  -> the model answers directly: {message.content}")


def main():
    questions = [
        "How long does it take to charge the battery?",
        "Hi there!",
        "My bike shows E07 since the last update. Is that covered by the warranty?",
    ]
    for question in questions:
        print(f"\nQ: {question}")
        ask_once(question)


if __name__ == "__main__":
    main()