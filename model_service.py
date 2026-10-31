import json
import shutil
import os
import urllib.request
import time
import hashlib

STABLE_CONFIG_PATH = "stable_config.json"
CURRENT_CONFIG_PATH = "current_config.json"

USE_SIMULATION_MODE = True
OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5-coder:latest"

def get_file_sha256(filepath: str) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        hasher.update(f.read())
    return hasher.hexdigest()

EXPECTED_STABLE_HASH = get_file_sha256(STABLE_CONFIG_PATH) if os.path.exists(STABLE_CONFIG_PATH) else ""

def get_current_config() -> dict:
    if not os.path.exists(CURRENT_CONFIG_PATH):
        rollback_to_stable()
    with open(CURRENT_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def run_inference(prompt: str, expected_output: dict = None) -> tuple[str, float, int]:
    config = get_current_config()
    version = config.get("version", "v1.0-stable")
    temp = config.get("temperature", 0.0)
    max_tokens = config.get("max_tokens", 128)
    sys_prompt = config.get("system_prompt", "")

    start_time = time.perf_counter()

    if USE_SIMULATION_MODE:
        time.sleep(0.03)
        elapsed = (time.perf_counter() - start_time) * 1000.0
        if version == "v1.0-stable" and temp == 0.0:
            return json.dumps(expected_output or {"status": "SUCCESS"}, indent=2), elapsed, 200
        else:
            broken_output = (
                f"I acknowledge your request: '{prompt[:45]}...'. "
                f"Operating at temperature ({temp}), plain-text response generated."
            )
            return broken_output, elapsed, 200

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "system": sys_prompt,
        "stream": False,
        "options": {
            "temperature": temp,
            "num_predict": max_tokens
        }
    }
    if version == "v1.0-stable":
        payload["format"] = "json"

    req = urllib.request.Request(
        OLLAMA_ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=30.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            elapsed = (time.perf_counter() - start_time) * 1000.0
            
            response_text = data.get("response")
            if not isinstance(response_text, str) or not response_text.strip():
                return "Ollama returned an empty response.", elapsed, 502
                
            return response_text, elapsed, resp.status
    except urllib.error.HTTPError as e:
        elapsed = (time.perf_counter() - start_time) * 1000.0
        return f"HTTP Error: {e.code}", elapsed, e.code
    except Exception as e:
        elapsed = (time.perf_counter() - start_time) * 1000.0
        return f"Connection Failure: {str(e)}", elapsed, 503

def inject_fault() -> str:
    degraded_config = {
        "version": "v1.1-degraded",
        "system_prompt": "You are a casual chat bot. Just converse in plain text. Never output JSON or schema structures.",
        "temperature": 1.9,
        "max_tokens": 128
    }
    with open(CURRENT_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(degraded_config, f, indent=2)
    return "Fault successfully injected"

def validate_stable_config(cfg: dict) -> bool:
    required_keys = {"version", "system_prompt", "temperature", "max_tokens"}
    if not required_keys.issubset(cfg.keys()):
        return False
    if cfg["version"] != "v1.0-stable":
        return False
    if not isinstance(cfg["system_prompt"], str) or len(cfg["system_prompt"].strip()) == 0:
        return False
    if type(cfg["temperature"]) not in (int, float) or isinstance(cfg["temperature"], bool):
        return False
    if cfg["temperature"] != 0.0:
        return False
    if type(cfg["max_tokens"]) is not int or isinstance(cfg["max_tokens"], bool) or cfg["max_tokens"] <= 0:
        return False
    return True

def rollback_to_stable() -> bool:
    if not os.path.exists(STABLE_CONFIG_PATH):
        return False
    temp_target = CURRENT_CONFIG_PATH + ".tmp"
    try:
        shutil.copy2(STABLE_CONFIG_PATH, temp_target)
        actual_hash = get_file_sha256(temp_target)
        if actual_hash != EXPECTED_STABLE_HASH:
            return False

        with open(temp_target, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        if not validate_stable_config(cfg):
            return False

        os.replace(temp_target, CURRENT_CONFIG_PATH)
        return True
    except (OSError, json.JSONDecodeError, ValueError):
        return False
    finally:
        if os.path.exists(temp_target):
            try:
                os.remove(temp_target)
            except OSError:
                pass
