"""
🚀 CORE AGENT APPLICATION (DAY 03: CHATBOT VS REACT AGENT)
Thực thi so sánh giữa Chatbot Baseline (Cấp 2) và ReAct Agent kết nối MCP Server (Cấp 3).
"""

import json
import os
import sys
import time
from flask import Flask, render_template, request
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from mcp_server import MCPAcademicServer
from prompts import (
    CHATBOT_BASELINE_PROMPT,
    REACT_AGENT_SYSTEM_PROMPT,
    MAX_ITERATIONS
)
from providers import get_llm_provider

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "templates"), static_folder=os.path.join(BASE_DIR, "static"))
provider = get_llm_provider()
mcp_server = MCPAcademicServer()


@app.route("/", methods=["GET", "POST"])
def web_index():
    """Simple browser UI for the library assistant."""
    query = ""
    answer = ""
    logs = []

    if request.method == "POST":
        query = (request.form.get("query") or "").strip()
        if query:
            logs = run_react_agent(query, provider, mcp_server)
            save_waterfall_trace(logs)
            answer = logs[-1]["output"] if logs else ""

    sample_queries = [
        "Tìm vị trí của cuốn sách BK1001 và cho biết tình trạng hiện tại.",
        "Tôi muốn mượn sách BK1002 bằng thẻ thành viên MEM001.",
        "Tôi muốn trả sách BK1002 cho thành viên MEM001.",
        "Gia hạn BK1002 cho MEM001 thêm 7 ngày."
    ]

    return render_template(
        "index.html",
        query=query,
        answer=answer,
        logs=logs,
        sample_queries=sample_queries,
    )


def load_test_cases():
    """Tải danh sách 5 test cases từ config/test_cases.json hoặc config/test_cases.example.json"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    if not os.path.exists(config_path):
        example_path = os.path.join(base_dir, "config", "test_cases.example.json")
        if os.path.exists(example_path):
            print("⚠️ [CONFIG NOTICE]: Chưa thấy file 'config/test_cases.json'. Đang dùng mẫu 'config/test_cases.example.json'.")
            print("👉 Hãy chạy: copy config/test_cases.example.json config/test_cases.json và viết test cases theo đề tài của bạn!\n")
            config_path = example_path
        else:
            config_path = "test_cases.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_waterfall_trace(trace_data: list):
    """Ghi vết log Waterfall Trace Log ra file docs/trace_waterfall.json"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docs_dir = os.path.join(base_dir, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    trace_path = os.path.join(docs_dir, "trace_waterfall.json")
    with open(trace_path, "w", encoding="utf-8") as f:
        json.dump(trace_data, f, ensure_ascii=False, indent=2)
    print(f"📊 [OBSERVABILITY]: Đã lưu {len(trace_data)} sự kiện Waterfall Trace tại '{trace_path}'!")


def run_baseline_chatbot(user_query: str, provider):
    """Chạy Chatbot gốc (Cấp 2) không có công cụ gọi Tool"""
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot phản hồi:\n{response}")


def run_react_agent(user_query: str, provider, mcp_server: MCPAcademicServer) -> list:
    """
    [REACT AGENT LOOP] Thực thi vòng lặp Thought -> Action -> Observation với MCP Server
    Trả về danh sách trace log của phiên thực thi.
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")
    
    step = 0
    trace_logs = []
    tools_list = mcp_server.list_tools()
    
    while step < MAX_ITERATIONS:
        step += 1
        step_start_time = time.time()
        print(f"\n--- 🔄 Vòng lặp ReAct Loop (Step {step}/{MAX_ITERATIONS}) ---")
        
        # Gọi LLM với Native Tool Calling Specs
        llm_response = provider.generate_with_tools(user_query, tools_list, system_prompt=REACT_AGENT_SYSTEM_PROMPT)
        latency_ms = round((time.time() - step_start_time) * 1000, 2)
        
        thought = llm_response.get("thought", "Đang suy luận...")
        print(f"🧠 [Thought]: {thought}")
        
        # Trường hợp 1: LLM quyết định trả lời bằng văn bản trực tiếp
        if llm_response.get("type") == "text":
            final_content = llm_response.get("content", "")
            print(f"🏁 [Final Answer]: {final_content}")
            trace_logs.append({
                "step": step,
                "query": user_query,
                "action_type": "FINAL_ANSWER",
                "thought": thought,
                "output": final_content,
                "latency_ms": latency_ms
            })
            break
            
        # Trường hợp 2: LLM đề xuất gọi Tool (Action)
        elif llm_response.get("type") == "tool_call":
            tool_name = llm_response.get("tool_name")
            arguments = llm_response.get("arguments", {})
            
            print(f"🛠️ [Action Proposed]: {tool_name}({arguments})")
            
            # Thực thi Tool qua MCP Server
            mcp_result = mcp_server.call_tool(tool_name, arguments)
            obs_data = mcp_result.get("result", {})
            
            if not obs_data:
                print(f"👁️ [Observation từ MCP Server]: {{}}")
                print(f"⚠️ [CHÚ Ý]: MCP Server trả về kết quả rỗng! Học viên cần hoàn thành TODO 2.1 trong 'src/mcp_server.py'.")
                final_answer = "Chưa thể trả lời chi tiết do chưa nhận được dữ liệu từ MCP Server (hãy hoàn thành TODO 2.1)."
            else:
                obs_str = json.dumps(obs_data, ensure_ascii=False)
                print(f"👁️ [Observation từ MCP Server]: {obs_str}")
                
                # Tổng hợp Final Answer từ kết quả Observation thực tế
                if obs_data.get("status") == "SUCCESS":
                    if isinstance(obs_data.get("data"), list):
                        items = obs_data["data"]
                        snippets = []
                        for item in items:
                            snippets.append(
                                f"{item.get('book_id', '')} - {item.get('title', '')} ({item.get('location', '')})"
                            )
                        final_answer = f"Tìm thấy {len(items)} sách phù hợp: {'; '.join(snippets)}."
                    elif isinstance(obs_data.get("data"), dict):
                        d = obs_data["data"]
                        if "title" in d:
                            borrower_ids = d.get("borrower_ids") or []
                            borrower_text = ", ".join(borrower_ids) if borrower_ids else "chưa có"
                            if len(borrower_ids) > 1:
                                borrower_text = f"{len(borrower_ids)} thành viên ({', '.join(borrower_ids)})"
                            final_answer = (
                                f"Sách {d.get('title', '')} ({d.get('book_id', '')}) đang ở {d.get('location', '')}. "
                                f"Tình trạng: {d.get('status', '')}, còn {d.get('available_copies', 0)} bản có sẵn, "
                                f"người đang giữ: {borrower_text}."
                            )
                        else:
                            final_answer = obs_data.get("message", json.dumps(obs_data, ensure_ascii=False))
                    elif "message" in obs_data:
                        final_answer = obs_data["message"]
                    else:
                        final_answer = f"Đã hoàn tất xử lý qua MCP Server: {json.dumps(obs_data, ensure_ascii=False)}"
                elif obs_data.get("status") in {"NOT_FOUND", "UNAVAILABLE", "INVALID_MEMBER", "ALREADY_RETURNED", "INVALID_ARGUMENT"}:
                    final_answer = obs_data.get("message", "Không thể xử lý yêu cầu với dữ liệu hiện có.")
                else:
                    final_answer = f"Phản hồi từ công cụ: {json.dumps(obs_data, ensure_ascii=False)}"
            
            trace_logs.append({
                "step": step,
                "query": user_query,
                "action_type": "TOOL_EXECUTION",
                "tool_name": tool_name,
                "arguments": arguments,
                "observation": obs_data,
                "latency_ms": latency_ms
            })
            
            # Kết thúc vòng lặp sau khi hoàn tất Observation và xuất Final Answer
            print(f"🧠 [Thought]: Đã nhận được dữ liệu từ MCP Server. Tổng hợp kết quả phản hồi.")
            print(f"🏁 [Final Answer]: {final_answer}")
            
            trace_logs.append({
                "step": step + 1,
                "query": user_query,
                "action_type": "FINAL_ANSWER",
                "thought": "Tổng hợp kết quả từ MCP Server thành công.",
                "output": final_answer,
                "latency_ms": 10.0
            })
            break

    return trace_logs


if __name__ == "__main__":
    if "--web" in sys.argv:
        print("==========================================================")
        print("🌐 KHỞI ĐỘNG WEB UI CHO LIBRARY AGENT")
        print("==========================================================")
        print("🧭 Mở trình duyệt tại http://127.0.0.1:3000")
        app.run(host="0.0.0.0", port=3000, debug=True)
        raise SystemExit

    print("==========================================================")
    print("🏫 VINUNI AI COURSE - DAY 03 LAB: CHATBOT VS REACT AGENT")
    print("==========================================================")
    
    print(f"🔌 LLM Provider: {provider.__class__.__name__}")
    print(f"🌐 MCP Server: {mcp_server.server_name}\n")
    
    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases thử nghiệm.\n")
    
    if "--interactive" in sys.argv:
        print("🎮 [INTERACTIVE MODE] Trò chuyện trực tiếp với ReAct Agent:")
        print("💡 Gợi ý câu hỏi thử nghiệm:")
        print("   - Câu hỏi chung: 'Mượn sách tối đa bao nhiêu ngày?' ")
        print("   - Tra cứu sách: 'Tìm vị trí của cuốn sách BK1001 và cho biết tình trạng hiện tại.'")
        print("   - Mượn sách: 'Tôi muốn mượn sách BK1002 bằng thẻ thành viên MEM001.'")
        print("   - Gõ 'exit' hoặc 'quit' để kết thúc phiên trò chuyện.\n")
        while True:
            try:
                user_input = input("👤 Người dùng hỏi: ").strip()
                if not user_input or user_input.lower() in ["exit", "quit"]:
                    print("👋 Tạm biệt! Kết thúc phiên trò chuyện.")
                    break
                logs = run_react_agent(user_input, provider, mcp_server)
                save_waterfall_trace(logs)
            except (KeyboardInterrupt, EOFError):
                print("\n👋 Đã thoát phiên tương tác.")
                break
    elif "--all" in sys.argv:
        print("🚀 [TEST SUITE MODE] Kiểm tra 5 Test Cases:")
        completed_count = 0
        todo_count = 0
        all_traces = []
        
        for tc in tests:
            print(f"\n==================================================")
            print(f"🧪 [{tc['id']}] Loại test: {tc['type']} (Độ phức tạp: {tc['complexity']})")
            print(f"📌 Kỳ vọng: {tc['expected_behavior']}")
            
            if tc["question"].strip().startswith("TODO"):
                print(f"⏸️ [CHƯA KÍCH HOẠT - ĐANG LÀ TODO]:")
                print(f"   {tc['question']}")
                print(f"   👉 Hãy mở file 'config/test_cases.json' để viết câu hỏi thực tế cho Test Case này!")
                todo_count += 1
            else:
                logs = run_react_agent(tc["question"], provider, mcp_server)
                all_traces.extend(logs)
                completed_count += 1
                
        print(f"\n==================================================")
        print(f"📊 [KẾT QUẢ TEST SUITE]: Đã thực thi {completed_count}/{len(tests)} Test Cases | {todo_count} Test Cases đang chờ điền câu hỏi (TODO)")
        if all_traces:
            save_waterfall_trace(all_traces)
        print(f"💡 Để trò chuyện trực tiếp từng câu: Chạy 'python src/app.py --interactive'")
    else:
        # Chế độ mặc định khi chỉ gõ 'python src/app.py'
        print("ℹ️ HƯỚNG DẪN SỬ DỤNG CHƯƠNG TRÌNH:")
        print("  1. Mở Web UI:                 python src/app.py --web")
        print("  2. Chat trực tiếp liên tục:    python src/app.py --interactive")
        print("  3. Chạy toàn bộ Test Cases:   python src/app.py --all\n")
        
        sample_query = tests[1]["question"]
        print(f"--- 🏁 DEMO CHẠY THỬ 1 TEST CASE MẪU (TC02: Tra cứu sách) ---")
        logs = run_react_agent(sample_query, provider, mcp_server)
        save_waterfall_trace(logs)
        print("\n💡 Hãy thử ngay lệnh: python src/app.py --interactive hoặc python src/app.py --web")
