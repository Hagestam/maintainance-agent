import anthropic
from app.config import settings
from tools.cmms_tools import create_work_order, search_assets, find_available_technician, get_asset_history

client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

# Conversation memory per user
conversation_history = {}

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
                    "description": "P0 = production stopped or safety hazard, P1 = serious operational issue, P2 = non-urgent issue"
                },
                "description": {
                    "type": "string",
                    "description": "Clear description of the problem, location, and symptoms"
                },
                "asset_id": {
                    "type": "integer",
                    "description": "The asset ID if known, otherwise omit"
                }
            },
            "required": ["priority", "description"]
        }
    },
    {
        "name": "search_assets",
        "description": "Search the asset database by name or keyword to find the asset ID. Use this when the user mentions a machine or equipment name.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The asset name or keyword to search for, e.g. 'dye machine', 'boiler', 'cutter'"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "find_available_technician",
        "description": "Find an available technician, optionally filtered by trade/skill.",
        "input_schema": {
            "type": "object",
            "properties": {
                "trade": {
                    "type": "string",
                    "description": "The trade needed, e.g. 'Electrician', 'Mechanic', 'Plumber'"
                }
            },
            "required": []
        }
    },
    {
        "name": "get_asset_history",
        "description": "Get the recent maintenance history for a specific asset by its ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "asset_id": {
                    "type": "integer",
                    "description": "The asset ID to look up history for"
                }
            },
            "required": ["asset_id"]
        }
    }
]


def handle_message(from_number: str, text: str) -> str:
    print("\n========== AGENT START ==========")
    print(f"From: {from_number}")
    print(f"Message: {text}")

    # Get or create conversation history for this user
    if from_number not in conversation_history:
        conversation_history[from_number] = []

    # Add incoming message to history
    conversation_history[from_number].append({
        "role": "user",
        "content": text
    })

    try:
        print("[1] Loading system prompt...")
        with open("prompts/intake_prompt.txt", "r", encoding="utf-8") as file:
            system_prompt = file.read()

        print("[2] Calling Claude...")
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1024,
            system=system_prompt,
            tools=TOOLS,
            messages=conversation_history[from_number]
        )

        print(f"[3] Claude responded | stop_reason: {response.stop_reason}")

        # Scan all blocks first — don't return on text if a tool call also exists
        tool_block = None
        text_block = None

        for block in response.content:
            print(f"Block type: {block.type}")
            if block.type == "tool_use":
                tool_block = block
            elif block.type == "text" and block.text:
                text_block = block

        # Tool calls take priority over text
        if tool_block:
            print(f"Tool: {tool_block.name} | Input: {tool_block.input}")

            if tool_block.name == "create_work_order":
                tool_result = create_work_order(**tool_block.input)
            elif tool_block.name == "search_assets":
                tool_result = search_assets(**tool_block.input)
            elif tool_block.name == "find_available_technician":
                tool_result = find_available_technician(**tool_block.input)
            elif tool_block.name == "get_asset_history":
                tool_result = get_asset_history(**tool_block.input)
            else:
                tool_result = {"error": "Unknown tool"}

            print(f"Tool result: {tool_result}")

            conversation_history[from_number].append({
                "role": "assistant",
                "content": response.content
            })
            conversation_history[from_number].append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": tool_block.id,
                    "content": str(tool_result)
                }]
            })

            follow_up = client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=1024,
                system=system_prompt,
                tools=TOOLS,
                messages=conversation_history[from_number]
            )

            # follow-up might also be a tool call (e.g. create_work_order after search)
            reply = None
            for b in follow_up.content:
                if b.type == "text" and b.text:
                    reply = b.text
                elif b.type == "tool_use" and b.name == "create_work_order":
                    wo_result = create_work_order(**b.input)
                    reply = (
                        f"Work order #{wo_result['wo_id']} created.\n"
                        f"Priority: {wo_result['priority']}\n"
                        f"A technician will be assigned shortly."
                    )

            if not reply:
                reply = "Work order processed."
                
            conversation_history[from_number].append({
                "role": "assistant",
                "content": reply
            })
            print(f"[4] Returning reply: {reply}")
            print("========== AGENT END ==========\n")
            return reply

        elif text_block:
            conversation_history[from_number].append({
                "role": "assistant",
                "content": text_block.text
            })
            print(f"[4] Text reply: {text_block.text}")
            print("========== AGENT END ==========\n")
            return text_block.text

        return "I processed your request but had no output to return."

    except Exception as error:
        print("\n========== AGENT ERROR ==========")
        print(type(error).__name__)
        print(str(error))
        print("=================================\n")
        return "I received your message but encountered an internal error."