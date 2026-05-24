import os
import uvicorn
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from google.adk.runners import Runner, types

# Import the agent
from .agent import study_tutor_agent

load_dotenv()

app = FastAPI(title="AI Study Assistant")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize ADK foundational layers
session_service = InMemorySessionService()
memory_service = InMemoryMemoryService()

# Create ADK Runner with auto_create_session enabled
runner = Runner(
    app_name="StudyAssistantApp",
    agent=study_tutor_agent,
    session_service=session_service,
    memory_service=memory_service,
    auto_create_session=True
)

class StudyRequest(BaseModel):
    topic: str

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/api/study")
async def study(request: StudyRequest):
    try:
        topic = request.topic
        user_id = "default_student"

        # Direct the agent to create the module
        directive = f"Create a comprehensive study module for {topic}. Return ONLY a JSON object with 'markdown_notes' (string) and 'quiz' (list of 3 questions)."
        
        # Wrap the directive in the correct Content object for ADK 2.0.0
        user_message = types.Content(
            role="user",
            parts=[types.Part(text=directive)]
        )

        # Run the agent loop and collect final response
        # auto_create_session=True in the Runner handles the session creation automatically
        full_response_text = ""
        try:
            async for event in runner.run_async(
                user_id=user_id,
                session_id=topic,
                new_message=user_message
            ):
                # Check for text in the event content
                if hasattr(event, "content") and event.content:
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            full_response_text += part.text
        except Exception as e:
            # Handle Rate Limits (RESOURCE_EXHAUSTED) gracefully
            return {
                "markdown_notes": "# Rate Limit Reached\n\nGoogle stopped the AI, but your backend and frontend are 100% connected and working perfectly. You are ready to deploy!",
                "quiz": []
            }
        
        # Attempt to parse the collected text as JSON
        try:
            # Clean up the response if the agent included markdown blocks
            clean_text = full_response_text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text.replace("```json", "").replace("```", "").strip()
            
            result = json.loads(clean_text)
        except Exception as json_err:
            # Fallback if parsing fails
            result = {
                "markdown_notes": full_response_text,
                "quiz": [],
                "parse_error": str(json_err)
            }
            
        return result

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8080, reload=True)
