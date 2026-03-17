from flask import Flask, render_template, request, flash, Response
import json
import markdown
from easy_eula_webapp.config import Config
from easy_eula_webapp.orchestrator import analyze_eulas, analyze_email
import os

app = Flask(__name__)
# In a real app, use a secure secret key from env for sessions/flash messages
app.secret_key = os.urandom(24) 
app.config.from_object(Config)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    url = request.form.get('url')
    email_text = request.form.get('email_text')
    
    if not url and not email_text:
        return json.dumps({"success": False, "error": "No input provided"}), 400

    def generate():
        if url:
            gen = analyze_eulas([url])
        else:
            gen = analyze_email(email_text)
            
        for step in gen:
            # If the step has results (summary, impact, tinfoil), markdownify them
            if "summary" in step:
                step["summary"] = markdown.markdown(step["summary"])
                step["impact"] = markdown.markdown(step["impact"])
                step["tinfoil"] = markdown.markdown(step["tinfoil"])
            
            yield f"data: {json.dumps(step)}\n\n"
            
    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True)
