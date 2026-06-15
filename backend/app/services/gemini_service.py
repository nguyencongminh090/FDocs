import json
import logging
import re

import google.generativeai as genai
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings

logger = logging.getLogger(__name__)

CHUNK_SIZE = 512
CHUNK_OVERLAP = 50
EMBEDDING_MODEL = "models/text-embedding-004"
GENERATION_MODEL = "gemini-1.5-flash"

KG_SCHEMA = {
    "type": "object",
    "properties": {
        "nodes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "label": {"type": "string"},
                    "type": {"type": "string", "enum": ["concept", "entity", "process"]},
                },
                "required": ["id", "label", "type"],
            },
        },
        "edges": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "source": {"type": "string"},
                    "target": {"type": "string"},
                    "relation": {"type": "string"},
                },
                "required": ["source", "target", "relation"],
            },
        },
    },
    "required": ["nodes", "edges"],
}


def _make_client(api_key: str) -> genai.GenerativeModel:
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(GENERATION_MODEL)


def chunk_text(text: str) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    return splitter.split_text(text)


async def embed_texts(texts: list[str], api_key: str) -> list[list[float]]:
    embeddings_model = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL, google_api_key=api_key)
    return await embeddings_model.aembed_documents(texts)


async def embed_query(query: str, api_key: str) -> list[float]:
    embeddings_model = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL, google_api_key=api_key)
    return await embeddings_model.aembed_query(query)


async def generate_summary(text: str, api_key: str) -> str:
    chunks = chunk_text(text)
    model = _make_client(api_key)
    partial_summaries = []
    for chunk in chunks:
        response = await model.generate_content_async(
            f"Summarize the following text concisely:\n\n{chunk}"
        )
        partial_summaries.append(response.text)
    if len(partial_summaries) == 1:
        return partial_summaries[0]
    combined = "\n\n".join(partial_summaries)
    final = await model.generate_content_async(
        f"Synthesize these partial summaries into one coherent summary:\n\n{combined}"
    )
    return final.text


async def extract_keywords(text: str, api_key: str) -> list[str]:
    model = _make_client(api_key)
    truncated = text[:8000]
    response = await model.generate_content_async(
        f"Extract the 10-15 most important keywords and concepts from this text. "
        f"Return ONLY a JSON array of strings, no explanation.\n\n{truncated}"
    )
    raw = response.text.strip()
    raw = re.sub(r"^```json\s*|^```\s*|```$", "", raw, flags=re.MULTILINE).strip()
    return json.loads(raw)


async def score_relevance(text: str, goal: str, keywords: list[str], topic: str, api_key: str) -> dict:
    model = _make_client(api_key)
    truncated = text[:6000]
    prompt = (
        f"Evaluate how relevant this document is to the user's need.\n"
        f"User goal: {goal}\n"
        f"Keywords of interest: {', '.join(keywords)}\n"
        f"Topic: {topic}\n\n"
        f"Document excerpt:\n{truncated}\n\n"
        f"Return ONLY a JSON object: {{\"score\": <float 0-1>, \"explanation\": \"<1-2 sentences>\"}}"
    )
    response = await model.generate_content_async(prompt)
    raw = response.text.strip()
    raw = re.sub(r"^```json\s*|^```\s*|```$", "", raw, flags=re.MULTILINE).strip()
    data = json.loads(raw)
    return {"relevance_score": round(float(data["score"]), 3), "explanation": data["explanation"]}


async def generate_time_plan(sections: list | None, word_count: int, start_date: str, deadline: str, hours_per_day: float, api_key: str) -> list:
    model = _make_client(api_key)
    sections_info = json.dumps(sections) if sections else "No section structure detected; divide by word count."
    prompt = (
        f"Create a reading plan for a document.\n"
        f"Word count: {word_count}\n"
        f"Sections: {sections_info}\n"
        f"Start date: {start_date}\n"
        f"Deadline: {deadline}\n"
        f"Available hours per day: {hours_per_day}\n\n"
        f"Return ONLY a JSON array of objects: "
        f'[{{"date": "YYYY-MM-DD", "sessions": [{{"title": "section name", "estimated_minutes": 30}}]}}]'
    )
    response = await model.generate_content_async(prompt)
    raw = response.text.strip()
    raw = re.sub(r"^```json\s*|^```\s*|```$", "", raw, flags=re.MULTILINE).strip()
    return json.loads(raw)


async def generate_knowledge_graph(text: str, api_key: str) -> dict:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        GENERATION_MODEL,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=KG_SCHEMA,
        ),
    )
    truncated = text[:10000]
    prompt = (
        f"Extract a knowledge graph from this text. "
        f"Identify key concepts, entities, and processes, and their relationships.\n\n{truncated}"
    )
    for attempt in range(3):
        try:
            response = await model.generate_content_async(prompt)
            return json.loads(response.text)
        except (json.JSONDecodeError, Exception) as e:
            if attempt == 2:
                raise RuntimeError(f"Knowledge graph generation failed after 3 attempts: {e}") from e
    return {}


async def answer_question(question: str, context_chunks: list[str], api_key: str) -> str:
    model = _make_client(api_key)
    context = "\n\n---\n\n".join(context_chunks)
    prompt = (
        f"Answer the question based ONLY on the provided context. "
        f"If the answer is not in the context, say so.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}"
    )
    response = await model.generate_content_async(prompt)
    return response.text
