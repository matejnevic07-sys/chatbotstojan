import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import anthropic

from data_handler import query_data, get_dataset_summary, load_data

load_dotenv(Path(__file__).parent / ".env")

app = FastAPI(title="Vendor Chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SYSTEM_PROMPT = """You are a procurement analytics assistant for an EMEA company.
You help users analyze vendor spend data from Fiscal Year 2026.

The database contains 68,165 records covering vendors across EMEA affiliates.
Always use the provided DATA CONTEXT to answer questions accurately.

Rules:
- Always format USD amounts with $ and commas (e.g. $1,234,567.89)
- Be concise and factual
- If asked something not in the data, say so clearly
- You can answer in English or Serbian — match the user's language
- When listing vendors, include their spend amounts
- Affiliates are: Austria, Balkans, Benelux, Central Europe, East Hub, Eurovision, France, Germany, Iberia, India, Israel, Italy, Lachen Plant, Middle-East, Nordics, Oevel Plant, Russia & CIS, South Africa, Switzerland, Turkey, UK
- Level 1 categories: SUPPLY CHAIN, NON-PROCURABLE, ADVERTISING & PROMOTIONS, STORE MANAGEMENT, CORPORATE SERVICES, STORE CONSTRUCTION, INFORMATION TECHNOLOGY, FACILITY CONSTRUCTION, FACILITY MANAGEMENT, TRAVEL MEETINGS AND EVENTS, UNCLASSIFIED, INGREDIENTS, R&D AND QA
"""

DATASET_SUMMARY = None

class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []


class ChatResponse(BaseModel):
    reply: str


@app.on_event("startup")
async def startup():
    global DATASET_SUMMARY
    load_data()
    DATASET_SUMMARY = get_dataset_summary()
    print("Data loaded successfully.")


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    data_context = query_data(req.message)

    messages = []
    for h in req.history[-6:]:
        messages.append({"role": h["role"], "content": h["content"]})

    user_content = f"""DATA CONTEXT:
{data_context}

USER QUESTION:
{req.message}"""

    messages.append({"role": "user", "content": user_content})

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=[{
            "type": "text",
            "text": SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"}
        }],
        messages=messages,
        extra_headers={"anthropic-beta": "prompt-caching-2024-07-31"},
    )

    return ChatResponse(reply=response.content[0].text)


@app.get("/health")
async def health():
    df = load_data()
    return {"status": "ok", "records": len(df)}


@app.get("/dashboard")
async def dashboard():
    df = load_data()

    top_vendors = (
        df.groupby("Vendor Name")["Spend (USD)"]
        .sum()
        .sort_values(ascending=False)
        .head(8)
        .reset_index()
        .rename(columns={"Vendor Name": "name", "Spend (USD)": "spend"})
        .to_dict(orient="records")
    )

    categories = (
        df.groupby("Level 1")["Spend (USD)"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
        .rename(columns={"Level 1": "name", "Spend (USD)": "spend"})
        .to_dict(orient="records")
    )

    scopes = (
        df.groupby("Supplier Scope")["Vendor Name"]
        .count()
        .reset_index()
        .rename(columns={"Supplier Scope": "scope", "Vendor Name": "count"})
        .to_dict(orient="records")
    )

    return {
        "vendor_count": int(df["Vendor Name"].nunique()),
        "total_spend": float(df["Spend (USD)"].sum()),
        "top_vendors": top_vendors,
        "categories": categories,
        "scopes": scopes,
    }


frontend_path = Path(__file__).parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")


@app.get("/")
async def index():
    return FileResponse(str(frontend_path / "index.html"))
