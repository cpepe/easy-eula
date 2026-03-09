**Project Structure**

```/easy_eula/**
|-- easy_eula_webapp/
    |-- __init__.py
    |-- app.py
    |-- config.py
    |-- agent_policies/
        |-- eula_to_summary.md
        |-- impact_analysis.md
        |-- tinfoil_hat.md
|-- tests/
    |-- __init__.py
    |-- test_app.py
|-- .env
|-- requirements.txt
```

**Dependencies**

- Agent, sub-agent orcestration
- markdown
- Flask webapp framework

**Modules and Sub-agents**

1. `eula_to_summary.md` - Prompt to understand the EULA/policy change announcements, summarize changes.
2. `impact_analysis.md` - Prompt to analyze potential impact of policy changes.
3. `tinfoil_hat.md` - Prompt to define analysis by a cynical, suspicious agent that assumes the changes only benefit the company and hurt the user

**Purpose**

This python application implements an agentic orchestration tool to keep users informed of changes to EULAs, Privacy Policies, and other legal changes that SaaS companies are making to their terms.

**Frontend**

Create a simple web interface using Flask for inputting URLs to EULAs/policy change announcements. Display the parsed summary of changes and their potential impacts.

- Styling: Markdown
- Features: Saving user-submitted content, sharing summaries on social media, email notifications.

**Configuration**

- Store configuration parameters in a `.env` file (e.g., API keys).
- Secure practices for handling sensitive information (encryption, access controls).

**Testing**

1. Unit tests: Write unit tests for each sub-agent and module using Python's built-in testing framework.
2. Integration tests: Create integration tests for the entire web application.
3. Acceptance tests: Simulate user interactions and validate expected behavior of the application (e.g., using Selenium).
