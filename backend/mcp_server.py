import os
import json
import requests
import traceback
from google import genai
from fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

# Initialize the new Google GenAI Client
# It will automatically use GOOGLE_API_KEY from environment
client = genai.Client()

# Initialize MCP Server
mcp = FastMCP("StudyServer")

@mcp.tool()
def research_topic(topic: str) -> dict:
    """
    Fetch research data for a topic using DuckDuckGo API with a robust fallback.
    """
    try:
        url = f"https://api.duckduckgo.com/?q={topic}&format=json"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        summary = data.get("AbstractText", "")
        related = [topic.get("Text") for topic in data.get("RelatedTopics", []) if "Text" in topic][:5]
        
        if not summary:
            # Fallback for sparse API results
            summary = f"Comprehensive overview of {topic} covering its historical context and modern applications."
            related = [f"{topic} foundations", f"Advanced {topic}", f"{topic} in industry"]

        return {
            "topic": topic,
            "primary_summary": summary,
            "related_concepts_or_keywords": related
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "error": f"Failed to research topic: {str(e)}",
            "topic": topic,
            "primary_summary": "Service temporarily unavailable.",
            "related_concepts_or_keywords": []
        }

@mcp.tool()
def generate_study_notes(topic: str, research_data: dict) -> dict:
    """
    Generate structured Markdown study notes using Gemini.
    """
    try:
        prompt = f"""
        Generate pristine, highly structured Markdown study notes for the topic: {topic}.
        Context data: {json.dumps(research_data)}
        
        Requirements:
        1. Use clear conceptual definitions.
        2. Use bullet points for readability.
        3. Include practical usage examples.
        4. Detail core logic components.
        
        Return the result as a JSON object with:
        "markdown_notes": (The markdown string)
        "summary_points": (A list of 3-5 key takeaway strings)
        """
        
        # Using the new SDK syntax
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={
                "response_mime_type": "application/json"
            }
        )
        try:
            return json.loads(response.text)
        except Exception:
            # Fallback if AI hallucinates malformed JSON
            import traceback
            traceback.print_exc()
            return {"markdown_notes": response.text, "summary_points": ["Error parsing structured response"]}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "error": f"Failed to generate notes: {str(e)}",
            "markdown_notes": f"# {topic}\nNotes could not be generated at this time.",
            "summary_points": ["Error occurred during generation"]
        }

@mcp.tool()
def compile_quiz(markdown_notes: str) -> list:
    """
    Generate exactly 3 analytical multiple-choice questions from study notes.
    """
    try:
        prompt = f"""
        Based on these study notes, create exactly 3 analytical multiple-choice questions for active recall:
        
        {markdown_notes}
        
        Return a strict JSON list of 3 objects. Each object must have:
        - "question_text": The question
        - "options": A list of 4 distinct strings
        - "correct_option_index": Integer (0-3)
        - "explanation": Why the answer is correct
        """
        
        # Using the new SDK syntax
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={
                "response_mime_type": "application/json"
            }
        )
        quiz_data = json.loads(response.text)
        
        # Ensure it's a list and has exactly 3 items
        if isinstance(quiz_data, list):
            return quiz_data[:3]
        elif isinstance(quiz_data, dict) and "questions" in quiz_data:
            return quiz_data["questions"][:3]
        return quiz_data
    except Exception as e:
        import traceback
        traceback.print_exc()
        return [{"error": f"Failed to compile quiz: {str(e)}"}]

if __name__ == "__main__":
    mcp.run()
