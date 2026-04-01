import os
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping, Optional, Union


class Type(str, Enum):
    FALSE_POSITIVE = "False Positive"
    FALSE_NEGATIVE = "False Negative"
    LABEL_MISMATCH = "Label Mismatch"
    CORRECT = "Correct"


class Label(int, Enum):
    TASK_BASED = 0
    INFORMATION_SIMPLE = 1
    INFORMATION_COMPLEX = 2


class FeedbackSubmissionError(RuntimeError):
    """Raised when feedback could not be submitted to Google Sheets."""


_SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive",
]

_DEFAULT_SHEET_NAME = "AIImportance Feedback"
_DEFAULT_WORKSHEET_NAME = "MAIN"

_client = None


def _import_google_clients():
    try:
        import gspread
        from oauth2client.service_account import ServiceAccountCredentials
    except Exception as exc:  # pragma: no cover - import failure path
        raise FeedbackSubmissionError(
            "Google Sheets dependencies are missing. Install `gspread` and `oauth2client`."
        ) from exc
    return gspread, ServiceAccountCredentials


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _get_creds_path() -> str:
    return os.getenv("DYRWTUAFTQ_GOOGLE_CREDS_FILE", "creds.json")


def _get_sheet_name() -> str:
    return os.getenv("DYRWTUAFTQ_FEEDBACK_SHEET_NAME", _DEFAULT_SHEET_NAME)


def _get_worksheet_name() -> str:
    return os.getenv("DYRWTUAFTQ_FEEDBACK_WORKSHEET", _DEFAULT_WORKSHEET_NAME)


def _normalize_decision(value: Optional[Union[int, str, Label]]) -> str:
    if isinstance(value, Label):
        value = value.value

    if isinstance(value, int):
        value = str(value)

    text = (value or "").strip().lower()
    if text in {"allow", "task-based", "task_based", "0"}:
        return "allow"
    if text in {"no-ai", "no_ai", "information-simple", "information_simple", "low-complexity", "1"}:
        return "no-ai"
    if text in {"maybe", "information-complex", "information_complex", "high-complexity", "2"}:
        return "maybe"
    return text


def _coerce_feedback_type(
    value: Optional[Union[Type, str]],
    *,
    predicted_decision: Optional[str],
    actual_label: Optional[str],
) -> str:
    if isinstance(value, Type):
        return value.value

    text = (value or "").strip().lower()
    if text in {"false positive", "false_positive", "fp"}:
        return Type.FALSE_POSITIVE.value
    if text in {"false negative", "false_negative", "fn"}:
        return Type.FALSE_NEGATIVE.value
    if text in {"label mismatch", "label_mismatch", "mismatch"}:
        return Type.LABEL_MISMATCH.value
    if text in {"correct", "match", "matched"}:
        return Type.CORRECT.value

    predicted = _normalize_decision(predicted_decision)
    actual = _normalize_decision(actual_label)

    if not predicted or not actual:
        return "Unspecified"
    if predicted == actual:
        return Type.CORRECT.value
    if actual == "allow" and predicted != "allow":
        return Type.FALSE_POSITIVE.value
    if predicted == "allow" and actual != "allow":
        return Type.FALSE_NEGATIVE.value
    return Type.LABEL_MISMATCH.value


def _resolve_actual_label(
    label: Optional[Union[Label, int, str]],
    actual_label: Optional[str],
    expected_decision: Optional[str],
) -> str:
    # Priority: explicit actual_label -> legacy label input -> expected_decision fallback.
    for candidate in (actual_label, label, expected_decision):
        normalized = _normalize_decision(candidate)
        if normalized:
            return normalized
    return ""


def _authorize_client():
    global _client
    if _client is not None:
        return _client

    creds_path = _get_creds_path()
    if not os.path.exists(creds_path):
        raise FeedbackSubmissionError(
            f"Google credentials file not found at `{creds_path}`."
        )

    gspread, ServiceAccountCredentials = _import_google_clients()
    credentials = ServiceAccountCredentials.from_json_keyfile_name(creds_path, _SCOPE)
    _client = gspread.authorize(credentials)
    return _client


def _get_worksheet():
    client = _authorize_client()
    sheet_name = _get_sheet_name()
    worksheet_name = _get_worksheet_name()

    try:
        spreadsheet = client.open(sheet_name)
    except Exception as exc:  # pragma: no cover - network/API failure
        raise FeedbackSubmissionError(
            f"Could not open spreadsheet `{sheet_name}`."
        ) from exc

    try:
        return spreadsheet.worksheet(worksheet_name)
    except Exception:
        try:
            return spreadsheet.sheet1
        except Exception as exc:  # pragma: no cover - unexpected sheet failure
            raise FeedbackSubmissionError(
                f"Could not open worksheet `{worksheet_name}` in `{sheet_name}`."
            ) from exc


def write_feedback(
    type: Optional[Union[Type, str]],
    label: Optional[Union[Label, int, str]],
    prompt: str,
    *,
    predicted_decision: Optional[str] = None,
    actual_label: Optional[str] = None,
    expected_decision: Optional[str] = None,
    notes: Optional[str] = None,
    model_type: Optional[str] = None,
    ib_label: Optional[str] = None,
    ic_label: Optional[str] = None,
    source_url: Optional[str] = None,
    metadata: Optional[Mapping[str, Any]] = None,
    submitted_at: Optional[str] = None,
) -> dict:
    prompt_text = (prompt or "").strip()
    if not prompt_text:
        raise FeedbackSubmissionError("Feedback prompt cannot be empty.")

    resolved_actual_label = _resolve_actual_label(label, actual_label, expected_decision)
    resolved_type = _coerce_feedback_type(
        type,
        predicted_decision=predicted_decision,
        actual_label=resolved_actual_label,
    )

    payload = {
        "submitted_at": (submitted_at or "").strip() or _utc_now_iso(),
        "feedback_type": resolved_type,
        "actual_label": resolved_actual_label,
        "prompt": prompt_text,
        "predicted_decision": _normalize_decision(predicted_decision),
        "notes": (notes or "").strip(),
        "model_type": (model_type or "").strip(),
        "ib_label": (ib_label or "").strip(),
        "ic_label": (ic_label or "").strip(),
        "source_url": (source_url or "").strip(),
        "metadata": dict(metadata or {}),
    }

    worksheet = _get_worksheet()
    row = [
        payload["submitted_at"],
        payload["feedback_type"],
        payload["actual_label"] or "unknown",
        payload["prompt"],
    ]

    try:
        worksheet.append_row(row, value_input_option="RAW")
    except Exception as exc:  # pragma: no cover - network/API failure
        raise FeedbackSubmissionError("Failed to append feedback row to Google Sheet.") from exc

    return payload


def write_feedback_payload(payload: Mapping[str, Any]) -> dict:
    if payload is None:
        raise FeedbackSubmissionError("Missing feedback payload.")

    return write_feedback(
        type=payload.get("feedback_type"),
        label=payload.get("expected_label"),
        prompt=str(payload.get("prompt", "")),
        predicted_decision=payload.get("predicted_decision"),
        actual_label=payload.get("actual_label"),
        expected_decision=payload.get("expected_decision"),
        notes=payload.get("notes"),
        model_type=payload.get("model_type"),
        ib_label=payload.get("ib_label"),
        ic_label=payload.get("ic_label"),
        source_url=payload.get("source_url"),
        metadata=payload.get("metadata") if isinstance(payload.get("metadata"), Mapping) else {},
        submitted_at=payload.get("submitted_at"),
    )
