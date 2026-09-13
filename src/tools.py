"""
🛠️ TOOL DEFINITIONS & EXECUTION BACKEND
Mã nguồn chứa danh sách Tool Schemas (JSON Schema) và Execution Layer phục vụ cho MCP Server.
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List

# ==============================================================================
# 1. KHAI BÁO TOOL SCHEMAS CHUẨN NATIVE JSON SCHEMA
# ==============================================================================

TOOLS_SCHEMA = [
    {
        "name": "lookup_book",
        "description": "Tra cứu thông tin sách, vị trí kệ, tình trạng mượn/trả và người đang giữ sách bằng mã sách hoặc từ khóa tìm kiếm.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Mã sách (ví dụ: 'BK1001') hoặc từ khóa tên sách/tác giả/danh mục (ví dụ: 'Python căn bản')"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "borrow_book",
        "description": "Cho phép thành viên mượn sách từ thư viện.",
        "parameters": {
            "type": "object",
            "properties": {
                "book_id": {
                    "type": "string",
                    "description": "Mã sách cần mượn (ví dụ: 'BK1001')"
                },
                "member_id": {
                    "type": "string",
                    "description": "Mã thành viên mượn sách (ví dụ: 'MEM001')"
                }
            },
            "required": ["book_id", "member_id"]
        }
    },
    {
        "name": "return_book",
        "description": "Cho phép thành viên trả sách về thư viện.",
        "parameters": {
            "type": "object",
            "properties": {
                "book_id": {
                    "type": "string",
                    "description": "Mã sách cần trả (ví dụ: 'BK1001')"
                },
                "member_id": {
                    "type": "string",
                    "description": "Mã thành viên trả sách (ví dụ: 'MEM001')"
                }
            },
            "required": ["book_id", "member_id"]
        }
    },
    {
        "name": "renew_book",
        "description": "Gia hạn thời hạn mượn cho sách đã được mượn.",
        "parameters": {
            "type": "object",
            "properties": {
                "book_id": {
                    "type": "string",
                    "description": "Mã sách cần gia hạn (ví dụ: 'BK1001')"
                },
                "member_id": {
                    "type": "string",
                    "description": "Mã thành viên đang giữ sách (ví dụ: 'MEM001')"
                },
                "days": {
                    "type": "integer",
                    "description": "Số ngày muốn gia hạn thêm (mặc định 7 ngày)"
                }
            },
            "required": ["book_id", "member_id"]
        }
    }
]

# ==============================================================================
# 2. MÔ PHỎNG DỮ LIỆU & HÀM THỰC THI TOOL (EXECUTION LAYER)
# ==============================================================================

MOCK_DATABASE = {
    "BK1001": {
        "book_id": "BK1001",
        "title": "Python Căn Bản",
        "author": "Nguyễn Văn A",
        "category": "Lập trình",
        "location": "Tầng 1 - Kệ A101",
        "shelf": "A101",
        "status": "available",
        "total_copies": 3,
        "available_copies": 3,
        "borrowers": [],
        "borrower_id": None,
        "due_date": None,
        "renewals_used": 0
    },
    "BK1002": {
        "book_id": "BK1002",
        "title": "Thiết Kế CSDL",
        "author": "Trần Thị B",
        "category": "Cơ sở dữ liệu",
        "location": "Tầng 2 - Kệ B204",
        "shelf": "B204",
        "status": "borrowed",
        "total_copies": 2,
        "available_copies": 1,
        "borrowers": [
            {
                "member_id": "MEM001",
                "due_date": "2026-09-18",
                "renewals_used": 1
            }
        ],
        "borrower_id": "MEM001",
        "due_date": "2026-09-18",
        "renewals_used": 1
    },
    "BK1003": {
        "book_id": "BK1003",
        "title": "Machine Learning Cơ Bản",
        "author": "Lê Hoàng C",
        "category": "AI & ML",
        "location": "Tầng 3 - Kệ C305",
        "shelf": "C305",
        "status": "available",
        "total_copies": 4,
        "available_copies": 4,
        "borrowers": [],
        "borrower_id": None,
        "due_date": None,
        "renewals_used": 0
    },
    "BK1004": {
        "book_id": "BK1004",
        "title": "Đại cương Hoá Hữu cơ",
        "author": "Phạm Duy E",
        "category": "Hóa học",
        "location": "Tầng 1 - Kệ D112",
        "shelf": "D112",
        "status": "available",
        "total_copies": 2,
        "available_copies": 2,
        "borrowers": [],
        "borrower_id": None,
        "due_date": None,
        "renewals_used": 0
    }
}


def _next_due_date(days: int = 14) -> str:
    return (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")


def _normalize_book(query: str) -> str:
    return query.strip().upper()


def _normalize_member_id(member_id: str) -> str:
    return member_id.strip().upper()


def _sync_book_state(book: Dict[str, Any]) -> Dict[str, Any]:
    """Tái lập trạng thái sách từ danh sách borrowers để hỗ trợ nhiều người mượn cùng lúc."""
    borrowers = book.get("borrowers") or []
    if not borrowers and book.get("borrower_id"):
        borrowers = [{
            "member_id": _normalize_member_id(book["borrower_id"]),
            "due_date": book.get("due_date"),
            "renewals_used": book.get("renewals_used", 0)
        }]

    book["borrowers"] = borrowers
    book["borrower_ids"] = [item["member_id"] for item in borrowers]
    book["available_copies"] = max(0, book.get("total_copies", len(borrowers)) - len(borrowers))
    book["status"] = "borrowed" if borrowers else "available"

    if len(borrowers) == 1:
        book["borrower_id"] = borrowers[0]["member_id"]
        book["due_date"] = borrowers[0].get("due_date")
    else:
        book["borrower_id"] = None
        book["due_date"] = None

    return book


def execute_lookup_book(query: str) -> str:
    """Tra cứu sách theo mã hoặc từ khóa"""
    if not query or not query.strip():
        return json.dumps(
            {"status": "INVALID_ARGUMENT", "message": "Vui lòng cung cấp mã sách hoặc từ khóa tìm kiếm."},
            ensure_ascii=False,
        )

    normalized_query = _normalize_book(query)
    exact_match = MOCK_DATABASE.get(normalized_query)
    if exact_match:
        return json.dumps(
            {
                "status": "SUCCESS",
                "query": query,
                "data": exact_match,
                "message": f"Đã tìm thấy sách {exact_match['title']} tại {exact_match['location']}."
            },
            ensure_ascii=False,
        )

    matches = []
    for book in MOCK_DATABASE.values():
        haystack = f"{book['title']} {book['author']} {book['category']} {book['book_id']}".lower()
        if normalized_query.lower() in haystack:
            matches.append(book)

    if not matches:
        return json.dumps(
            {"status": "NOT_FOUND", "message": f"Không tìm thấy sách phù hợp với '{query}'."},
            ensure_ascii=False,
        )

    return json.dumps(
        {
            "status": "SUCCESS",
            "query": query,
            "data": matches,
            "message": f"Tìm thấy {len(matches)} sách phù hợp với '{query}'."
        },
        ensure_ascii=False,
    )


def execute_borrow_book(book_id: str, member_id: str) -> str:
    """Mượn sách. Hỗ trợ nhiều thành viên cùng mượn cùng lúc nếu còn bản sao."""
    normalized_book_id = _normalize_book(book_id)
    book = MOCK_DATABASE.get(normalized_book_id)

    if not book:
        return json.dumps(
            {"status": "NOT_FOUND", "message": f"Không tìm thấy sách có mã '{book_id}'."},
            ensure_ascii=False,
        )

    book = _sync_book_state(book)

    if book["available_copies"] <= 0:
        return json.dumps(
            {
                "status": "UNAVAILABLE",
                "message": f"Sách {book['title']} hiện đang không còn bản có sẵn để mượn."
            },
            ensure_ascii=False,
        )

    normalized_member_id = _normalize_member_id(member_id)
    existing_loan = next((item for item in book["borrowers"] if item["member_id"] == normalized_member_id), None)

    if existing_loan:
        return json.dumps(
            {
                "status": "ALREADY_BORROWED",
                "message": f"Thành viên {normalized_member_id} đã đang mượn sách {book['title']}.",
                "data": book
            },
            ensure_ascii=False,
        )

    book["borrowers"].append({
        "member_id": normalized_member_id,
        "due_date": _next_due_date(14),
        "renewals_used": 0
    })
    book = _sync_book_state(book)

    return json.dumps(
        {
            "status": "SUCCESS",
            "message": f"Đã cho thành viên {normalized_member_id} mượn sách {book['title']} thành công. Hạn trả dự kiến: {book['borrowers'][-1]['due_date']}",
            "data": book
        },
        ensure_ascii=False,
    )


def execute_return_book(book_id: str, member_id: str) -> str:
    """Trả sách theo từng thành viên giữ sách."""
    normalized_book_id = _normalize_book(book_id)
    book = MOCK_DATABASE.get(normalized_book_id)

    if not book:
        return json.dumps(
            {"status": "NOT_FOUND", "message": f"Không tìm thấy sách có mã '{book_id}'."},
            ensure_ascii=False,
        )

    book = _sync_book_state(book)
    normalized_member_id = _normalize_member_id(member_id)

    matched = next((item for item in book["borrowers"] if item["member_id"] == normalized_member_id), None)
    if not matched:
        return json.dumps(
            {
                "status": "INVALID_MEMBER",
                "message": f"Thành viên {normalized_member_id} không đang giữ sách {book['title']} nên không thể trả.",
                "data": book
            },
            ensure_ascii=False,
        )

    book["borrowers"] = [item for item in book["borrowers"] if item["member_id"] != normalized_member_id]
    book = _sync_book_state(book)

    return json.dumps(
        {
            "status": "SUCCESS",
            "message": f"Đã ghi nhận thành viên {normalized_member_id} trả sách {book['title']} thành công.",
            "data": book
        },
        ensure_ascii=False,
    )


def execute_renew_book(book_id: str, member_id: str, days: int = 7) -> str:
    """Gia hạn sách cho thành viên đang mượn."""
    normalized_book_id = _normalize_book(book_id)
    book = MOCK_DATABASE.get(normalized_book_id)

    if not book:
        return json.dumps(
            {"status": "NOT_FOUND", "message": f"Không tìm thấy sách có mã '{book_id}'."},
            ensure_ascii=False,
        )

    book = _sync_book_state(book)
    normalized_member_id = _normalize_member_id(member_id)

    matched = next((item for item in book["borrowers"] if item["member_id"] == normalized_member_id), None)
    if not matched:
        return json.dumps(
            {
                "status": "INVALID_MEMBER",
                "message": f"Sách {book['title']} hiện không thuộc quyền mượn của thành viên {normalized_member_id}."
            },
            ensure_ascii=False,
        )

    current_due_date = datetime.strptime(matched["due_date"], "%Y-%m-%d")
    matched["due_date"] = (current_due_date + timedelta(days=days)).strftime("%Y-%m-%d")
    matched["renewals_used"] += 1
    book = _sync_book_state(book)

    return json.dumps(
        {
            "status": "SUCCESS",
            "message": f"Đã gia hạn sách {book['title']} cho thành viên {normalized_member_id} thêm {days} ngày. Hạn mới: {matched['due_date']}",
            "data": book
        },
        ensure_ascii=False,
    )


# Router gọi tool thực tế
TOOL_ROUTER = {
    "lookup_book": execute_lookup_book,
    "borrow_book": execute_borrow_book,
    "return_book": execute_return_book,
    "renew_book": execute_renew_book,
}


def dispatch_tool_call(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Hàm trung chuyển thực thi tool"""
    if tool_name in TOOL_ROUTER:
        try:
            return TOOL_ROUTER[tool_name](**arguments)
        except Exception as e:
            return json.dumps({"status": "EXECUTION_ERROR", "error": str(e)}, ensure_ascii=False)
    return json.dumps({"status": "UNKNOWN_TOOL", "error": f"Tool '{tool_name}' không tồn tại!"}, ensure_ascii=False)
