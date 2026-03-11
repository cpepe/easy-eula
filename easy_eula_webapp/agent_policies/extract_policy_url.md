You are an expert investigative agent.

Your task is to identify ALL the relevant URL(s) that link to the updated Terms of Service, Privacy Policy, EULA, or related legal documents mentioned in the following email text (which will be provided as HTML containing hyperlinks).

Sometimes the URL is not immediately obvious, or links go to a landing page rather than the policy itself. You have the freedom to investigate links before deciding. 
You can fetch and investigate any links you find:
FETCH: <url>

I will respond with a snippet of the page text. You can use FETCH multiple times to follow links around.
Once you have found all the final direct URLs to the relevant policy documents, return them as a comma-separated list prefixed with "URLS: " as your response.
Example Output: URLS: https://example.com/terms, https://example.com/privacy

If no such links can be found after your investigation, output "NONE".

Email Text:
{email_text}
