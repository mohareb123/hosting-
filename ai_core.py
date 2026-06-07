"""Gemini-based AI core with function calling for SuperAgent tools."""
import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL, SYSTEM_PROMPT
from bot import tools as T
import storage

genai.configure(api_key=GEMINI_API_KEY)

# Tool declarations for Gemini function calling
TOOL_DECLARATIONS = [
    {
        "name": "web_search",
        "description": "Search the web for current/factual information.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"}}, "required": ["query"]},
    },
    {
        "name": "fetch_url",
        "description": "Fetch and read a webpage's text content.",
        "parameters": {"type": "object", "properties": {
            "url": {"type": "string"}}, "required": ["url"]},
    },
    {
        "name": "get_weather",
        "description": "Get current weather for a city or location.",
        "parameters": {"type": "object", "properties": {
            "location": {"type": "string"}}, "required": ["location"]},
    },
    {
        "name": "crypto_price",
        "description": "Get cryptocurrency price. Use the CoinGecko id (bitcoin, ethereum, solana...).",
        "parameters": {"type": "object", "properties": {
            "coin": {"type": "string"}}, "required": ["coin"]},
    },
    {
        "name": "translate",
        "description": "Translate text to a target language (use ISO codes like ar, en, fr, es).",
        "parameters": {"type": "object", "properties": {
            "text": {"type": "string"},
            "target": {"type": "string"}},
            "required": ["text", "target"]},
    },
    {
        "name": "read_rss",
        "description": "Read entries from an RSS feed URL.",
        "parameters": {"type": "object", "properties": {
            "url": {"type": "string"}}, "required": ["url"]},
    },
    {
        "name": "video_info",
        "description": "Extract metadata from a video URL (YouTube, etc.) via yt-dlp.",
        "parameters": {"type": "object", "properties": {
            "url": {"type": "string"}}, "required": ["url"]},
    },
    {
        "name": "run_python",
        "description": "Run Python code in a sandboxed subprocess. Returns stdout/stderr.",
        "parameters": {"type": "object", "properties": {
            "code": {"type": "string"}}, "required": ["code"]},
    },
    {
        "name": "browse_and_interact",
        "description": "Browse a website interactively with Playwright. Maintains session (cookies/state) across calls for the same user. Use for complex, multi-step tasks like logging in or multi-page forms.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Optional: New URL to navigate to. Omit to stay on current page."},
                "actions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string", "enum": ["click", "fill", "press", "wait"]},
                            "selector": {"type": "string", "description": "CSS selector for the element."},
                            "value": {"type": "string", "description": "Value for 'fill' or 'press' actions."}
                        },
                        "required": ["type", "selector"]
                    }
                }
            }
        },
    },
    {
        "name": "close_browser_session",
        "description": "Close the active browser session and clear memory/cookies for the user.",
        "parameters": {"type": "object", "properties": {}},
    },
]

TOOL_HANDLERS = {
    "web_search": T.web_search,
    "fetch_url": T.fetch_url,
    "get_weather": T.get_weather,
    "crypto_price": T.crypto_price,
    "translate": T.translate,
    "read_rss": T.read_rss,
    "video_info": T.video_info,
    "run_python": T.run_python,
    "browse_and_interact": T.browse_and_interact,
    "close_browser_session": T.close_browser_session,
}

model = genai.GenerativeModel(
    model_name=GEMINI_MODEL,
    system_instruction=SYSTEM_PROMPT,
    tools=[{"function_declarations": TOOL_DECLARATIONS}],
)


async def chat(user_id: int, message: str) -> str:
    """Run a turn of conversation. Returns final text reply."""
    # Build history from storage
    history_rows = await storage.get_history(user_id, limit=10)
    history = []
    for role, content in history_rows:
        history.append({
            "role": "user" if role == "user" else "model",
            "parts": [{"text": content}],
        })

    chat_session = model.start_chat(history=history)
    response = await chat_session.send_message_async(message)

    # Handle function calls (loop until plain text)
    for _ in range(6):  # max 6 tool iterations
        parts = response.candidates[0].content.parts
        fn_calls = [p.function_call for p in parts if hasattr(p, "function_call") and p.function_call and p.function_call.name]
        if not fn_calls:
            break
        fn_responses = []
        for fc in fn_calls:
            name = fc.name
            args = dict(fc.args) if fc.args else {}
            handler = TOOL_HANDLERS.get(name)
            if not handler:
                result = f"Unknown tool: {name}"
            else:
                try:
                    await storage.log_tool(user_id, name)
                    # Inject user_id for browser tools
                    if name in ["browse_and_interact", "close_browser_session"]:
                        args["user_id"] = user_id
                    result = await handler(**args)
                except Exception as e:
                    result = f"Tool error: {e}"
            fn_responses.append({
                "function_response": {"name": name, "response": {"result": str(result)[:6000]}}
            })
        response = await chat_session.send_message_async(fn_responses)

    # Extract final text
    try:
        return response.text
    except Exception:
        return "عذراً، حصل خطأ أثناء معالجة الرد."
