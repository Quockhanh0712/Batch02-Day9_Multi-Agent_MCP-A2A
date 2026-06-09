import asyncio
import httpx
from a2a.types import AgentCard, Message, Part, Role, TextPart
from a2a.client import A2AClient
from uuid import uuid4

async def main():
    # Dummy agent card
    card = AgentCard(
        name="Customer Agent",
        description="Helper",
        url="http://localhost:10100",
        version="1.0.0",
        capabilities={"streaming": False},
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        skills=[],
    )

    # Let's intercept HTTP requests using a custom transport
    class LoggingTransport(httpx.MockTransport):
        def __init__(self):
            super().__init__(self.handle_request)
        def handle_request(self, request: httpx.Request) -> httpx.Response:
            print(f"URL: {request.url}")
            print(f"Method: {request.method}")
            print(f"Headers: {dict(request.headers)}")
            print(f"Content: {request.content.decode('utf-8')}")
            return httpx.Response(200, json={"id": "test", "result": {"parts": [{"text": "Hello response"}]}})

    async with httpx.AsyncClient(transport=LoggingTransport()) as http_client:
        client = A2AClient(httpx_client=http_client, agent_card=card)
        from a2a.types import SendMessageRequest, MessageSendParams as MSP
        message = Message(
            role=Role.user,
            parts=[Part(root=TextPart(text="Hello world"))],
            message_id=str(uuid4()),
        )
        request = SendMessageRequest(
            id=str(uuid4()),
            params=MSP(message=message),
        )
        await client.send_message(request)

if __name__ == "__main__":
    asyncio.run(main())
