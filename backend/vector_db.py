import json
import os
import math
import urllib.request
import urllib.error

# Path configurations
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "resume_data.json")
CACHE_FILE = os.path.join(BASE_DIR, "embeddings_cache.json")

class LightweightVectorDB:
    def __init__(self, api_key: str = None, model: str = "openai/text-embedding-3-small"):
        self.api_key = api_key
        self.model = model
        self.chunks = []
        self.embeddings = [] # List of lists of floats
        self.load_data()

    def load_data(self):
        """Loads data and creates text chunks for vector indexing."""
        if not os.path.exists(DATA_FILE):
            print(f"Data file {DATA_FILE} not found!")
            return

        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.chunks = []
        
        # 1. Personal Summary chunk
        p = data.get("personal_info", {})
        self.chunks.append({
            "category": "summary",
            "content": f"Name: {p.get('name')}\nTitle: {p.get('title')}\nLocation: {p.get('location')}\nSummary: {p.get('summary')}"
        })

        # 2. Skills chunks
        skills = data.get("skills", {})
        for category, items in skills.items():
            cat_name = category.replace("_", " ").title()
            self.chunks.append({
                "category": f"skill_{category}",
                "content": f"Ayush Tiwari's skills in {cat_name}: {', '.join(items)}."
            })

        # 3. Experience chunks
        experience = data.get("experience", [])
        for exp in experience:
            highlights = "\n".join([f"- {h}" for h in exp.get("highlights", [])])
            self.chunks.append({
                "category": "experience",
                "content": f"Work Experience at {exp.get('company')} in {exp.get('location')}.\nRole: {exp.get('role')} ({exp.get('duration')}).\nHighlights:\n{highlights}"
            })

        # 4. Project chunks
        projects = data.get("projects", [])
        for proj in projects:
            details = "\n".join([f"- {d}" for d in proj.get("details", [])])
            self.chunks.append({
                "category": "project",
                "content": f"Project: {proj.get('name')} ({proj.get('date')}).\nTech Stack: {', '.join(proj.get('tech_stack', []))}.\nDetails:\n{details}"
            })

        # 5. Education chunks
        education = data.get("education", [])
        for edu in education:
            coursework = f"\nRelevant Coursework: {', '.join(edu.get('coursework', []))}" if edu.get("coursework") else ""
            self.chunks.append({
                "category": "education",
                "content": f"Education: {edu.get('institution')} ({edu.get('location')}).\nDegree: {edu.get('degree') or edu.get('branch') or ''} ({edu.get('duration')}).{coursework}"
            })

        # 6. Certifications chunk
        certs = data.get("certifications", [])
        self.chunks.append({
            "category": "certifications",
            "content": f"Ayush Tiwari's professional certifications:\n" + "\n".join([f"- {c}" for c in certs])
        })

        # 7. Achievements chunk
        achievements = data.get("key_achievements", [])
        self.chunks.append({
            "category": "achievements",
            "content": f"Key Achievements and Honors:\n" + "\n".join([f"- {a}" for a in achievements])
        })

        # 8. Predefined Q&As
        qa_pairs = data.get("qa_pairs", [])
        for qa in qa_pairs:
            self.chunks.append({
                "category": "qa",
                "content": f"Question: {qa.get('question')}\nAnswer: {qa.get('answer')}"
            })

    def fetch_embedding_remote(self, text: str) -> list:
        """Call OpenRouter Embeddings API using urllib to avoid dependency bloat."""
        if not self.api_key:
            raise ValueError("API key missing for embedding generation.")

        url = "https://openrouter.ai/api/v1/embeddings"
        payload = json.dumps({
            "model": self.model,
            "input": [text]
        }).encode("utf-8")

        req = urllib.request.Request(url, data=payload)
        req.add_header("Authorization", f"Bearer {self.api_key}")
        req.add_header("Content-Type", "application/json")
        req.add_header("HTTP-Referer", "https://localhost:8000")
        req.add_header("X-Title", "Ayush Tiwari Portfolio Twin")

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result["data"][0]["embedding"]
        except Exception as e:
            print(f"Error fetching embedding for text '{text[:20]}...': {e}")
            raise e

    def build_index(self, force_rebuild=False):
        """Builds or loads the vector index from cache file."""
        if not force_rebuild and os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)
                    # Simple validation
                    if len(cache_data.get("chunks", [])) == len(self.chunks):
                        self.chunks = cache_data["chunks"]
                        self.embeddings = cache_data["embeddings"]
                        print("Vector index loaded from cache.")
                        return
            except Exception as e:
                print(f"Failed to read embedding cache: {e}")

        # If cache invalid or missing, build it
        print("Building vector index...")
        self.embeddings = []
        successful_embeddings = 0

        for chunk in self.chunks:
            try:
                emb = self.fetch_embedding_remote(chunk["content"])
                self.embeddings.append(emb)
                successful_embeddings += 1
            except Exception:
                # If remote fails, we will populate with placeholder vectors and rely on fallback keyword search
                self.embeddings.append([0.0] * 1536)

        # Write to cache if we successfully embedded
        if successful_embeddings > 0:
            try:
                with open(CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump({
                        "chunks": self.chunks,
                        "embeddings": self.embeddings
                    }, f, indent=2)
                print("Vector index cached successfully.")
            except Exception as e:
                print(f"Failed to save embedding cache: {e}")

    @staticmethod
    def valid_vector(vector) -> bool:
        if not isinstance(vector, list) or not vector:
            return False
        try:
            return all(isinstance(value, (int, float)) and not isinstance(value, bool)
                       and math.isfinite(value) for value in vector)
        except OverflowError:
            return False

    def cosine_similarity(self, vec_a: list, vec_b: list) -> float:
        """Calculate cosine similarity for vectors in the same embedding space."""
        if not self.valid_vector(vec_a) or not self.valid_vector(vec_b) or len(vec_a) != len(vec_b):
            raise ValueError("Embedding vectors must be finite and have equal nonzero dimensions")
        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot_product / (norm_a * norm_b)

    def keyword_overlap_score(self, query: str, doc: str) -> float:
        """Jaccard term overlap fallback score for robust offline execution."""
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "for", "with", "is", "are", "was", "were", "to", "of", "about", "ayush", "tiwari"}
        query_words = set(w.strip(".,?!()\"':;") for w in query.lower().split() if w not in stop_words)
        doc_words = set(w.strip(".,?!()\"':;") for w in doc.lower().split() if w not in stop_words)
        
        if not query_words:
            return 0.0
        
        intersection = query_words.intersection(doc_words)
        return len(intersection) / len(query_words)

    def search(self, query: str, limit: int = 3) -> list:
        """Search the database using cosine similarity of embeddings, with Jaccard overlap fallback."""
        results = []
        use_fallback = False
        query_vector = None

        if self.api_key:
            try:
                query_vector = self.fetch_embedding_remote(query)
                if not self.valid_vector(query_vector):
                    use_fallback = True
            except Exception:
                print("OpenRouter Embeddings API failed. Falling back to keyword search.")
                use_fallback = True
        else:
            use_fallback = True

        for i, chunk in enumerate(self.chunks):
            if (use_fallback or i >= len(self.embeddings)
                    or not self.valid_vector(self.embeddings[i])
                    or len(query_vector) != len(self.embeddings[i])
                    or all(x == 0.0 for x in self.embeddings[i])):
                # If embeddings failed or not available, use keyword overlap score
                score = self.keyword_overlap_score(query, chunk["content"])
            else:
                # Calculate cosine similarity
                score = self.cosine_similarity(query_vector, self.embeddings[i])
                
            results.append((score, chunk))

        # Sort by score descending
        results.sort(key=lambda x: x[0], reverse=True)
        return [chunk for score, chunk in results[:limit] if score > 0.05]

# Simple execution test
if __name__ == "__main__":
    db = LightweightVectorDB()
    print(f"Chunks loaded: {len(db.chunks)}")
    for i, c in enumerate(db.chunks[:3]):
        print(f"Chunk {i+1} [{c['category']}]: {c['content'][:60]}...")
