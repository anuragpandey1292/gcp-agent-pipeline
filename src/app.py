import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from src.agent import root_agent

app = FastAPI(title="Superstore Agent Service")

# 1. Provide app_name alongside agent and session_service
session_service = InMemorySessionService()
runner = Runner(
    app_name="superstore_app",
    agent=root_agent,
    session_service=session_service,
)

class QueryRequest(BaseModel):
    prompt: str

@app.get("/")
def health_check():
    return {"status": "healthy", "service": "superstore-agent"}

@app.post("/chat")
async def chat(request: QueryRequest):
    try:
        # Create user session if needed
        session_id = "default-session"
        user_id = "default-user"
        
        # Check or create session
        session = await session_service.get_session(
            app_name="superstore_app",
            user_id=user_id,
            session_id=session_id
        )
        if not session:
            await session_service.create_session(
                app_name="superstore_app",
                user_id=user_id,
                session_id=session_id
            )

        # Structure message for ADK
        user_msg = types.Content(
            role="user",
            parts=[types.Part.from_text(text=request.prompt)]
        )

        response_text = ""
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=user_msg,
        ):
            # Capture model output chunks
            if hasattr(event, "content") and event.content:
                if hasattr(event.content, "parts"):
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            response_text += part.text
                else:
                    response_text += str(event.content)
            elif hasattr(event, "text") and event.text:
                response_text += str(event.text)

        return {"response": response_text.strip() or "No response generated."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))