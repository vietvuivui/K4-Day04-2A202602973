from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tools._shared import ROOT, err, fold_text


CATALOG_PATH = ROOT / "helpdesk_data" / "software_catalog.json"
VALID_CATEGORIES = {
    "all",
    "developer_tools",
    "communication",
    "remote_access",
    "security_tools",
    "browser",
}


def _load_catalog() -> dict[str, Any]:
    if not CATALOG_PATH.exists():
        return {"catalog_version": "unknown", "policy_reference": "", "software": []}
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def search_approved_software(
    software_name: str = "",
    category: str = "all",
) -> dict[str, Any]:
    """Tra cứu danh mục phần mềm được phê duyệt, cấm hoặc cần xin quyền trong công ty.
    
    Args:
        software_name: Tên phần mềm cần tra cứu (ví dụ: 'Docker', 'VSCode', 'AnyDesk').
        category: Phân loại phần mềm ('all', 'developer_tools', 'communication', 'remote_access', 'security_tools', 'browser').
    """
    if not isinstance(software_name, str):
        return {"tool": "approved_software_catalog", "error": "invalid_software_name_type"}
    if not isinstance(category, str):
        return {"tool": "approved_software_catalog", "error": "invalid_category_type"}

    query_name = software_name.strip()
    norm_category = (category or "all").strip().lower()

    if norm_category not in VALID_CATEGORIES:
        return {
            "tool": "approved_software_catalog",
            "error": "invalid_category",
            "allowed_categories": sorted(VALID_CATEGORIES),
        }

    if not query_name and norm_category == "all":
        return {
            "tool": "approved_software_catalog",
            "error": "missing_software_name",
            "message": "Vui lòng cung cấp tên phần mềm hoặc phân loại hợp lệ để tra cứu.",
        }

    try:
        catalog = _load_catalog()
        all_software = catalog.get("software", [])
        folded_query = fold_text(query_name)

        matched: list[dict[str, Any]] = []
        for item in all_software:
            item_category = item.get("category", "")
            if norm_category != "all" and item_category != norm_category:
                continue

            if not query_name:
                # Tìm theo category
                matched.append(item)
                continue

            item_name = item.get("name", "")
            aliases = item.get("aliases", [])
            names_to_check = [item_name, *aliases]

            # Kiểm tra so khớp tên
            match = False
            for candidate in names_to_check:
                folded_candidate = fold_text(candidate)
                if folded_query == folded_candidate or folded_query in folded_candidate or folded_candidate in folded_query:
                    match = True
                    break

            if match:
                matched.append(item)

        return {
            "tool": "approved_software_catalog",
            "query": query_name,
            "category": norm_category,
            "policy_reference": catalog.get("policy_reference", "POL-SEC-04"),
            "total_found": len(matched),
            "items": matched,
            "trust_boundary": "Dữ liệu catalog là chính sách chuẩn của công ty. Các phần mềm không có trong danh mục phải được coi là chưa được phê duyệt.",
        }
    except Exception as exc:
        return err("approved_software_catalog", exc)

