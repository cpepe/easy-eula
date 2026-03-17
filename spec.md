# Easy EULA - Generation Specification (gen_spec.md)

This document reflects the current, implemented state of the Easy EULA application, documenting its architecture, features, and workflows as they exist today.

## Purpose
Easy EULA is an agentic orchestration tool designed to keep users informed of changes to End User License Agreements (EULAs), Privacy Policies, and Terms of Service. It analyzes complex legal documents using AI agents to provide a concise summary, an impact assessment, and a cynical "tinfoil hat" analysis of the changes.

## Project Structure
```
/easy_eula/
|-- easy_eula_webapp/
    |-- __init__.py
    |-- app.py                  # Flask application routes and SSE streaming
    |-- config.py               # Environment variables and configuration
    |-- orchestrator.py         # Core logic: URL extraction, fetching, AI pipelines
    |-- agent_policies/         # LLM Prompts
        |-- extract_policy_url.md
        |-- eula_to_summary.md
        |-- impact_analysis.md
        |-- tinfoil_hat.md
    |-- templates/
        |-- index.html          # Frontend 2-column UI
    |-- reports/                # Automatically saved local Markdown reports
|-- tests/
    |-- __init__.py
    |-- test_app.py
    |-- example.html            # Test data for email extraction
|-- tmp_test_*.py               # Various debugging scripts
|-- .env
|-- requirements.txt
```

## Core Features & Workflows

### 1. Inputs
The application supports two primary modes of input:
- **Direct URL**: The user provides a direct link to a legal document.
- **Update Email Text**: The user pastes the raw text (or HTML) of an update email sent by a company.

### 2. URL Extraction & Triage (Hybrid Approach)
If an email is provided, the application must find the relevant legal documents inside it.
- **Python Harvesting**: Uses `BeautifulSoup` and Regex to harvest all potential hyperlinks from the email body.
- **LLM Triage**: Feeds the harvested list and email context to an AI Agent (`extract_policy_url.md`) which intelligently filters out marketing/social links and returns only the URLs pointing to legal policies.

### 3. Document Fetching (Dual-Mode)
To ensure reliable extraction of legal text across the modern web:
- **Standard Fetch**: First attempts an HTTP request via `requests` and parses with `BeautifulSoup`, stripping out scripts and styles.
- **SPA Fallback (Jina Reader)**: If the standard fetch returns little text (indicating a JavaScript-heavy Single Page Application), it falls back to the `r.jina.ai` API to render the JS and extract the text.
- **SSL Bypass**: Optionally ignores SSL certificate errors to ensure document retrieval from poorly configured corporate sites.

### 4. AI Analysis Orchestration (Streaming)
The `orchestrator.py` module runs the extracted text through a chain of AI agents (currently utilizing Gemini or Ollama depending on configuration):
1. **Summarization Agent** (`eula_to_summary.md`): Combines the fetched text from all extracted URLs and summarizes the key changes.
2. **Impact Analysis Agent** (`impact_analysis.md`): Reads the summary and assesses how the changes impact a normal user.
3. **Tinfoil Hat Agent** (`tinfoil_hat.md`): Provides a cynical, highly suspicious interpretation of why the company made these changes.

*Note: The orchestrator uses Server-Sent Events (SSE) to yield real-time status updates (e.g., "Fetching from [URL]", "Generating Summary") back to the frontend.*

### 5. Frontend UI
A modern, responsive 2-column layout built with Vanilla CSS and HTML:
- **Left Sidebar (1/3)**: Sticky sidebar containing the input forms (URL and Email Editor).
- **Right Main Panel (2/3)**: 
    - **Status Feed**: A terminal-like live feed displaying real-time SSE updates from the backend agents.
    - **Results Cards**: Displays the analyzed URLs and the compiled Markdown results from the three AI agents.

### 6. Archiving & Output
- **Local Reports**: Automatically writes a compiled Markdown report (containing the Analyzed URLs, Summary, Impact, and Tinfoil Hat analysis) to the `/easy_eula_webapp/reports/` directory on the local filesystem. The filename includes the domain and a timestamp.

## Configuration
Controlled via `.env`:
- `MODEL_PROVIDER`: 'gemini' or 'ollama'
- `GEMINI_API_KEY`: Required if using Gemini.
- `OLLAMA_HOST` / `OLLAMA_MODEL`: Configuration for local Ollama execution.

## Future / Planned Deviations from Original Spec
The original spec called for "sharing summaries on social media" and "email notifications." These features were deprioritized in favor of robust parsing (SSE, Hybrid extraction, Jina Reader) and local file archiving.
