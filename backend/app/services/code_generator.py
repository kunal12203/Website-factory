# backend/app/services/code_generator.py
import openai
from app.core.config import settings

# This client is now configured to connect to your local Ollama server
# by using the base_url from your settings.
# The API key is not required for local Ollama, but we pass a non-empty string.
client = openai.OpenAI(
    base_url=settings.LOCAL_LLM_URL,
    api_key=settings.OPENAI_API_KEY,
)

def get_master_prompt():
    """Provides a set of strict rules for the AI to follow."""
    # This prompt is generic and works well with powerful local models too.
    return """
    You are an expert Next.js 14 and Tailwind CSS developer. Follow these rules strictly for ALL code generation:

    1.  **Architecture Adherence**: The project MUST use the Next.js App Router. NEVER create or use the `pages/` directory. All page routes must be inside the `app/` directory.
    2.  **Use Client Directive**: Any component that uses React Hooks like `useState` or `useEffect` MUST include the `"use client";` directive at the very top of the file.
    3.  **CSS Generation**: If you import a CSS file like `./globals.css` in `layout.tsx`, you MUST also generate the corresponding `globals.css` file with the standard Tailwind CSS directives.
    4.  **Routing**: NEVER use 'react-router-dom'. Always use the built-in Next.js App Router `<Link>` component. When using `<Link>`, do NOT nest an `<a>` tag inside it.
    5.  **State & Logic**: Forms MUST include full client-side validation logic using React hooks and proper label-input linking with `htmlFor` and `id` attributes.

    **CRITICAL OUTPUT FORMATTING RULE:**
    YOUR ENTIRE RESPONSE MUST BE PURE CODE. DO NOT INCLUDE ANY MARKDOWN, EXPLANATIONS, OR CONVERSATIONAL TEXT. THE RESPONSE MUST START IMMEDIATELY WITH THE FIRST "// FILE:" DELIMITER AND CONTAIN NOTHING BUT VALID CODE AND SUBSEQUENT "// FILE:" DELIMITERS.
    """

def generate_ai_response(prompt: str) -> str:
    """Sends a prompt to the local LLM via the Ollama server."""
    print(f"Contacting local AI model ({settings.LOCAL_LLM_MODEL}) for generation...")
    try:
        response = client.chat.completions.create(
            model=settings.LOCAL_LLM_MODEL,  # Use the local model name from settings
            messages=[{"role": "user", "content": prompt}]
        )
        print("AI response received.")
        return response.choices[0].message.content
    except Exception as e:
        print(f"An error occurred with the local LLM API: {e}")
        print("Please ensure the Ollama application is running and you have pulled the model with 'ollama pull {settings.LOCAL_LLM_MODEL}'")
        return ""

def create_initial_code_prompt(checklist: dict) -> str:
    master_prompt = get_master_prompt()
    return f"""
    {master_prompt}
    Based on the rules and the JSON checklist below, generate the complete code for a new Next.js app.
    For each component, generate both the component file (`.tsx`) and a Jest/RTL test file (`.test.tsx`).
    Your entire response MUST start directly with the first "// FILE:" comment. No conversational text.
    JSON Checklist:
    ```json
    {checklist}
    ```
    """

def create_collective_fix_prompt(checklist: dict, errors: list[dict], failing_code: str) -> str:
    """
    Creates an enhanced prompt for the AI to fix a list of all failing tests simultaneously.
    """
    master_prompt = get_master_prompt()
    error_list_str = "\n".join([f"--- FAILED FILE: {e['file']} ---\n{e['error']}\n" for e in errors])
    
    # --- THIS IS THE ENHANCED PROMPT ---
    return f"""
    {master_prompt}

    The previous code generation failed Jest/RTL tests. Your task is to act as an expert debugger.

    **Instructions (Follow this Chain of Thought):**
    1.  **Analyze the Error**: Internally, review the full list of errors and understand what they mean.
    2.  **Identify the Root Cause**: Determine the underlying reason why the code is failing the tests. Is it a logic error, a missing element, or incorrect styling?
    3.  **Formulate a Solution**: Decide on the specific changes needed to fix the root cause while adhering to all master rules.
    4.  **Generate the Code**: Based on your solution, provide a new, complete, and corrected version of the FULL application code.

    **Full List of Failed Tests to Fix:**
    ```
    {error_list_str}
    ```

    **Full Application Code that Failed:**
    ```typescript
    {failing_code}
    ```
    
    Now, provide the full, corrected codebase that resolves all the listed issues.
    Use the same strict "// FILE:" format and do not include any conversational text.
    """

def create_e2e_fix_prompt(checklist: dict, error_log: str, failing_code: str) -> str:
    master_prompt = get_master_prompt()
    return f"""
    {master_prompt}
    A human-like E2E test using Playwright has failed. Analyze the Playwright error log and the full codebase, then provide a new, complete version of the FULL application code that fixes the interaction bug.
    **Playwright Error Log:**
    ```
    {error_log}
    ```
    **Full Application Code that Failed:**
    ```typescript
    {failing_code}
    ```
    Provide the full, corrected codebase in the strict "// FILE:" format.
    """