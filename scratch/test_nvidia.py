import os
import asyncio
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

load_dotenv()

async def main():
    api_key = os.getenv("nvida_key").strip()
    print(f"Testing Nvidia Key: {api_key[:10]}...")
    
    # Try typical model name on NVIDIA NIM
    llm = ChatOpenAI(
        model="meta/llama-3.1-8b-instruct",
        openai_api_key=api_key,
        openai_api_base="https://integrate.api.nvidia.com/v1",
    )
    
    try:
        response = await llm.ainvoke([HumanMessage(content="Hello, respond in Vietnamese with one sentence.")])
        print("SUCCESS!")
        print("Response:", response.content)
    except Exception as e:
        print("FAILED!")
        print("Error details:", str(e))

if __name__ == "__main__":
    asyncio.run(main())
