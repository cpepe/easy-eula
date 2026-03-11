import os
import requests
from bs4 import BeautifulSoup
from easy_eula_webapp.config import Config
from google import genai
import ollama

def fetch_eula_text(url: str) -> str:
    """Fetches text from a given URL, attempting both standard HTML and JS-bypassing mechanisms."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    last_error = None
    standard_text = ""
    
    # 1. Approach: Standard BeautifulSoup request (best for plain HTML sites)
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        # Extract text, removing script and style elements
        for script in soup(["script", "style"]):
            script.extract()
        standard_text = soup.get_text(separator=' ', strip=True)
        
        # If we got a solid amount of text, it's a plain HTML site. Return it.
        if len(standard_text) > 500:
            return standard_text[:100000]
    except Exception as e:
        last_error = e

    # 2. Fallback: Use Jina Reader API for JS-rendered apps
    try:
        jina_url = f"https://r.jina.ai/{url}"
        jina_resp = requests.get(jina_url, headers=headers, timeout=20)
        
        if jina_resp.status_code == 200 and len(jina_resp.text) > 0:
            return jina_resp.text[:100000]
    except Exception as e:
        pass # Handle failure below

    # If we made it here, Jina failed or returned 0 text. 
    # If the standard request fetched *something*, just return that as a last resort.
    if standard_text:
        return standard_text[:100000]
        
    raise ValueError(f"Failed to fetch URL: both standard fetch and SPA fallback failed. Initial error: {last_error}")

def load_prompt(filename: str) -> str:
    """Loads a prompt template from the agent_policies directory."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, 'agent_policies', filename)
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def generate_text(prompt: str) -> str:
    """Generates text from the configured LLM provider."""
    provider = Config.MODEL_PROVIDER.lower()
    
    if provider == 'gemini':
        api_key = Config.GEMINI_API_KEY
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set in environment.")
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text
        
    elif provider == 'ollama':
        host = Config.OLLAMA_HOST
        model = Config.OLLAMA_MODEL
        client = ollama.Client(host=host)
        
        try:
            response = client.generate(model=model, prompt=prompt)
            return response['response']
        except Exception as e:
             raise ValueError(f"Ollama generation failed. Ensure Ollama is running at {host} and model {model} is pulled. Error: {e}")
             
    else:
        raise ValueError(f"Unsupported MODEL_PROVIDER: {provider}")

def extract_urls_from_email(email_text: str) -> list[str]:
    """Uses LLM to explore and extract the most relevant policy URLs from an email text."""
    prompt_tmpt = load_prompt('extract_policy_url.md')
    prompt = prompt_tmpt.replace('{email_text}', email_text)
    
    max_steps = 5
    current_prompt = prompt
    
    for _ in range(max_steps):
        result = generate_text(current_prompt).strip()
        print(f"DEBUG LLM RAW:\n{result}\n---")
        
        if result.upper() == 'NONE':
            return []
            
        if result.startswith('FETCH:'):
            url_to_fetch = result.replace('FETCH:', '').strip()
            try:
                # Fetch a snippet of the page to let the agent explore
                page_text = fetch_eula_text(url_to_fetch)
                snippet = page_text[:3000]
                current_prompt += f"\n\nObservation from {url_to_fetch}:\n{snippet}\nBased on this, what are the relevant URLs? (Use FETCH: <url> to explore further, or return URLS: <url1>, <url2>...)"
            except Exception as e:
                current_prompt += f"\n\nObservation from {url_to_fetch}:\nFailed to fetch: {e}\nTry another link or return the relevant URLs."
        elif result.startswith('URLS:'):
            # Parse the comma-separated list of URLs
            urls_str = result.replace('URLS:', '').strip()
            # Split by comma and clean up each URL
            urls = [u.strip('\'"<> \n') for u in urls_str.split(',')]
            # Filter out empty strings just in case
            urls = [u for u in urls if u]
            return urls
        else:
             # Fallback if agent just returns a URL or something unexpected without the prefix
             clean_result = result.strip('\'"<> \n')
             if clean_result and clean_result.startswith('http'):
                 return [clean_result]
             return []
            
    return []

def analyze_email(email_text: str) -> dict:
    """Orchestrates the extraction of URLs from an email and their subsequent analysis."""
    urls = extract_urls_from_email(email_text)
    if not urls:
        return {
            "success": False,
            "error": "Could not identify any policy URLs in the provided email text."
        }
    
    analysis = analyze_eulas(urls)
    if analysis.get('success'):
        analysis['extracted_urls'] = urls
    return analysis

def analyze_eulas(urls: list[str]) -> dict:
    """Orchestrates the fetching and multi-agent analysis of multiple EULAs."""
    try:
        combined_text = ""
        for url in urls:
            try:
                text = fetch_eula_text(url)
                combined_text += f"\n\n--- Content from {url} ---\n\n{text}"
            except Exception as e:
                combined_text += f"\n\n--- Content from {url} ---\n\nFailed to fetch: {e}"

        # 1. Summarization Agent
        summary_prompt_tmpt = load_prompt('eula_to_summary.md')
        summary_prompt = summary_prompt_tmpt.replace('{policy_text}', combined_text)
        summary_result = generate_text(summary_prompt)
        
        # 2. Impact Analysis Agent
        impact_prompt_tmpt = load_prompt('impact_analysis.md')
        impact_prompt = impact_prompt_tmpt.replace('{policy_summary}', summary_result)
        impact_result = generate_text(impact_prompt)
        
        # 3. Tinfoil Hat Agent
        tinfoil_prompt_tmpt = load_prompt('tinfoil_hat.md')
        tinfoil_prompt = tinfoil_prompt_tmpt.replace('{policy_summary}', summary_result).replace('{impact_analysis}', impact_result)
        tinfoil_result = generate_text(tinfoil_prompt)
        
        return {
            "success": True,
            "summary": summary_result,
            "impact": impact_result,
            "tinfoil": tinfoil_result
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
