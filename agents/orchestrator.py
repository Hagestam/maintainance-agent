import anthropic

from app.config import settings
from tools.cmms_tools import create_work_order

client = anthropic.Anthropic(
    api_key=settings.anthropic_api_key
)

TOOLS = [
    {
        "name": "create_work_order",
        "description": (
            "Create a maintenance work order in the CMMS database. "
            "Only call this once you have enough information: what the "
            "problem is, where it is, and the priority."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "priority": {
                    "type": "string",
                    "enum": ["P0", "P1", "P2"],
                    "description": (
                        "P0 = production stopped or safety hazard, "
                        "P1 = serious operational issue, "
                        "P2 = non-urgent issue"
                    )
                },
                "description": {
                    "type": "string",
                    "description": (
                        "Clear description of the problem, location, "
                        "and symptoms"
                    )
                },
                "asset_id": {
                    "type": "integer",
                    "description": (
                        "The asset ID if known, otherwise omit"
                    )
                }
            },
            "required": [
                "priority",
                "description"
            ]
        }
    }
]


def handle_message(from_number: str, text: str) -> str:
    print("\n========== AGENT START ==========")
    print(f"From: {from_number}")
    print(f"Message: {text}")

    try:
        print("[1] Loading system prompt...")

        with open(
            "prompts/intake_prompt.txt",
            "r",
            encoding="utf-8"
        ) as file:
            system_prompt = file.read()

        print("[2] Calling Claude...")

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=system_prompt,
            tools=TOOLS,
            messages=[
                {
                    "role": "user",
                    "content": text
                }
            ]
        )

        print("[3] Claude responded")
        print(f"Stop reason: {response.stop_reason}")

        for block in response.content:

            print(f"Claude block type: {block.type}")

            if block.type == "tool_use":

                print(f"Claude wants to use tool: {block.name}")
                print(f"Tool input: {block.input}")

                if block.name == "create_work_order":

                    result = create_work_order(
                        **block.input
                    )

                    print(f"Work order result: {result}")

                    reply = (
                        f"Work order #{result['wo_id']} created.\n"
                        f"Priority: {result['priority']}\n"
                        f"Someone will be assigned shortly."
                    )

                    print("[4] Returning work order reply...")
                    print("========== AGENT END ==========\n")

                    return reply

            elif block.type == "text" and block.text:

                print(f"Claude text response: {block.text}")
                print("[4] Returning Claude response...")
                print("========== AGENT END ==========\n")

                return block.text

        return "I processed your request, but had no text output to display."

    except Exception as error:

        print("\n========== AGENT ERROR ==========")
        print(type(error).__name__)
        print(str(error))
        print("=================================\n")

        return "I received your message, but I encountered an internal error while processing it."