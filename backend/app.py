import os
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from functools import lru_cache
import torch

from src.model import encode_text, get_sbert_model, load_model, predict_from_embedding

app = FastAPI()

torch.set_num_threads(int(os.getenv("PROMPT_SENTINEL_TORCH_THREADS", "4")))

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

    return {
        "ib": ib_check,
        "ic": ic_check,
        "ib_label": ib_label,
        "ic_label": ic_label,
        "model_type": request.model_type,
        "decision_level": decision_level,
        "latency_ms": elapsed_ms,
    }