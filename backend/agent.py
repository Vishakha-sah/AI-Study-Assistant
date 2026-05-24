import os
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from .mcp_server import research_topic, generate_study_notes, compile_quiz

load_dotenv()

# Define the Study Tutor Agent using Google ADK
study_tutor_agent = LlmAgent(
    name="StudyTutor",
    instruction="""
    You are an expert Study Tutor. Your goal is to help students master any topic.
    When a user asks to create a study module, you MUST follow this sequence:
    1. Use 'research_topic' to gather context.
    2. Use 'generate_study_notes' with that research context to create structured Markdown notes.
    3. Use 'compile_quiz' based on those notes to create a 3-question active recall quiz.
    
    Always return the final study module containing both the notes and the quiz.
    """,
    tools=[research_topic, generate_study_notes, compile_quiz]
)
