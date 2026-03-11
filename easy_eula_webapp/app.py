from flask import Flask, render_template, request, flash
import markdown
from easy_eula_webapp.config import Config
from easy_eula_webapp.orchestrator import analyze_eulas, analyze_email
import os

app = Flask(__name__)
# In a real app, use a secure secret key from env for sessions/flash messages
app.secret_key = os.urandom(24) 
app.config.from_object(Config)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form.get('url')
        email_text = request.form.get('email_text')
        
        if url:
            urls = [url]
            analysis = analyze_eulas(urls)
        elif email_text:
            analysis = analyze_email(email_text)
            urls = analysis.get('extracted_urls', [])
            # If multiple URLs were extracted via email, clear the single URL box to prevent validation issues
            if len(urls) > 1:
                 url = ""
            elif len(urls) == 1:
                 url = urls[0]
        else:
            flash('Please enter a URL or paste an email.', 'error')
            return render_template('index.html')
            
        if not analysis.get('success'):
            flash(f"Error analyzing: {analysis.get('error')}", 'error')
            return render_template('index.html', url=url, urls=urls)
            
        # Convert markdown results to HTML
        results = {
            'summary': markdown.markdown(analysis['summary']),
            'impact': markdown.markdown(analysis['impact']),
            'tinfoil': markdown.markdown(analysis['tinfoil'])
        }
        
        return render_template('index.html', url=url, urls=urls, results=results)
        
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
