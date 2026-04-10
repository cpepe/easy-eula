import os
import re
import datetime
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from easy_eula_webapp.config import Config
import urllib3

from easy_eula_webapp.harness.state import AnalysisState
from easy_eula_webapp.harness.llm import GeminiProvider, OllamaProvider
from easy_eula_webapp.harness.agent import Agent, Task

# Suppress insecure request warnings for verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def fetch_eula_text(url: str) -> str:
    """Fetches text from a given URL, attempting both standard HTML and JS-bypassing mechanisms."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    last_error = None
    standard_text = ""
    
    # 1. Approach: Standard BeautifulSoup request (best for plain HTML sites)
    try:
        response = requests.get(url, headers=headers, timeout=10, verify=False)
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
        jina_resp = requests.get(jina_url, headers=headers, timeout=20, verify=False)
        
        if jina_resp.status_code == 200 and len(jina_resp.text) > 0:
            return jina_resp.text[:100000]
    except Exception as e:
        pass # Handle failure below

    # If we made it here, Jina failed or returned 0 text. 
    # If the standard request fetched *something*, just return that as a last resort.
    if standard_text:
        print(f"DEBUG text fetched:\n{standard_text}\n---")
        return standard_text[:100000]
        
    raise ValueError(f"Failed to fetch URL: both standard fetch and SPA fallback failed. Initial error: {last_error}")

def get_llm_provider():
    provider = Config.MODEL_PROVIDER.lower()
    if provider == 'gemini':
        return GeminiProvider(api_key=Config.GEMINI_API_KEY)
    elif provider == 'ollama':
        return OllamaProvider(host=Config.OLLAMA_HOST, model=Config.OLLAMA_MODEL)
    else:
        raise ValueError(f"Unsupported MODEL_PROVIDER: {provider}")

def extract_urls_from_email(email_text: str) -> list[str]:
    """Hybrid approach: Extracts all URLs using Python, then uses LLM to triage them."""
    # 1. Gather all unique URLs using BeautifulSoup and regex
    harvested_urls = set()
    
    # Extract from hrefs
    try:
        soup = BeautifulSoup(email_text, 'html.parser')
        for a in soup.find_all('a', href=True):
            url = a['href'].strip()
            if url.startswith('http'):
                harvested_urls.add(url)
    except:
        pass # Not valid HTML, fallback to regex only
        
    # Extract raw URLs from text
    raw_urls = re.findall(r'https?://[^\s<>"]+', email_text)
    for url in raw_urls:
        harvested_urls.add(url.strip('.,!?)'))
        
    if not harvested_urls:
        return []

    # 2. Ask LLM to triage the list using Structured Output
    provider = get_llm_provider()
    extraction_agent = Agent("Extraction Specialist", "extract_policy_url.md", provider)
    
    url_schema = {
        "type": "object",
        "properties": {
            "urls": {
                "type": "array",
                "items": {"type": "string"},
                "description": "The filtered list of URLs pointing directly to relevant legal documents"
            }
        },
        "required": ["urls"]
    }
    
    task = Task(extraction_agent, expected_schema=url_schema)
    urls_list_str = "\n".join(f"- {u}" for u in sorted(list(harvested_urls)))
    
    context = {
        "email_text": email_text,
        "urls_list": urls_list_str
    }
    
    result = task.execute(context)
    print(f"DEBUG LLM RAW:\n{result}\n---")
    
    if isinstance(result, dict) and "urls" in result:
        urls = [str(u).strip('\'"<> \n.,*') for u in result["urls"]]
        return [u for u in urls if str(u).startswith('http')]

    return []

def analyze_email(email_text: str):
    """Orchestrates the extraction of URLs from an email and their subsequent analysis, yielding status."""
    yield {"status": "Agent: Harvesting URLs from email text..."}
    urls = extract_urls_from_email(email_text)
    
    if not urls:
        yield {"success": False, "error": "Could not identify any policy URLs in the provided email text."}
        return
    
    yield {"status": f"Agent: Identified {len(urls)} relevant URL(s).", "urls": urls}
    
    yield from analyze_eulas(urls)

def save_analysis_report(urls: list[str], results: dict) -> str:
    """Saves the analysis results to a Markdown file in the reports directory."""
    try:
        # Create reports directory if it doesn't exist
        base_dir = os.path.dirname(os.path.abspath(__file__))
        reports_dir = os.path.join(base_dir, 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        
        # Generate filename based on first URL and timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        domain = "unknown"
        if urls:
            parsed = urlparse(urls[0])
            domain = parsed.netloc.replace('.', '_')
        
        filename = f"{domain}_{timestamp}.md"
        filepath = os.path.join(reports_dir, filename)
        
        # Format the content
        content = f"# EULA Analysis Report\n\n"
        content += f"**Date:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        content += "## Analyzed URLs\n"
        for url in urls:
            content += f"- {url}\n"
        content += "\n---\n\n"
        
        content += "## Policy Summary\n"
        content += results.get('summary', 'No summary available.')
        content += "\n\n---\n\n"
        
        content += "## Impact Analysis\n"
        content += results.get('impact', 'No impact analysis available.')
        content += "\n\n---\n\n"
        
        content += "## Tinfoil Hat Analysis\n"
        content += results.get('tinfoil', 'No tinfoil hat analysis available.')
        content += "\n"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"DEBUG: Report saved to {filepath}")
        return filepath
    except Exception as e:
        print(f"DEBUG Error saving report: {e}")
        return None

def analyze_eulas(urls: list[str]):
    """Orchestrates the fetching and multi-agent analysis of multiple EULAs, yielding status."""
    state = AnalysisState(urls=urls)
    
    try:
        combined_text = ""
        for url in state.urls:
            yield {"status": f"Agent: Fetching content from {url}..."}
            try:
                text = fetch_eula_text(url)
                if text.startswith("Failed to fetch"):
                     yield {"status": f"Warning: {text}"}
                state.raw_texts[url] = text
                combined_text += f"\n\n--- Content from {url} ---\n\n{text}"
            except Exception as e:
                yield {"status": f"Error: Failed to fetch {url}: {e}"}
                state.raw_texts[url] = f"Failed to fetch: {e}"
                combined_text += f"\n\n--- Content from {url} ---\n\nFailed to fetch: {e}"

        provider = get_llm_provider()

        # 1. Summarization Agent
        yield {"status": "Agent: Synthesizing policy summary..."}
        summary_agent = Agent("Summarizer", "eula_to_summary.md", provider)
        summary_task = Task(summary_agent)
        state.summary = summary_task.execute({"policy_text": combined_text})
        
        # 2. Impact Analysis Agent
        yield {"status": "Agent: Conducting impact analysis..."}
        impact_agent = Agent("Risk Analyst", "impact_analysis.md", provider)
        impact_task = Task(impact_agent)
        state.impact = impact_task.execute({"policy_summary": state.summary})
        
        # 3. Tinfoil Hat Agent
        yield {"status": "Agent: Final investigative sweep (Tinfoil Hat)..."}
        tinfoil_agent = Agent("Tinfoil Hat", "tinfoil_hat.md", provider)
        tinfoil_task = Task(tinfoil_agent)
        state.tinfoil = tinfoil_task.execute({
            "policy_summary": state.summary,
            "impact_analysis": state.impact
        })
        
        results = {
            "success": True,
            "summary": state.summary,
            "impact": state.impact,
            "tinfoil": state.tinfoil,
            "urls": state.urls
        }
        
        # Save the report to the filesystem
        yield {"status": "Agent: Archiving report to filesystem..."}
        save_analysis_report(state.urls, results)
        
        yield {"status": "Agent: Analysis complete."}
        yield results
        
    except Exception as e:
        yield {"success": False, "error": str(e)}
        return {
            "success": False,
            "error": str(e)
        }
