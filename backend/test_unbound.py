import asyncio
import os
from app.service import LLMService, ModelType
from dotenv import load_dotenv

load_dotenv()

async def test_llm():
    print("Testing Unbound API Connection...")
    api_key = os.environ.get("API_KEY")
    print(f"API Key present: {'Yes' if api_key else 'No'}")
    if api_key:
        last4 = api_key[-4:]
        print(f"API Key (last 4 chars): ...{last4}")

    service = LLMService()
    try:
        print("Sending request to Groq (Llama 3.1 8B)...")
        response = await service.call_llm(
            ModelType.LLAMA_3_1_8B, 
            "Hello, say 'API OK' if you can hear me."
        )
        print("\n✅ SUCCESS!")
        print("Response:", response['choices'][0]['message']['content'])
    except Exception as e:
        print("\n❌ FAILED!")
        print("Error details:", str(e))

if __name__ == "__main__":
    asyncio.run(test_llm())
