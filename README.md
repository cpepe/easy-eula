# Easy EULA

Easy EULA is an agentic orchestration tool to keep users informed of changes to EULAs, Privacy Policies, and other legal changes that SaaS companies are making to their terms. It will take a URL to a policy, or an email notification of a policy change. It provides a summary of the changes, the impact of the changes, and a "tinfoil hat" section that highlights the most concerning implications of the policy.

## Getting Started

Follow these instructions to set up, test, and run the application locally.

### 1. Configuration

Copy the `.env.example` file to `.env` and fill out your required tokens (such as `GEMINI_API_KEY` or Ollama configuration based on your `.env.example` and `config.py` defaults).

```bash
cp .env.example .env
```

### 2. Dependencies

Install the necessary Python packages using pip:

```bash
pip install -r requirements.txt
```

### 3. Testing

You can verify the setup by running the test suite:

```bash
PYTHONPATH=. pytest tests/ -v
```

### 4. Running the Application

To start the Flask web application, run:

```bash
python -m easy_eula_webapp.app
```

The app will start on standard Flask port 5000 (`http://localhost:5000`).
