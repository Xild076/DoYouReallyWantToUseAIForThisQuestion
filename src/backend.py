from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import torch
from functools import lru_cache
from .model import SmallClassifier, get_sbert_model, load_model, run_inference

app = FastAPI()

class InferenceRequest(BaseModel):
    text: str
    model_type: str  # "ib" or "ic"

@lru_cache(maxsize=1)
def load_models():
    sbert_model = get_sbert_model()
    ib_model = load_model('model/ib_classifier.pth', input_dim=384)
    ic_model = load_model('model/ic_classifier.pth', input_dim=384)
    return sbert_model, ib_model, ic_model

@app.post("/infer")
def infer(request: InferenceRequest):
    sbert_model, ib_model, ic_model = load_models()
    ib_check = run_inference(request.text, ib_model)
    ic_check = run_inference(request.text, ic_model)

    ib_label = "information-based" if ib_check == 0 else "task-based"
    ic_label = "low-complexity" if ic_check == 0 else "high-complexity"

    def determine_level(ib_lbl, ic_lbl):
        if ic_lbl == "high-complexity":
            return "no-ai"
        if ib_lbl == "information-based":
            return "allow"
        return "maybe"

    decision_level = determine_level(ib_label, ic_label)

    return {
        "ib": ib_check,
        "ic": ic_check,
        "ib_label": ib_label,
        "ic_label": ic_label,
        "model_type": request.model_type,
        "decision_level": decision_level,
    }