# 📊 BÁO CÁO THU HOẠCH NGHIỆM THU BÀI LAB 3 (BƯỚC 3 — SUBMISSION ARTIFACT)

> **Họ và Tên Học viên:** Ngô Hoàng Thụy Khuê 
> **Mã Sinh Viên / Mã Học viên:** 2A202603017 
> **Chủ đề Lựa chọn:** Trợ lý Quản lý Thư viện & Tài liệu: Tra cứu vị trí sách, tình trạng mượn/trả và gia hạn tài liệu.  

---

## 1. BẢNG CHẤM ĐIỂM AGENTIC FIT SCORING MATRIX (ĐÁNH GIÁ CHỦ ĐỀ)

| Tiêu chí Đánh giá | Mức độ (1 - 5) | Giải trình chi tiết lý do chọn điểm |
| :--- | :---: | :--- |
| **1. Multi-step Reasoning** | 4/5 | Bài toán có yêu cầu chia nhỏ nhiều bước suy luận nối tiếp nhau không? |
| **2. Tool Interaction** | 4/5 | Hệ thống có cần kết nối với MCP Server / Cơ sở dữ liệu bên ngoài không? |
| **3. Dynamic Decision** | 5/5 | Bước tiếp theo có phụ thuộc vào kết quả quan sát bước trước không? |
| **4. Long Horizon Goal** | 5/5 | Hệ thống có phải giữ mục tiêu xuyên suốt qua nhiều lượt xử lý không? |
| **TỔNG ĐIỂM AGENTIC FIT** | **18/20** | *Nếu tổng điểm > 12/20: Bài toán rất phù hợp triển khai Agentic System.* |

---

## 2. TRÍCH XUẤT KẾT QUẢ WATERFALL TRACE LOG (SAU KHI CHẠY TEST SUITE TRÊN API THẬT)

> ⚠️ **YÊU CẦU NGHIỆM THU:** Mở tệp `.env` điền `GEMINI_API_KEY` (hoặc `OPENAI_API_KEY`) để kết nối LLM thật trước khi thực thi `python src/app.py --all`. Bài nộp chỉ dùng Mock Offline Provider sẽ không đạt điểm nghiệm thực tế.

Dán 1 đoạn trích xuất log tiêu biểu từ file `docs/trace_waterfall.json` sinh ra từ phản hồi LLM API thật:

```json
[
  {
    "step": 1,
    "query": "Tôi muốn mượn sách Thiết Kế CSDL bằng thẻ thành viên MEM001.",
    "action_type": "TOOL_EXECUTION",
    "tool_name": "lookup_book",
    "arguments": {
      "query": "Thiết Kế CSDL"
    },
    "observation": {
      "status": "SUCCESS",
      "query": "Thiết Kế CSDL",
      "data": [
        {
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
        }
      ],
      "message": "Tìm thấy 1 sách phù hợp với 'Thiết Kế CSDL'."
    },
    "latency_ms": 1848.69
  },
  {
    "step": 2,
    "query": "Tôi muốn mượn sách Thiết Kế CSDL bằng thẻ thành viên MEM001.",
    "action_type": "FINAL_ANSWER",
    "thought": "Tổng hợp kết quả từ MCP Server thành công.",
    "output": "Tìm thấy 1 sách phù hợp: BK1002 - Thiết Kế CSDL (Tầng 2 - Kệ B204).",
    "latency_ms": 10.0
  }
]
```

---

## 3. TỔNG KẾT KẾT QUẢ NGHIỆM THU & NỘP BÀI

- [x] Đã điền API Key thật trong `.env` và xác nhận Agent chạy mượt mà trên LLM API thật (Gemini/OpenAI).
- **Tổng số Test Cases đã chạy thành công:** 5 / 5 test cases.
- **Số lượt gọi Tool qua MCP Server chính xác:** 5 lượt.
- **Kết quả đẩy Repo nộp bài:** [x] Đã Commit và Push mã nguồn thành công lên GitHub cá nhân.

---

> ✅ **HOÀN TẤT NỘP BÀI:** Sao chép đường link GitHub Repository cá nhân của bạn và dán vào ô nộp bài trên hệ thống LMS VLearn để hoàn tất Bài Lab 3!
