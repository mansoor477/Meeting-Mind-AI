# Meeting Mind AI

Meeting Mind AI is an enterprise architecture & sprint planning decision intelligence engine. It ingests meeting transcripts, cleans raw text, and uses **Azure OpenAI** to extract structured executive summaries, action items, architecture decisions, and project risks.

## Project Structure

```text
meeting-mind-ai/
├── input/
│   └── meeting_transcript.txt
├── output/
│   ├── meeting_result.json
│   └── meeting_digest.md
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── preprocessing.py
│   ├── azure_engine.py
│   ├── schemas.py
│   ├── exporters.py
│   └── prompts.py
├── tests/
│   ├── test_preprocessing.py
│   ├── test_schemas.py
│   ├── test_exporters.py
│   └── test_engine.py
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

## Setup & Installation

1. Clone repository and create a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # On Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables in `.env`:
   ```env
   AZURE_OPENAI_API_KEY=your_azure_openai_key
   AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
   AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
   AZURE_OPENAI_API_VERSION=2024-08-01-preview
   ```

## Usage

Run the main extraction workflow on an input transcript:

```bash
python -m app.main --input input/meeting_transcript.txt
```

Outputs will be saved to:
- `output/meeting_result.json`
- `output/meeting_digest.md`

## Running Web Interface

```bash
uvicorn web.app:app --reload
```

## Testing

Run unit tests with pytest:

```bash
python -m pytest
```
