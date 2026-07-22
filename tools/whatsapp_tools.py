import httpx

# Point to your local Node.js Express WhatsApp bridge
LOCAL_BRIDGE_URL = "http://localhost:3000/send-message"

def send_whatsapp(to: str, message: str) -> dict:
    """
    Sends a WhatsApp message via the local Node.js WhatsApp Web bridge.
    """
    # Ensure the phone number format matches what the local bridge expects 
    # (e.g., appending @c.us if the bridge requires WhatsApp web format, 
    # or just sending the clean number string)
    
    payload = {
        "phone": to,
        "message": message
    }

    try:
        response = httpx.post(
            LOCAL_BRIDGE_URL,
            json=payload,
            timeout=30
        )

        print(f"Node Bridge status: {response.status_code}")
        print(f"Node Bridge response: {response.text}")

        response.raise_for_status()

        print(f"[SENT] Message successfully routed to local WhatsApp bridge for {to}")
        return {"status": "sent", "to": to}

    except httpx.HTTPStatusError as e:
        print(f"[ERROR] Bridge failed for {to}: {e.response.text}")
        return {"status": "failed", "error": e.response.text}

    except Exception as e:
        print(f"[ERROR] Unexpected error connecting to WhatsApp bridge: {e}")
        return {"status": "failed", "error": str(e)}