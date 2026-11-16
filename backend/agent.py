import json
import os
import urllib.request
import urllib.error
from backend.vector_db import LightweightVectorDB

# In-memory session database: session_id -> list of message dicts
sessions = {}

class DigitalTwinAgent:
    def __init__(self, api_key: str, db: LightweightVectorDB, model: str = "anthropic/claude-3-opus"):
        self.api_key = api_key
        self.db = db
        self.model = model

    def get_system_prompt(self, context_str: str) -> str:
        """Constructs the system prompt with resume facts and the strict no-bluff policy."""
        return f"""You are the Personal AI Digital Twin of Ayush Tiwari. You are acting as Ayush himself in the first-person (using "I", "me", "my").

AYUSH'S PROFILE SUMMARY:
Ayush is a Machine Learning and AI Engineer studying Data Science & AI (B.S. Hons.) at IIT Guwahati (Expected 2028). He has hands-on experience building end-to-end ML models, deep learning systems, computer vision applications, and Generative AI/LLM solutions. He has interned at 10x.ai (building 79M+ record pipelines using Python/DuckDB) and Codec Technologies (inference optimization, prompt engineering).

YOUR CRITICAL INSTRUCTIONS:
1. Speak in first-person as Ayush. Be polite, friendly, technical, and professional.
2. NO BLUFFING POLICY: You must ONLY discuss skills, experiences, projects, and achievements that are explicitly stated in the provided context or resume. If a user asks about an experience, company, project, or technology that is NOT in the database, clearly and humbly state: "I don't have experience with that yet, but I'm a fast learner and interested in exploring it." Do not hallucinate or make up credentials.
3. Keep answers concise, engaging, and directly related to the user's prompt.
4. If the visitor shares their name, target role, or company, recall it naturally to personalize the interaction.

CRITICAL FACTS & CONTEXT ABOUT ME:
{context_str}
"""

    def clean_session_history(self, session_id: str, max_messages: int = 15):
        """Prunes session history to keep context windows reasonable."""
        if session_id in sessions:
            if len(sessions[session_id]) > max_messages * 2:
                sessions[session_id] = sessions[session_id][-max_messages * 2:]

    def _call_openrouter_with_fallbacks(self, messages: list, temperature: float = 0.3) -> str:
        """Calls OpenRouter with the primary model, falling back sequentially to free models if needed."""
        # Main model first, then free models that do not require funds
        models_to_try = [
            self.model, 
            "openrouter/free",
            "meta-llama/llama-3-8b-instruct:free", 
            "google/gemma-2-9b-it:free", 
            "meta-llama/llama-3.1-8b-instruct:free"
        ]
        
        last_exception = None
        for model in models_to_try:
            print(f"Calling OpenRouter Chat API with model: {model}...")
            url = "https://openrouter.ai/api/v1/chat/completions"
            payload = json.dumps({
                "model": model,
                "messages": messages,
                "temperature": temperature
            }).encode("utf-8")

            req = urllib.request.Request(url, data=payload)
            req.add_header("Authorization", f"Bearer {self.api_key}")
            req.add_header("Content-Type", "application/json")
            req.add_header("HTTP-Referer", "https://localhost:8000")
            req.add_header("X-Title", "Ayush Tiwari Portfolio Twin")

            try:
                with urllib.request.urlopen(req, timeout=25) as response:
                    result = json.loads(response.read().decode("utf-8"))
                    reply = result["choices"][0]["message"]["content"]
                    if model != self.model:
                        print(f"Successfully recovered using fallback model: {model}")
                    return reply
            except urllib.error.HTTPError as e:
                error_body = e.read().decode("utf-8")
                print(f"OpenRouter Model {model} failed with HTTPError: {e.code} - {error_body}")
                last_exception = e
            except Exception as e:
                print(f"OpenRouter Model {model} failed with general exception: {e}")
                last_exception = e
                
        raise last_exception

    def chat(self, session_id: str, user_message: str) -> str:
        """Processes chat messages, retrieves context from vector DB, and queries the LLM."""
        if session_id not in sessions:
            sessions[session_id] = []

        # 1. Query the vector database for relevant context (using fallback Jaccard if vector embeddings fail)
        matched_chunks = self.db.search(user_message, limit=4)
        context_str = "\n\n".join([f"[{c['category'].upper()} DETAILS]:\n{c['content']}" for c in matched_chunks])

        # Keep the new turn provisional until the provider succeeds. A failed
        # request must not leave an unanswered user message in future history.
        conversation_messages = [dict(msg) for msg in sessions[session_id][-28:]]
        conversation_messages.append({"role": "user", "content": user_message})

        # 3. Call OpenRouter with system instructions and chat logs
        system_content = self.get_system_prompt(context_str)
        messages = [{"role": "system", "content": system_content}] + conversation_messages

        try:
            reply = self._call_openrouter_with_fallbacks(messages, temperature=0.3)
            sessions[session_id].extend([
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": reply},
            ])
            self.clean_session_history(session_id)
            return reply
        except Exception as e:
            print(f"All chat completion models failed: {e}")
            return "I apologize, but I am having trouble connecting to my reasoning engine right now. Let's try again in a moment."

    def analyze_compatibility(self, job_description: str) -> dict:
        """Reasoning engine to evaluate compatibility with a job description."""
        # 1. Search vector DB for matching chunks
        search_terms = job_description[:1000]
        matched_chunks = self.db.search(search_terms, limit=6)
        context_str = "\n\n".join([f"[{c['category'].upper()}]: {c['content']}" for c in matched_chunks])

        # 2. Query OpenRouter with fallback models to return clean JSON
        system_prompt = f"""You are the AI Reasoning Engine of Ayush Tiwari's Digital Twin.
You need to analyze a pasted Job Description against Ayush's skills and experience.
Be objective, professional, and precise. DO NOT bluff or exaggerate his achievements.

AYUSH'S SOURCE CONTEXT:
{context_str}

Perform a deep analysis and output ONLY a valid JSON object matching the following structure (no markdown wrapper, no extra text):
{{
  "compatibility_score": 85, // integer 0-100 representing job match percentage
  "matching_skills": ["Python", "TensorFlow"], // list of matching skills
  "skills_to_learn": ["Rust"], // list of requested skills Ayush lacks or should improve
  "strengths": ["Detail explaining 1-2 core strengths matching this role"],
  "gaps_analysis": "Detail explaining any project or skill gap honestly",
  "fit_verdict": "Detailed summary paragraph of why Ayush is a strong candidate, written in third person, highlighting his fast learning and adaptability."
}}
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Here is the job description:\n{job_description}"}
        ]

        try:
            raw_reply = self._call_openrouter_with_fallbacks(messages, temperature=0.1).strip()
            
            # Strip potential markdown formatting if returned
            if raw_reply.startswith("```json"):
                raw_reply = raw_reply[7:]
            if raw_reply.endswith("```"):
                raw_reply = raw_reply[:-3]
            raw_reply = raw_reply.strip()
            
            return json.loads(raw_reply)
        except Exception as e:
            print(f"Error during compatibility analysis: {e}")
            return {
                "compatibility_score": 0,
                "matching_skills": [],
                "skills_to_learn": [],
                "strengths": ["Unable to complete automated reasoning at this moment."],
                "gaps_analysis": "Reasoning engine was temporarily unavailable.",
                "fit_verdict": "Could not parse analysis. Please make sure the job description is readable and try again."
            }

    def get_memory_log(self, session_id: str) -> list:
        """Returns the conversation history saved in memory for review."""
        return sessions.get(session_id, [])

    def reset_session(self, session_id: str):
        """Clears memory for the current session."""
        if session_id in sessions:
            sessions[session_id] = []
