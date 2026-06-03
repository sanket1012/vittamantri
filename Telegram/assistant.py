from groq import Groq
from collections import defaultdict
import os

MODEL = "llama-3.3-70b-versatile"
MAX_HISTORY = 20  # messages per user (kept in pairs)

SYSTEM_PROMPT = """You are Sanket's personal AI assistant, integrated into his Telegram.

Your role:
- Help Sanket with tasks, questions, planning, research, writing, code, and anything else he needs
- Be concise and direct — no filler, no unnecessary padding
- Remember context within the current conversation to give coherent, continuous help
- When asked to do something complex, break it into clear steps
- Format responses with markdown when it aids clarity (lists, code blocks, etc.)
- You have no access to external tools or the internet unless Sanket provides information
- Be proactive: if you notice something Sanket might want to know, mention it briefly
- You have a financial tracking system. If Sanket asks about expenses, balance, or transactions, direct him to /balance, /history, or /report commands.

Tone: professional but conversational, like a sharp colleague who gets things done."""

client = Groq(api_key=os.environ["GROQ_API_KEY"])
histories: dict[int, list[dict]] = defaultdict(list)


def chat(user_id: int, user_message: str) -> str:
    history = histories[user_id]
    history.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + history,
        temperature=0.7,
        max_tokens=2048,
    )

    reply = response.choices[0].message.content
    history.append({"role": "assistant", "content": reply})

    # Trim history to avoid token bloat (keep last MAX_HISTORY messages)
    if len(history) > MAX_HISTORY:
        histories[user_id] = history[-MAX_HISTORY:]

    return reply


def clear_history(user_id: int) -> None:
    histories[user_id] = []
