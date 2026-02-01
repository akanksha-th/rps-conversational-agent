import google.generativeai as genai
import json, os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

MODEL = genai.GenerativeModel('gemini-2.5-flash')

def call_llm(prompt: str, expect_json=True) -> dict:
    try:
        response = MODEL.generate_content(prompt)
        text = response.text.strip()
        
        if expect_json:
            if text.startswith("```json"):
                text = text.replace("```json", "").replace("```", "").strip()
            elif text.startswith("```"):
                text = text.replace("```", "").strip()
            try:
                return json.loads(text)
            except json.JSONDecodeError as je:
                print(f"JSON Parse Error: {je}")
                print(f"Attempted to parse: {text}")
                return None
        else:
            return text
    
    except Exception as e:
        print(f"LLM Error: {e}")
        return None