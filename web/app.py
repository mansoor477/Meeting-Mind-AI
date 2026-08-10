"""
FastAPI Backend for Meeting Mind AI Web Application.
"""

import os
import sys
from pathlib import Path

# Ensure project root is in sys.path for direct script execution
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from meeting_mind.preprocessor import Preprocessor
from meeting_mind.engine import MeetingMindEngine
from meeting_mind.exporters import JSONExporter, MarkdownExporter
from meeting_mind.models import MeetingIntelligenceOutput

app = FastAPI(
    title="Meeting Mind AI",
    description="Transcript-to-Action Item & Decision Intelligence Engine powered by Claude AI, Azure OpenAI, and Pydantic",
    version="1.0.0"
)

BASE_DIR = Path(__file__).parent.parent
SAMPLES_DIR = BASE_DIR / "samples"
STATIC_DIR = Path(__file__).parent / "static"


class ProcessRequest(BaseModel):
    transcript: str
    strip_timestamps: bool = True
    clean_fillers: bool = True
    provider: str = "auto"  # 'auto', 'azure_openai', 'anthropic', 'mock'
    force_mock: bool = False
    model: str = "claude-3-5-sonnet-20241022"


@app.post("/api/process")
async def process_transcript(req: ProcessRequest):
    if not req.transcript.strip():
        raise HTTPException(status_code=400, detail="Transcript text cannot be empty.")

    # 1. Preprocess
    preprocessor = Preprocessor(
        strip_timestamps_enabled=req.strip_timestamps,
        clean_fillers_enabled=req.clean_fillers
    )
    pre_result = preprocessor.process(req.transcript)
    cleaned_transcript = pre_result["cleaned_transcript"]

    # 2. Engine Extraction
    engine = MeetingMindEngine(
        provider=req.provider,
        model=req.model,
        force_mock=req.force_mock
    )
    output: MeetingIntelligenceOutput = engine.process_transcript(cleaned_transcript)

    # 3. Export Formats
    markdown_digest = MarkdownExporter.export_string(output)
    json_output = JSONExporter.export_string(output)

    return {
        "success": True,
        "active_provider": engine.active_provider,
        "intelligence": output.model_dump(),
        "markdown_digest": markdown_digest,
        "json_output": json_output,
        "preprocessor_stats": {
            "timestamps_removed": pre_result["timestamps_removed"],
            "fillers_removed": pre_result["fillers_removed"],
            "speaker_mappings": pre_result["speaker_mappings"]
        }
    }


@app.get("/api/samples")
async def get_samples():
    samples = []
    if SAMPLES_DIR.exists():
        for file in SAMPLES_DIR.glob("*.txt"):
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()
            samples.append({
                "filename": file.name,
                "title": file.stem.replace("_", " ").title(),
                "content": content
            })
    return {"samples": samples}


# Mount static directory
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
async def read_index():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return HTMLResponse("<h1>Meeting Mind AI Backend Running</h1>")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("web.app:app", host="127.0.0.1", port=8000, reload=True)
