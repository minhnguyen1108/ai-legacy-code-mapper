from __future__ import annotations

import json

from app.models import BusinessFlow, Risk


SYSTEM_PROMPT_VI = """Bạn là senior backend engineer chuyên reverse engineer Laravel legacy.
Chỉ suy luận từ dữ liệu được cung cấp. Không bịa business rule.
Nếu thiếu thông tin, ghi rõ "chưa xác định".
Không dùng Markdown ngoài nội dung được yêu cầu."""


def business_flow_prompt(flow: BusinessFlow) -> str:
    payload = {
        "route": f"{flow.route.method} {flow.route.path}",
        "controller": f"{flow.route.controller}@{flow.route.action}",
        "middleware": flow.route.middleware,
        "call_chain": [
            {
                "kind": step.kind,
                "call": f"{step.class_name}::{step.method_name}",
                "snippet": step.snippet,
            }
            for step in flow.steps
        ],
        "tables": flow.tables,
    }
    return (
        "Hãy giải thích business meaning của flow sau bằng tiếng Việt trong 2-4 câu. "
        "Nêu actor/hành động/kết quả chỉ khi code cho phép xác định. "
        "Không thêm tiêu đề.\n\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
    )


def risk_summary_prompt(risks: list[Risk]) -> str:
    payload = [
        {
            "severity": risk.severity,
            "category": risk.category,
            "message": risk.message,
            "source": f"{risk.source.file}:{risk.source.line}" if risk.source else None,
        }
        for risk in risks[:50]
    ]
    return (
        "Tóm tắt rủi ro kỹ thuật sau thành 3-6 câu tiếng Việt. "
        "Ưu tiên high/medium, không phóng đại và không khẳng định lỗ hổng nếu chưa đủ bằng chứng.\n\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
    )
