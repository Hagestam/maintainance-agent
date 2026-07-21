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

def handle_message(from_number: str, text: str, image_base64: str = None, image_mime_type: str = None) -> str:
    print("\n========== AGENT START ==========")
    print(f"From: {from_number} | Message: {text}")

    if from_number not in conversation_history:
        conversation_history[from_number] = []

    # Build message content — text only, or text + image
    if image_base64 and image_mime_type:
        user_content = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": image_mime_type,
                    "data": image_base64
                }
            },
            {
                "type": "text",
                "text": text if text.strip() else "I sent a photo of the issue. What do you see?"
            }
        ]
    else:
        user_content = text

    conversation_history[from_number].append({
        "role": "user",
        "content": user_content
    })

    try:
        with open("prompts/intake_prompt.txt", "r", encoding="utf-8") as file:
            system_prompt = file.read()

        # Allow up to 5 rounds of tool calling
        for _ in range(5):
            response = client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=1024,
                system=system_prompt,
                tools=TOOLS,
                messages=conversation_history[from_number]
            )

            print(f"Stop reason: {response.stop_reason}")

            # If Claude is done — just return the text
            if response.stop_reason == "end_turn":
                for block in response.content:
                    if block.type == "text" and block.text:
                        conversation_history[from_number].append({
                            "role": "assistant",
                            "content": block.text
                        })
                        print(f"Reply: {block.text}")
                        return block.text
                return "Done."

            # Claude wants to call tools — run ALL of them
            if response.stop_reason == "tool_use":
                tool_results = []

                for block in response.content:
                    if block.type == "tool_use":
                        print(f"Tool: {block.name} | Input: {block.input}")

                        if block.name == "create_work_order":
                            result = create_work_order(**block.input)
                        elif block.name == "search_assets":
                            result = search_assets(**block.input)
                        elif block.name == "find_available_technician":
                            result = find_available_technician(**block.input)
                        elif block.name == "get_asset_history":
                            result = get_asset_history(**block.input)
                        else:
                            result = {"error": "Unknown tool"}

                        print(f"Result: {result}")
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": str(result)
                        })

                # Add Claude's response and ALL tool results to history
                conversation_history[from_number].append({
                    "role": "assistant",
                    "content": response.content
                })
                conversation_history[from_number].append({
                    "role": "user",
                    "content": tool_results
                })

        return "I was unable to complete the request."

    except Exception as error:
        print(f"ERROR: {type(error).__name__}: {error}")
        return "I received your message but encountered an internal error."