import json
import os

CHAT_FILE = "chats.json"


# ---------------- LOAD ALL ----------------
def load_all_chats():

    # If file doesn't exist return empty
    if not os.path.exists(CHAT_FILE):
        return {}

    try:
        with open(CHAT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            return {}

        return data

    except:
        return {}


# ---------------- SAVE ALL ----------------
def save_all_chats(data):

    try:
        with open(CHAT_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except:
        pass


# ---------------- SAVE CHAT ----------------
def save_chat(user, chat_id, messages):

    if not messages:
        return

    data = load_all_chats()

    if user not in data:
        data[user] = []

    # Generate title from first user message
    title = "New Chat"

    for msg in messages:
        if msg.get("role") == "user":
            title = msg.get("content", "")[:40]
            break

    chat_data = {
        "chat_id": chat_id,
        "title": title,
        "messages": messages
    }

    # Remove existing chat with same id
    data[user] = [c for c in data[user] if c.get("chat_id") != chat_id]

    # Insert latest chat at top
    data[user].insert(0, chat_data)

    save_all_chats(data)


# ---------------- LOAD USER CHATS ----------------
def load_chats(user):

    data = load_all_chats()

    chats = data.get(user, [])

    # Remove invalid chats
    cleaned = []
    for chat in chats:
        if chat.get("chat_id") and chat.get("messages"):
            cleaned.append(chat)

    return cleaned


# ---------------- CLEAR ALL CHATS ----------------
def clear_all_chats():

    if os.path.exists(CHAT_FILE):
        os.remove(CHAT_FILE)