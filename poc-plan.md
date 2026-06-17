# PoC Plan: Kokoro-FastAPI

## Project Classification
- **Type:** model-serving
- **Key Technologies:** Python, FastAPI, PyTorch, Kokoro-82M TTS model, espeak-ng
- **ODH Relevance:** Validates serving a text-to-speech model on OpenShift AI using an OpenAI-compatible API. Demonstrates ML model serving patterns including model baking, health endpoints, and inference latency measurement.

## PoC Objectives
1. Deploy the Kokoro-FastAPI TTS service on OpenShift using the pre-built CPU container image
2. Validate the OpenAI-compatible /v1/audio/speech endpoint generates audio from text
3. Verify health and readiness endpoints work correctly for Kubernetes probes
4. Measure inference latency for CPU-based TTS generation
5. Demonstrate the built-in web player UI is accessible

## Infrastructure Requirements
- **Resource Profile:** medium (1Gi RAM, 500m CPU minimum; 4Gi recommended)
- **GPU Required:** No (CPU mode fully supported)
- **Persistent Storage:** None (model baked into image)
- **Sidecar Containers:** None
- **Deployment Model:** deployment (long-running HTTP server)
- **Listens on Port:** Yes (8880)
- **LLM API Required:** No

## Test Scenarios

### Scenario 1: health-check
- **Description:** Verify the health endpoint
- **Type:** http
- **Endpoint:** GET /health
- **Expected:** Returns HTTP 200 with {"status":"healthy"}
- **Timeout:** 60 seconds (model warmup may take time)

### Scenario 2: tts-generate
- **Description:** Generate speech audio from text using the OpenAI-compatible endpoint
- **Type:** http
- **Endpoint:** POST /v1/audio/speech
- **Input:** {"model":"kokoro","input":"Hello from OpenShift","voice":"af_heart"}
- **Expected:** Returns HTTP 200 with audio data (WAV/MP3)
- **Timeout:** 120 seconds

### Scenario 3: voices-list
- **Description:** List available TTS voices
- **Type:** http
- **Endpoint:** GET /v1/audio/voices
- **Expected:** Returns HTTP 200 with JSON array of available voices
- **Timeout:** 30 seconds

### Scenario 4: web-player
- **Description:** Verify the web player UI is accessible
- **Type:** http
- **Endpoint:** GET /web/
- **Expected:** Returns HTTP 200 with HTML content
- **Timeout:** 15 seconds

## Dockerfile Considerations
- Using pre-built image ghcr.io/remsky/kokoro-fastapi-cpu:latest (multi-arch, 4+ GB)
- UBI re-containerization deferred due to complexity (Rust toolchain, model download, UniDic dictionary)
- Image includes baked-in Kokoro-82M model weights

## Deployment Considerations
- Deploy as a Kubernetes Deployment with 1 replica
- Resource requests: 2Gi RAM, 1 CPU (model loading requires significant memory)
- Resource limits: 4Gi RAM, 2 CPU
- Liveness probe: GET /health with 60s initial delay (model warmup)
- Readiness probe: GET /health with 60s initial delay
- Set DOWNLOAD_MODEL=false since model is baked in
- Set USE_GPU=false for CPU inference
