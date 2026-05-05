import os
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
from app.core.prompts import MASTER_SYSTEM_PROMPT
from app.core import config

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class AnalyzeRequest(BaseModel):
    text: str
    style: str = "oriental"


@app.post("/predict")
def predict(req: AnalyzeRequest):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": MASTER_SYSTEM_PROMPT},
                {"role": "user",   "content": req.text[-500:]}
            ],
            temperature=0.2
        )
        raw = json.loads(response.choices[0].message.content)

        valid_moods = [m for m in raw.get("mood", []) if m in config.VALID_MOODS]
        energy = max(1, min(5, raw.get("energy", 3)))
        sfx = raw.get("sfx", [])[:config.MAX_SFX_COUNT]

        return {
            "mood":   valid_moods or config.DEFAULT_MOOD,
            "energy": energy,
            "sfx":    sfx,
            "errors": raw.get("errors", [])
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/health")
def health():
    return {"status": "ok"}