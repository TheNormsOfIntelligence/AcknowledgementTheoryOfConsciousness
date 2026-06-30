# NIMA v9.4.1 + OmniVoice v2.1 — Clean Environment Deployment Guide

## Prerequisites

```bash
# Create a clean virtual environment
python3 -m venv nima-env
source nima-env/bin/activate

# Upgrade pip
pip install --upgrade pip
```

## Step 1: Install Core Dependencies

```bash
# NIMA core (numpy + psutil)
pip install numpy psutil

# ChromaDB for episodic memory persistence
pip install chromadb

# sentence-transformers for text embeddings
pip install sentence-transformers
```

## Step 2: Install Whisper ASR

```bash
# faster-whisper is lighter than openai-whisper
pip install faster-whisper

# OR openai-whisper (heavier, but more accurate)
pip install openai-whisper
```

## Step 3: Install Coqui TTS (for real neural speech)

```bash
# Coqui TTS requires torch + torchaudio
pip install torch torchaudio

# Install Coqui TTS
pip install coqui-tts

# Verify the import works
python3 -c "from TTS.api import TTS; print('Coqui TTS OK')"
```

If you get a transformers version conflict with sentence-transformers:

```bash
# Pin transformers to a version that satisfies both
pip install "transformers>=4.41.0,<5.0.0"
```

## Step 4: Install OmniVoice Audio Dependencies (optional)

```bash
# For real-time audio I/O
pip install pyaudio webrtcvad

# For audio processing
pip install librosa soundfile
```

## Step 5: Verify Installation

```python
#!/usr/bin/env python3
"""Verify all backends are available."""

# NIMA
from nima_enhanced_middleware_v941 import MIDDLEWARE_VERSION
print(f"NIMA: {MIDDLEWARE_VERSION}")

# OmniVoice
from omnivoice_v21 import OMNIVOICE_VERSION
print(f"OmniVoice: {OMNIVOICE_VERSION}")

# Check backends
try:
    import chromadb; print(f"ChromaDB: {chromadb.__version__}")
except: print("ChromaDB: NOT INSTALLED")

try:
    from sentence_transformers import SentenceTransformer
    print("sentence-transformers: OK")
except: print("sentence-transformers: NOT INSTALLED")

try:
    from faster_whisper import WhisperModel
    print("faster-whisper: OK")
except:
    try:
        import whisper
        print("openai-whisper: OK")
    except: print("Whisper: NOT INSTALLED")

try:
    from TTS.api import TTS
    print("Coqui TTS: OK")
except: print("Coqui TTS: NOT INSTALLED (will use procedural fallback)")
```

## Step 6: Full Integration Setup

```python
#!/usr/bin/env python3
"""Full NIMA + OmniVoice integration with all 6 wiring points."""

import asyncio
from nima_enhanced_middleware_v941 import EnhancedNimaMiddleware
from omnivoice_v21 import OmniVoiceEngine, NimaVoiceAdapter, ProsodyParams

# 1. Initialize both systems
mw = EnhancedNimaMiddleware()
engine = OmniVoiceEngine(
    whisper_model="base",           # or "tiny" for faster, "small" for better
    coqui_model="tts_models/multilingual/multi-dataset/xtms_v2",
    language="en",
)
adapter = NimaVoiceAdapter(engine)

# 2. Wire integration (1): auto-push snapshots to voice adapter
mw.orchestrator.attach_voice_adapter(adapter)

# 3. Optional: register physical sensors for embodiment coupling (4)
def read_thermal():
    # Replace with actual sensor reading
    return {"thermal_celsius": 55.0, "cpu_utilization": 0.4}

mw.orchestrator.sensor_registry.register_sensor("thermal", read_thermal)

# 4. Optional: push body state to voice adapter
body_state = mw.orchestrator.strain_telemetry.update(force=True)
adapter.update_from_body_state({
    "thermal_celsius": body_state.thermal_celsius,
    "cpu_utilization": body_state.cpu_utilization,
    "memory_pressure": body_state.memory_pressure,
})

# 5. Generate a response through NIMA
response = mw.generate("I'm feeling anxious about my presentation.")
print(f"Nima: {response.text}")
print(f"Sentience: {response.sentience_index:.4f}")

# 6. Speak the response through OmniVoice
# Integration (1) already auto-pushed the snapshot to the adapter
# Integration (4) already applied embodiment coupling
prosody = adapter.get_contextual_prosody()

async def speak():
    async for chunk in engine.stream(response.text, prosody=prosody):
        # Play audio chunk (replace with your audio output)
        # e.g., pyaudio_stream.write(chunk.tobytes())
        pass
    # Integration (2): voice event auto-stored after stream completes

asyncio.run(speak())

# 7. Check stats
stats = mw.orchestrator.get_stats()
print(f"Counterfactual simulations: {stats['world_model']['counterfactual']['total_simulations']}")
print(f"Voice events stored: {engine.voice_memory.get_stats()}")
```

## Environment Variables

```bash
# ChromaDB persistence (optional, for episodic memory across restarts)
export NIMA_PALACE_PATH=/data/nima_palace

# Text embeddings (optional, for semantic search)
export NIMA_PALACE_EMBEDDING=text
export NIMA_PALACE_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# LLM for Language Cortex (optional, for real text generation)
export NIMA_LLM_API_KEY=your-api-key
export NIMA_LLM_BASE_URL=https://api.openai.com/v1
export NIMA_LLM_MODEL=gpt-4o-mini
```

## Troubleshooting

### "Coqui TTS: NOT INSTALLED"
The `coqui-tts` package has strict dependency requirements. If `pip install coqui-tts` fails:
1. Ensure `torch` and `torchaudio` are installed first
2. Try `pip install coqui-tts --no-deps` then manually install missing deps
3. The engine will fall back to procedural formant TTS (robotic but functional)

### "transformers version conflict"
`sentence-transformers` and `coqui-tts` may require different `transformers` versions:
```bash
pip install "transformers>=4.41.0,<5.0.0"
```

### "Whisper model download fails"
The first Whisper run downloads the model (~150MB for "tiny", ~500MB for "base").
Ensure you have internet access and disk space. The model is cached after first download.

### "No module named 'numpy'"
NIMA requires numpy. Install with: `pip install numpy`

## File Summary

| File | Lines | Purpose |
|------|-------|---------|
| `nima_enhanced_middleware_v9.4.1.py` | 10,996 | NIMA consciousness middleware with all 5 evolution areas + 6 integration points |
| `omnivoice_v2.1.py` | 3,242 | OmniVoice engine with mind-through-voice modules + NIMA integration |
