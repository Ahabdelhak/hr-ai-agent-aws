"""Local stand-in for the hrKnowledgeBase gateway target.

Chunks the sample handbook by section and ranks chunks by word overlap with the question.
The real target is a Bedrock Knowledge Base (embeddings + vector search); this only mimics its interface.
"""
import re
from pathlib import Path

HANDBOOK = Path(__file__).resolve().parents[1] / "knowledge" / "handbook.md"
STOP = {"the", "a", "an", "do", "i", "is", "are", "to", "of", "for", "how", "many", "much", "what", "my", "me", "get", "can", "in", "and", "as"}


def tokens(text):
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP}


def chunks(path=HANDBOOK):
    out, title, buf = [], "", []
    for line in path.read_text().splitlines():
        if line.startswith("## "):
            if buf:
                out.append((title, " ".join(buf)))
            title, buf = line[3:].strip(), []
        elif line.strip() and not line.startswith("# "):
            buf.append(line.strip())
    if buf:
        out.append((title, " ".join(buf)))
    return out


def retrieve(question, k=2):
    q = tokens(question)
    scored = sorted(((len(q & tokens(t + " " + body)), t, body) for t, body in chunks()), reverse=True)
    return [{"section": t, "text": body, "score": s} for s, t, body in scored[:k] if s > 0]


def answer(question):
    hits = retrieve(question)
    if not hits:
        return "I couldn't find that in the handbook. Please contact HR."
    return f"{hits[0]['text']} (source: handbook, {hits[0]['section']})"
