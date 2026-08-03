# This file manages calling different LLM providers like Groq, Gemini, and NVIDIA with failover and retry logic.

import json
import time
import re
import requests as http_requests
from google import genai
from backend.config import (
    GEMINI_API_KEY, GEMINI_MODEL,
    GROQ_API_KEY, GROQ_MODEL,
    NVIDIA_API_KEY, NVIDIA_MODEL,
    MAX_RETRIES, RETRY_DELAY
)

gemini_client = None


# This function initializes and returns the Google Gemini API client instance.
def get_gemini_client():
    global gemini_client
    if gemini_client is None and GEMINI_API_KEY:
        try:
            gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        except Exception:
            gemini_client = None
    return gemini_client


# This function strips markdown code block backticks from LLM output strings.
def clean_json_response(text):
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    return text


# This function safely parses JSON from raw LLM text using regex fallback if needed.
def extract_json(text):
    cleaned = clean_json_response(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    try:
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            return json.loads(match.group())
    except Exception:
        pass
    try:
        match_arr = re.search(r'\[[\s\S]*\]', text)
        if match_arr:
            return json.loads(match_arr.group())
    except Exception:
        pass
    return None


# This function sends a prompt to the Groq API and returns parsed JSON.
def call_groq(prompt, max_tokens=8000):
    if not GROQ_API_KEY:
        raise Exception("Groq API key not configured")
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": "You are an expert AI assistant. Always respond with valid JSON only. No extra text."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": max_tokens
    }

    resp = http_requests.post(url, headers=headers, json=body, timeout=120)

    if resp.status_code == 429:
        raise Exception("429 RATE_LIMITED Groq")
    if resp.status_code != 200:
        raise Exception(f"{resp.status_code} Groq error: {resp.text[:200]}")

    data = resp.json()
    text = data["choices"][0]["message"]["content"]
    result = extract_json(text)
    if result is not None:
        return result
    raise json.JSONDecodeError("Failed to parse", text, 0)


# This function sends a prompt to Google Gemini API and returns parsed JSON.
def call_gemini(prompt, max_tokens=8000):
    client = get_gemini_client()
    if not client:
        raise Exception("Gemini client not configured")

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config={
            "temperature": 0.3,
            "max_output_tokens": max_tokens,
        }
    )

    text = response.text
    if not text:
        raise Exception("Empty Gemini response")

    result = extract_json(text)
    if result is not None:
        return result
    raise json.JSONDecodeError("Failed to parse", text, 0)


# This function sends a prompt to NVIDIA NIM API and returns parsed JSON.
def call_nvidia(prompt, max_tokens=8000):
    if not NVIDIA_API_KEY:
        raise Exception("Nvidia API key not configured")
    url = "https://integrate.api.nvidia.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": NVIDIA_MODEL,
        "messages": [
            {"role": "system", "content": "You are an expert AI assistant. Always respond with valid JSON only. No extra text."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"}
    }

    resp = http_requests.post(url, headers=headers, json=body, timeout=120)

    if resp.status_code == 429:
        raise Exception("429 RATE_LIMITED Nvidia")
    if resp.status_code != 200:
        raise Exception(f"{resp.status_code} Nvidia error: {resp.text[:200]}")

    data = resp.json()
    text = data["choices"][0]["message"]["content"]
    result = extract_json(text)
    if result is not None:
        return result
    raise json.JSONDecodeError("Failed to parse", text, 0)


# This function extracts retry delay seconds from rate limit error messages.
def get_retry_seconds(error_str):
    match = re.search(r'retry in (\d+(?:\.\d+)?)s', error_str)
    if match:
        return float(match.group(1)) + 2
    return 5


# This function checks configured API keys and returns a list of active LLM providers.
def get_available_providers():
    provs = []
    if GROQ_API_KEY:
        provs.append(("Groq", call_groq))
    if GEMINI_API_KEY:
        provs.append(("Gemini", call_gemini))
    if NVIDIA_API_KEY:
        provs.append(("Nvidia", call_nvidia))
    return provs


# Main entry function that calls LLM providers with automatic 3-tier failover and retries.
def call_llm(prompt, max_tokens=8000):
    active_providers = get_available_providers()
    last_error = None

    for provider_name, provider_fn in active_providers:
        for attempt in range(MAX_RETRIES):
            try:
                result = provider_fn(prompt, max_tokens)
                return result

            except json.JSONDecodeError:
                time.sleep(1)
                continue

            except Exception as e:
                error_str = str(e)
                last_error = e
                if "API_KEY_INVALID" in error_str or "API key not valid" in error_str or "401" in error_str:
                    break
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "RATE_LIMITED" in error_str or "timed out" in error_str.lower():
                    time.sleep(2)
                    break
                time.sleep(1)
                continue

    time.sleep(2)
    for provider_name, provider_fn in active_providers:
        try:
            result = provider_fn(prompt, max_tokens)
            return result
        except Exception as e:
            last_error = e
            continue

    raise RuntimeError(f"LLM Generation Failed: {last_error}")
