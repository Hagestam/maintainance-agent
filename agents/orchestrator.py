import anthropic
from app.config import settings
# 1. Import ADMIN_NUMBERS from admin_tools
from tools.admin_tools import (
    ADMIN_NUMBERS,
    delete_work_order,
    view_all_work_orders,
)
from tools.cmms_tools import (
    create_work_order,
    search_assets,
    find_available_technician,
    get_asset_history,
)

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
                    "description": "P0 = production stopped or safety hazard, P1 = serious operational issue, P2 = non-urgent issue",
                },
                "description": {
                    "type": "string",
                    "description": "Clear description of the problem, location, and symptoms",
                },
                "asset_id": {
                    "type": "integer",
                    "description": "The asset ID if known, otherwise omit",
                },
            },
            "required": ["priority", "description"],
        },
    },
    {
        "name": "delete_work_order",
        "description": "ADMIN ONLY. Delete a work order permanently from the database.",
        "input_schema": {
            "type": "object",
            "properties": {
                "wo_id": {
                    "type": "integer",
                    "description": "The ID of the work order to delete",
                }
            },
            "required": ["wo_id"],
        },
    },
    {
        "name": "view_all_work_orders",
        "description": "ADMIN ONLY. View all reported tasks/work orders. Can be filtered by status (e.g., 'open', 'completed', 'pending').",
        "input_schema": {
            "type": "object",
            "properties": {
                "status_filter": {
                    "type": "string",
                    "description": "Optional status to filter by (e.g. 'open', 'closed'). Omit to see all.",
                }
            },
            "required": [],
        },
    },
    {
        "name": "search_assets",
        "description": "Search the asset database by name or keyword to find the asset ID. Use this when the user mentions a machine or equipment name.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The asset name or keyword to search for, e.g. 'dye machine', 'boiler', 'cutter'",
                }
            },
            "required": ["query"],
        },
    },
    {
        "name": "find_available_technician",
        "description": "Find an available technician, optionally filtered by trade/skill.",
        "input_schema": {
            "type": "object",
            "properties": {
                "trade": {
                    "type": "string",
                    "description": "The trade needed, e.g. 'Electrician', 'Mechanic', 'Plumber'",
                }
            },
            "required": [],
        },
    },
    {
        "name": "get_asset_history",
        "description": "Get the recent maintenance history for a specific asset by its ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "asset_id": {
                    "type": "integer",
                    "description": "The asset ID to look up history for",
                }
            },
            "required": ["asset_id"],
        },
    },
]


def get_trimmed_history(history: list, max_messages: int = 6) -> list:
    """
    Trims history to the last N messages while ensuring:
    1. The sequence starts with a 'user' message.
    2. No dangling 'tool_result' blocks are left at the beginning.
    """
    if len(history) <= max_messages:
        return history

    trimmed = history[-max_messages:]

    while trimmed:
        first_msg = trimmed[0]
        if first_msg.get("role") == "user":
            content = first_msg.get("content")
            is_tool_result = (
                isinstance(content, list)
                and len(content) > 0
                and content[0].get("type") == "tool_result"
            )
            if not is_tool_result:
                break
        trimmed.pop(0)

    return trimmed if trimmed else history


def handle_message(
    from_number: str,
    text: str,
    image_base64: str = None,
    image_mime_type: str = None,
) -> str:
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
                    "data": image_base64,
                },
            },
            {
                "type": "text",
                "text": text.strip()
                if text.strip()
                else "I sent a photo of the issue. What do you see?",
            },
        ]
    else:
        user_content = text

    conversation_history[from_number].append(
        {"role": "user", "content": user_content}
    )

    # 2. Dynamically filter tools based on user permissions (Strategy A)
    is_admin = from_number in ADMIN_NUMBERS
    active_tools = [
        t
        for t in TOOLS
        if is_admin or not t["name"].startswith(("delete_", "view_all_"))
    ]

    try:
        with open("prompts/intake_prompt.txt", "r", encoding="utf-8") as file:
            system_prompt = file.read()

        # Allow up to 5 rounds of tool calling
        for _ in range(7):
            # 3. Trim message history safely before calling API (Strategy B)
            trimmed_history = get_trimmed_history(
                conversation_history[from_number], max_messages=10
            )

            response = client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=1024,
                system=system_prompt,
                tools=active_tools,
                messages=trimmed_history,
            )

            print(f"Stop reason: {response.stop_reason}")

            # If Claude is done — just return the text
            if response.stop_reason == "end_turn":
                for block in response.content:
                    if block.type == "text" and block.text:
                        conversation_history[from_number].append(
                            {"role": "assistant", "content": block.text}
                        )
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
                        elif block.name == "delete_work_order":
                            block.input["requesting_user"] = from_number
                            result = delete_work_order(**block.input)
                        elif block.name == "view_all_work_orders":
                            block.input["requesting_user"] = from_number
                            result = view_all_work_orders(**block.input)
                        elif block.name == "search_assets":
                            result = search_assets(**block.input)
                        elif block.name == "find_available_technician":
                            result = find_available_technician(**block.input)
                        elif block.name == "get_asset_history":
                            result = get_asset_history(**block.input)
                        else:
                            result = {"error": "Unknown tool"}

                        print(f"Result: {result}")
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": str(result),
                            }
                        )

                # Add Claude's response and ALL tool results to history
                conversation_history[from_number].append(
                    {"role": "assistant", "content": response.content}
                )
                conversation_history[from_number].append(
                    {"role": "user", "content": tool_results}
                )

        return "I was unable to complete the request."

    except Exception as error:
        print(f"ERROR: {type(error).__name__}: {error}")
        return "I received your message but encountered an internal error."