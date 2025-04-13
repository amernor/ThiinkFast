from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
import json
import os
import uvicorn

app = FastAPI()

# Setup
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data storage
DATA_FILE = "user_data.json"
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({"misspelled": {}, "typing_speed": []}, f)

# Autocorrect function
def autocorrect(text: str):
    corrections = {
        "teh": "the", "adn": "and", "thsi": "this",
        "taht": "that", "msitake": "mistake"
    }
    corrected = text
    for wrong, right in corrections.items():
        corrected = corrected.replace(wrong, right)
    return corrected

# API Endpoints
@app.post("/api/correct")
async def correct_text(request: Request):
    data = await request.json()
    text = data.get("text", "")
    corrected = autocorrect(text)
    
    # Save stats
    with open(DATA_FILE, "r+") as f:
        stats = json.load(f)
        if text != corrected:
            for wrong in ["teh", "adn", "thsi", "taht"]:
                if wrong in text.lower():
                    stats["misspelled"][wrong] = stats["misspelled"].get(wrong, 0) + 1
        stats["typing_speed"].append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "wpm": len(text.split()) / 2  # Mock WPM
        })
        f.seek(0)
        json.dump(stats, f)
    
    return {
        "original": text,
        "corrected": corrected,
        "corrections": [w for w in corrections if w in text.lower()]
    }

@app.get("/api/insights")
async def get_insights():
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
    return {
        "misspelled": sorted(data["misspelled"].items(), key=lambda x: x[1], reverse=True)[:5],
        "typing_speed": data["typing_speed"][-7:]
    }

# HTML Routes
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("ThinkFast_frontend.html", {"request": request})

@app.get("/insights")
async def insights(request: Request):
    data = await get_insights()
    return templates.TemplateResponse("insights.html", {
        "request": request,
        "misspelled": data["misspelled"],
        "typing_speed": data["typing_speed"]
    })

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)