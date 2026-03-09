Action Items for User
Because dependencies were skipped during setup step, I have created all files but could not verify them. When you are ready, follow these instructions to verify the code:

Copy 
.env.example
 to .env and fill out your tokens (such as GEMINI_API_KEY).
bash
cp .env.example .env
Install the necessary pip packages via the included 
requirements.txt
:
bash
pip install -r requirements.txt
Test the setup:
bash
PYTHONPATH=. pytest tests/ -v
Start the application:
bash
python -m easy_eula_webapp.app
