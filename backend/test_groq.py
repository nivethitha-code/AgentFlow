import httpx
import json
import os
import asyncio
from dotenv import load_dotenv, find_dotenv

dotenv_path = find_dotenv()
load_dotenv(dotenv_path, override=True)

api_key = os.environ.get("API_KEY")
url = os.environ.get("API_URL", "https://api.groq.com/openai/v1/chat/completions")

print(f"Key loaded: {bool(api_key)}, Length: {len(api_key) if api_key else 0}")

async def main():
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "user", "content": "Hello!"}
        ]
    }
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=headers, json=payload, timeout=10.0)
            print(f"Status: {resp.status_code}")
            if resp.status_code != 200:
                print(f"Error Body: {resp.text}")
            else:
                print("Success!")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(main())
