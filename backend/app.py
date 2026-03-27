import os
import time
from collections import OrderedDict
from threading import Lock

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from functools import lru_cache
import torch

from src.model import encode_text, get_sbert_model, load_model, predict_from_embedding

app = FastAPI()

torch.set_num_threads(int(os.getenv("PROMPT_SENTINEL_TORCH_THREADS", "4")))

CACHE_TTL_SECONDS = int(os.getenv("PROMPT_SENTINEL_CACHE_TTL_SECONDS", "900"))
CACHE_MAX_ENTRIES = int(os.getenv("PROMPT_SENTINEL_CACHE_MAX_ENTRIES", "5000"))

_inference_cache = OrderedDict()
_cache_lock = Lock()


def _cache_key(request: InferenceRequest):
    # Normalize text to maximize cache hit ratio for semantically identical prompts.
    return f"{request.model_type}|{request.text.strip().lower()}"


def _cache_get(key):
    now = time.time()
    with _cache_lock:
        entry = _inference_cache.get(key)
        if not entry:
            return None
        expires_at, payload = entry
        if now >= expires_at:
            _inference_cache.pop(key, None)
            return None
        _inference_cache.move_to_end(key)
        return payload.copy()


def _cache_set(key, payload):
    if CACHE_TTL_SECONDS <= 0 or CACHE_MAX_ENTRIES <= 0:
        return

    expires_at = time.time() + CACHE_TTL_SECONDS
    with _cache_lock:
        _inference_cache[key] = (expires_at, payload.copy())
        _inference_cache.move_to_end(key)
        while len(_inference_cache) > CACHE_MAX_ENTRIES:
            _inference_cache.popitem(last=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class InferenceRequest(BaseModel):
    text: str
    model_type: str = "ic"


@lru_cache(maxsize=1)
def load_models():
    sbert_model = get_sbert_model()
    ib_model = load_model('model/ib_classifier.pth', input_dim=384)
    ic_model = load_model('model/ic_classifier.pth', input_dim=384)
    return sbert_model, ib_model, ic_model


@app.on_event("startup")
def warmup_models():
    # Eagerly load and warm the encoder to avoid a very slow first request.
    load_models()
    encode_text("warmup")


@app.get("/")
@app.head("/")
def health_check():
    return {"status": "ok"}


def determine_decision_level(ib_lbl, ic_lbl):
    print(f"Determining decision level for IB label: {ib_lbl}, IC label: {ic_lbl}")
    if ic_lbl == "high-complexity":
        return "maybe"
    if ib_lbl == "task-based":
        return "allow"
    return "no-ai"


@app.post("/infer")
def infer(request: InferenceRequest):
    key = _cache_key(request)
    cached = _cache_get(key)
    if cached is not None:
        cached["cache_hit"] = True
        cached["latency_ms"] = 0.0
        return cached

    _sbert_model, ib_model, ic_model = load_models()

    started = time.perf_counter()
    embedding_tensor = encode_text(request.text)
    ib_check = predict_from_embedding(embedding_tensor, ib_model)
    ic_check = predict_from_embedding(embedding_tensor, ic_model)
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)

    ib_label = "information-based" if ib_check == 0 else "task-based"
    ic_label = "low-complexity" if ic_check == 0 else "high-complexity"
    decision_level = determine_decision_level(ib_label, ic_label)

    print(f"Received inference request: {request.text}")
    print(f"Decision level: {decision_level}")
    print(f"Inference latency (ms): {elapsed_ms}")

    payload = {
        "ib": ib_check,
        "ic": ic_check,
        "ib_label": ib_label,
        "ic_label": ic_label,
        "model_type": request.model_type,
        "decision_level": decision_level,
        "latency_ms": elapsed_ms,
        "cache_hit": False,
    }

    _cache_set(key, payload)
    return payload