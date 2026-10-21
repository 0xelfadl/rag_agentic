import json
import sys
from datetime import date

from llm import MODEL, client
from search import search

MAX_STEPS = 6  # safety net: the most model calls we allow for one question

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

SYSTEM_PROMPT = f"""You are the support assistant for Voltway, an e-bike company.
Answer questions about Voltway using ONLY passages returned by search_documents.

How to work:
- For any question about Voltway, search before answering. Never use your general knowledge of e-bikes.
- For greetings or questions unrelated to Voltway, reply briefly without searching.
- If the question has several parts, search once per part.
- If the results don't answer the question, rephrase and search again, or filter by doc_type.
- Cite every fact with its ref in square brackets, e.g. [warranty-policy#3].
- If the passages don't contain the answer, say so plainly and suggest contacting Voltway support.
  Never guess prices, numbers or dates.
- Today's date is {date.today().isoformat()}.
- Stop searching as soon as the results answer the question."""


def run_tool(name: str, arguments: dict) -> list[dict]:
    """Our code, not the model, actually runs the tool."""
    if name == "search_documents":
        return search(arguments["query"], top_k=5, doc_type=arguments.get("doc_type"))
    raise ValueError(f"Unknown tool: {name}")


def ask(question: str) -> str:
    # The conversation so far. It grows at every step: this list IS the agent's memory.
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]

    for step in range(1, MAX_STEPS + 1):
        response = client.chat.completions.create(model=MODEL, messages=messages, tools=[SEARCH_TOOL])
        message = response.choices[0].message

        # 1. No tool requested? Then this is the final answer: the loop ends.
        if not message.tool_calls:
            return message.content

        # 2. Keep the model's request in the history, exactly as it came back.
        messages.append(message.model_dump(exclude_none=True))

        # 3. Run each requested tool and add its result to the history.
        for call in message.tool_calls:
            arguments = json.loads(call.function.arguments)
            print(f"  [step {step}] {call.function.name}({arguments})")
            hits = run_tool(call.function.name, arguments)
            print("           <- " + ", ".join(f"{hit['ref']} ({hit['score']})" for hit in hits))
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,  # tells the model which request this result answers
                "content": json.dumps(hits),
            })
        # 4. Loop: the model now sees the results and decides what to do next.

    return "Sorry, I couldn't find an answer within the step limit."


DEMO_QUESTIONS = [
    "How long does it take to charge the battery?",
    (
        "My bike shows E07 since the last update and my warranty ended last year. "
        "What does E07 mean, and will Voltway still fix it for free?"
    ),
    "Can I clean my bike with a pressure washer?",
    "How much does the Voltway V2 cost?",
    "Hi there!",
]


def main():
    questions = [" ".join(sys.argv[1:])] if len(sys.argv) > 1 else DEMO_QUESTIONS
    for question in questions:
        print(f"\nQ: {question}")
        answer = ask(question)
        print(f"\nA: {answer}\n" + "-" * 70)


if __name__ == "__main__":
    main()