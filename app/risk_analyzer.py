from __future__ import annotations

import re

from app.models import Risk, SourceRef
from app.scanner.file_scanner import PhpFile
from app.scanner.php_parser import ClassInfo


def analyze_risks(files: list[PhpFile], classes: list[ClassInfo]) -> list[Risk]:
    risks: list[Risk] = []
    patterns = [
        (
            r"\b(md5|sha1)\s*\(",
            "high",
            "security",
            "Thuật toán hash cũ được sử dụng; không phù hợp để lưu mật khẩu hoặc dữ liệu nhạy cảm.",
            "Dùng password_hash/Hash facade hoặc thuật toán hiện đại phù hợp ngữ cảnh.",
        ),
        (
            r"\b(unserialize|eval)\s*\(",
            "high",
            "security",
            "Có lời gọi thực thi hoặc deserialize dữ liệu tiềm ẩn rủi ro.",
            "Loại bỏ eval và chỉ deserialize dữ liệu đáng tin cậy với allowlist.",
        ),
        (
            r"(DB::raw|whereRaw|selectRaw)\s*\(",
            "medium",
            "database",
            "Raw SQL cần được kiểm tra binding để tránh SQL injection và khó nâng cấp.",
            "Ưu tiên Query Builder và parameter binding.",
        ),
        (
            r"\benv\s*\(",
            "low",
            "configuration",
            "Gọi env() ngoài file config có thể sai khi Laravel cache cấu hình.",
            "Đưa biến vào config và đọc qua config().",
        ),
        (
            r"\bdd\s*\(|\bdump\s*\(",
            "medium",
            "debug",
            "Debug statement còn trong source production.",
            "Xóa debug statement hoặc thay bằng logging có kiểm soát.",
        ),
    ]
    for file in files:
        for pattern, severity, category, message, recommendation in patterns:
            for match in re.finditer(pattern, file.content):
                risks.append(
                    Risk(
                        severity=severity,
                        category=category,
                        message=message,
                        source=SourceRef(
                            file.relative_path,
                            file.content.count("\n", 0, match.start()) + 1,
                        ),
                        recommendation=recommendation,
                    )
                )
    for class_info in classes:
        for method in class_info.methods.values():
            lines = [line for line in method.body.splitlines() if line.strip()]
            if len(lines) > 80:
                risks.append(
                    Risk(
                        severity="medium",
                        category="complexity",
                        message=f"{class_info.name}::{method.name} có {len(lines)} dòng, khó đọc và kiểm thử.",
                        source=SourceRef(class_info.file.relative_path, method.line),
                        recommendation="Tách method theo từng trách nhiệm nghiệp vụ.",
                    )
                )
            branch_count = len(re.findall(r"\b(if|elseif|for|foreach|while|case|catch)\b", method.body))
            if branch_count > 12:
                risks.append(
                    Risk(
                        severity="medium",
                        category="complexity",
                        message=f"{class_info.name}::{method.name} có độ phân nhánh cao ({branch_count}).",
                        source=SourceRef(class_info.file.relative_path, method.line),
                        recommendation="Tách điều kiện thành policy, rule hoặc service nhỏ.",
                    )
                )
    return risks
