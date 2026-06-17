#!/usr/bin/env python3
"""AutoPoC Test Script for Kokoro-FastAPI TTS Service"""
import json, os, sys, time, urllib.request, urllib.error

SERVICE_URL = os.environ.get("SERVICE_URL", sys.argv[1] if len(sys.argv) > 1 else "http://kokoro-fastapi.poc-kokoro-fastapi.svc.cluster.local:8880")
MAX_RETRIES = 5
RETRY_DELAY = 15
results = []

def test_scenario(name, description, method, path, body=None,
                  expected_status=200, expected_content=None, timeout=120,
                  check_binary=False):
    url = f"{SERVICE_URL.rstrip('/')}{path}"
    start = time.time()
    for attempt in range(MAX_RETRIES):
        try:
            if body:
                data = json.dumps(body).encode() if isinstance(body, dict) else body.encode()
                req = urllib.request.Request(url, data=data, method=method)
                req.add_header("Content-Type", "application/json")
            else:
                req = urllib.request.Request(url, method=method)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                status = resp.status
                if check_binary:
                    raw = resp.read()
                    content_type = resp.headers.get("Content-Type", "")
                    response_body = f"Binary response: {len(raw)} bytes, Content-Type: {content_type}"
                    if len(raw) < 100:
                        r = {"scenario_name": name, "status": "fail",
                             "output": response_body,
                             "error_message": f"Audio response too small ({len(raw)} bytes)",
                             "duration_seconds": round(time.time()-start, 2)}
                        results.append(r); return r
                else:
                    response_body = resp.read().decode()
                if status == expected_status:
                    if expected_content and expected_content not in response_body:
                        r = {"scenario_name": name, "status": "fail",
                             "output": response_body[:2000],
                             "error_message": f"Expected '{expected_content}' not in response",
                             "duration_seconds": round(time.time()-start, 2)}
                    else:
                        r = {"scenario_name": name, "status": "pass",
                             "output": response_body[:2000], "error_message": None,
                             "duration_seconds": round(time.time()-start, 2)}
                    results.append(r); return r
                elif attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY); continue
                else:
                    r = {"scenario_name": name, "status": "fail",
                         "output": response_body[:2000],
                         "error_message": f"Expected {expected_status}, got {status}",
                         "duration_seconds": round(time.time()-start, 2)}
                    results.append(r); return r
        except urllib.error.HTTPError as e:
            response_body = e.read().decode() if hasattr(e, 'read') else str(e)
            if attempt < MAX_RETRIES - 1:
                print(f"  Retry {attempt+1}/{MAX_RETRIES}: HTTP {e.code}", file=sys.stderr)
                time.sleep(RETRY_DELAY)
            else:
                r = {"scenario_name": name, "status": "fail",
                     "output": response_body[:2000],
                     "error_message": f"Expected {expected_status}, got {e.code}",
                     "duration_seconds": round(time.time()-start, 2)}
                results.append(r); return r
        except urllib.error.URLError as e:
            if attempt < MAX_RETRIES - 1:
                print(f"  Retry {attempt+1}/{MAX_RETRIES}: {e}", file=sys.stderr)
                time.sleep(RETRY_DELAY)
            else:
                r = {"scenario_name": name, "status": "error", "output": "",
                     "error_message": f"Unreachable after {MAX_RETRIES} attempts: {e}",
                     "duration_seconds": round(time.time()-start, 2)}
                results.append(r); return r
        except Exception as e:
            r = {"scenario_name": name, "status": "error", "output": "",
                 "error_message": str(e),
                 "duration_seconds": round(time.time()-start, 2)}
            results.append(r); return r

# === SCENARIO 1: Health Check ===
print("Testing health-check...", file=sys.stderr)
test_scenario(
    name="health-check",
    description="Verify the health endpoint",
    method="GET",
    path="/health",
    expected_status=200,
    expected_content="healthy"
)

# === SCENARIO 2: TTS Generate ===
print("Testing tts-generate...", file=sys.stderr)
test_scenario(
    name="tts-generate",
    description="Generate speech audio from text",
    method="POST",
    path="/v1/audio/speech",
    body={
        "model": "kokoro",
        "input": "Hello from OpenShift. This is a proof of concept for text to speech.",
        "voice": "af_heart",
        "response_format": "wav"
    },
    expected_status=200,
    check_binary=True,
    timeout=120
)

# === SCENARIO 3: Voices List ===
print("Testing voices-list...", file=sys.stderr)
test_scenario(
    name="voices-list",
    description="List available TTS voices",
    method="GET",
    path="/v1/audio/voices",
    expected_status=200,
    expected_content="voices"
)

# === SCENARIO 4: Web Player ===
print("Testing web-player...", file=sys.stderr)
test_scenario(
    name="web-player",
    description="Verify web player UI is accessible",
    method="GET",
    path="/web/",
    expected_status=200,
    expected_content="html"
)

# === OUTPUT RESULTS ===
print(json.dumps({"results": results}, indent=2))
sys.exit(1 if any(r["status"] in ("fail", "error") for r in results) else 0)
