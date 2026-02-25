"""Load restaurant dataset from Hugging Face API."""

from typing import List, Optional

from datasets import load_dataset

from .models import RestaurantRecord

HF_DATASET_ID = "ManikaSaini/zomato-restaurant-recommendation"
SPLIT = "train"


def _fix_mojibake(text: str) -> str:
    """Fix double-encoded UTF-8 text (e.g. 'SantÃ©' → 'Santé').

    Common in datasets where UTF-8 bytes were misread as Latin-1.
    Applies repeatedly to handle multi-level corruption.
    """
    for _ in range(10):                       # guard against infinite loop
        try:
            fixed = text.encode("latin-1").decode("utf-8")
        except (UnicodeDecodeError, UnicodeEncodeError):
            break
        if fixed == text or len(fixed) >= len(text):
            break
        text = fixed
    return text


def _safe_str(value, default: str = "") -> str:
    if value is None:
        return default
    s = str(value).strip() or default
    return _fix_mojibake(s) if s else s


def _safe_int(value) -> Optional[int]:
    if value is None:
        return None
    try:
        s = str(value).replace(",", "").strip()
        return int(s) if s else None
    except (ValueError, TypeError):
        return None


def _row_to_record(row: dict) -> RestaurantRecord:
    """Map a dataset row to canonical RestaurantRecord."""
    return RestaurantRecord(
        name=_safe_str(row.get("name"), "Unknown"),
        address=_safe_str(row.get("address")) or None,
        location=_safe_str(row.get("location")) or None,
        listed_in_city=_safe_str(row.get("listed_in(city)")) or None,
        cuisines=_safe_str(row.get("cuisines")) or None,
        approx_cost=_safe_str(row.get("approx_cost(for two people)")) or None,
        rate=_safe_str(row.get("rate")) or None,
        votes=_safe_int(row.get("votes")),
        rest_type=_safe_str(row.get("rest_type")) or None,
        dish_liked=_safe_str(row.get("dish_liked")) or None,
        online_order=_safe_str(row.get("online_order")) or None,
        book_table=_safe_str(row.get("book_table")) or None,
        url=_safe_str(row.get("url")) or None,
        phone=_safe_str(row.get("phone")) or None,
    )


def load_dataset_from_hf(
    dataset_id: str = HF_DATASET_ID,
    split: str = SPLIT,
    trust_remote_code: bool = False,
) -> List[RestaurantRecord]:
    """
    Fetch the dataset from Hugging Face API and return a list of RestaurantRecords.

    Uses the Datasets Hub API; no static file download.
    """
    ds = load_dataset(
        dataset_id,
        split=split,
        trust_remote_code=trust_remote_code,
    )
    return [_row_to_record(ds[i]) for i in range(len(ds))]
