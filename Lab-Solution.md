# Báo Cáo Giải Quyết Lab & Lý Thuyết Day 09

**Học viên:** Trần Quốc Khánh  
**Mã học viên:** 2A202600679  
**Dự án:** Multi-Agent A2A System

---

## PHẦN 1: DIRECT LLM CALLING

### Câu 1: LLM được khởi tạo như thế nào? (Tìm hàm `get_llm()`)
Trong file `common/llm.py`, LLM được khởi tạo bằng class `ChatOpenAI` từ thư viện `langchain_openai`. 
- Nếu phát hiện biến môi trường `nvida_key` tồn tại và không rỗng, hệ thống sẽ kết nối đến **Nvidia NIM API** (`https://integrate.api.nvidia.com/v1`) với mô hình mặc định là `meta/llama-3.1-8b-instruct`.
- Ngược lại, hệ thống sẽ kết nối đến **OpenRouter API** (`https://openrouter.ai/api/v1`) thông qua API Key của OpenRouter và sử dụng model mặc định là `openai/gpt-4o`.

### Câu 2: Message được gửi đến LLM có cấu trúc gì?
Message được gửi đi dưới dạng một mảng (list) chứa các đối tượng Message của LangChain, tuân theo cấu trúc phân vai:
- `SystemMessage`: Chứa chỉ dẫn hệ thống định cấu hình hành vi của AI.
- `HumanMessage`: Chứa nội dung yêu cầu hoặc câu hỏi từ người dùng.
- `AIMessage`: Phản hồi của mô hình (nếu có lịch sử hội thoại).

### Câu 3: Tại sao cần có `SystemMessage` và `HumanMessage`?
- **SystemMessage**: Thiết lập bối cảnh nền tảng, định hình tính cách, phân vai và quy tắc ràng buộc chung cho mô hình (ví dụ: ngôn ngữ trả lời, định dạng trích dẫn, cách xử lý khi thiếu thông tin). Nó giúp kiểm soát chất lượng câu trả lời ổn định.
- **HumanMessage**: Chứa nội dung câu hỏi cụ thể của người dùng ở lượt hội thoại hiện tại. Việc phân tách giúp mô hình phân biệt rõ ràng đâu là hướng dẫn hệ thống (độ ưu tiên cao nhất) và đâu là dữ liệu đầu vào cần xử lý.

---

## PHẦN 2: LLM + RAG & TOOLS

### Câu 1: Hàm `@tool` decorator được dùng ở đâu?
Hàm `@tool` decorator được sử dụng phía trên định nghĩa các hàm Python trong các module exercises (ví dụ: `exercises/exercise_2_tools.py`) để chuyển đổi các hàm Python thông thường thành các đối tượng Tool của LangChain. Các đối tượng này tự động tạo schema JSON dựa trên docstring và kiểu dữ liệu tham số để LLM có thể đọc và hiểu cách gọi.

### Câu 2: `LEGAL_KNOWLEDGE` được cấu trúc như thế nào?
`LEGAL_KNOWLEDGE` là một danh sách chứa các dictionary đóng vai trò là một cơ sở kiến thức tĩnh. Mỗi entry gồm:
- `id`: Mã định danh duy nhất của kiến thức.
- `keywords`: Mảng từ khóa để so khớp tìm kiếm nhanh.
- `text`: Nội dung văn bản pháp luật chi tiết được sử dụng làm ngữ cảnh.

### Câu 3: LLM được bind với tools ra sao?
LLM liên kết với tools thông qua phương thức `.bind_tools()` trên đối tượng model:
```python
llm_with_tools = llm.bind_tools(tools)
```
Sau khi bind, LLM sẽ nhận thức được danh sách công cụ khả dụng và có khả năng trả về một `tool_calls` chứa tên tool và đối số tương ứng khi xử lý câu hỏi.

---

## PHẦN 4: MULTI-AGENT IN-PROCESS

### Bài Tập 4.1 & 4.2: Thêm Privacy Agent và Conditional Routing
Tôi đã bổ sung trường `privacy_analysis` vào shared `State` của LangGraph, cài đặt `privacy_agent` chuyên trách GDPR và bảo vệ dữ liệu cá nhân, đồng thời cập nhật hàm `check_routing` để chuyển tiếp tác vụ đến `privacy_agent` khi câu hỏi chứa các từ khóa liên quan như `"data"`, `"privacy"`, `"gdpr"`, `"dữ liệu"`. 
*(Code chi tiết đã được cập nhật và chạy thử nghiệm thành công trong [exercises/exercise_4_multiagent.py](file:///a:/AIK20_aithucchien/Batch02-Day9_Multi-Agent_MCP-A2A/exercises/exercise_4_multiagent.py))*

---

## PHẦN 5: DISTRIBUTED A2A SYSTEM

### Bài Tập 5.1: Request Flow Sequence Diagram

```
User          CustomerAgent       Registry         LawAgent        TaxAgent     ComplianceAgent
 |                 |                  |                |               |               |
 |--- 1. Hỏi ---->|                  |                |               |               |
 |                 |--- 2. Discover ->|                |               |               |
 |                 |<-- 3. Endpoint --|                |               |               |
 |                 |                                  |               |               |
 |                 |----------- 4. Giao tiếp A2A ---->|               |               |
 |                 |                                  |--5. Discover->|               |
 |                 |                                  |<--6. Endpoint-|               |
 |                 |                                  |                               |
 |                 |                                  |----------- 7. A2A ----------->|
 |                 |                                  |<---------- 8. Trả về ---------|
 |                 |                                  |                               |
 |                 |                                  |--9. Discover----------------->|
 |                 |                                  |<--10. Endpoint----------------|
 |                 |                                  |                               |
 |                 |                                  |----------- 11. A2A ---------->|
 |                 |                                  |<---------- 12. Trả về --------|
 |                 |                                  |                               |
 |                 |<---------- 13. Kết quả ----------|                               |
 |<-- 14. Trả lời -|                                  |                               |
```

### Bài Tập 5.2: Test Dynamic Discovery
Khi tắt `Tax Agent` đột ngột:
- `Law Agent` vẫn nhận diện được nhiệm vụ cần gọi Tax Agent từ luồng suy nghĩ.
- Nó gửi yêu cầu mạng đến endpoint lấy từ Registry nhưng thất bại do dịch vụ không hoạt động.
- Cơ chế bắt ngoại lệ trong `graph.py` của Law Agent giữ cho hệ thống không bị crash, ghi nhận lỗi phân tích thuế và tiếp tục tổng hợp kết quả dựa trên dữ liệu từ Compliance Agent.

---

## PHẦN 6: TỔNG KẾT & CÂU HỎI ÔN TẬP

### 1. Khi nào nên dùng single agent thay vì multi-agent?
- **Nên dùng Single Agent**: Khi tác vụ đơn giản, thẳng luồng, số lượng công cụ bổ trợ ít (dưới 5-10 công cụ). Điều này giúp tối ưu hóa latency (không mất thời gian chuyển tiếp mạng giữa các agent) và tiết kiệm chi phí token do prompt đơn giản hơn.
- **Nên dùng Multi-Agent**: Khi hệ thống cần xử lý đa domain phức tạp (pháp lý, thuế, kiểm toán), mỗi domain cần prompt chuyên biệt và tập công cụ lớn. Việc tách thành nhiều Agent giúp tránh hiện tượng mô hình bị loãng thông tin, nhầm lẫn công cụ và dễ dàng kiểm thử, nâng cấp độc lập từng agent.

### 2. Ưu điểm của A2A protocol so với gRPC hoặc REST thông thường?
- A2A định nghĩa sẵn cấu trúc truyền dữ liệu ngữ cảnh chuyên biệt cho AI (như `trace_id` để theo dõi vết, `context_id` để giữ phiên hội thoại, `delegation_depth` để chống lặp đệ quy).
- Standard hóa các khái niệm: `Task`, `Message`, `Artifact` giúp các hệ thống Agent viết bằng các ngôn ngữ khác nhau có thể dễ dàng hiểu và tích hợp trực tiếp mà không cần thiết kế lại giao thức truyền thông điệp ở tầng ứng dụng.

### 3. Làm thế nào để prevent infinite delegation loops trong A2A?
Giao thức A2A sử dụng trường `delegation_depth` trong metadata của message. Mỗi lần một Agent gửi yêu cầu ủy thác đến Agent khác, độ sâu này tăng thêm 1. Khi một Agent nhận được request có `delegation_depth` vượt quá cấu hình an toàn tối đa (ví dụ: `MAX_DELEGATION_DEPTH = 3`), nó sẽ từ chối xử lý và báo lỗi, cắt đứt vòng lặp vô hạn.

### 4. Tại sao cần Registry service? Có thể hardcode URLs không?
Registry đóng vai trò là danh bạ động (Service Discovery). Nó cho phép các Agent tự đăng ký địa chỉ khi khởi động và tự hủy khi tắt. Nếu hardcode URLs:
- Hệ thống sẽ mất tính linh hoạt, không thể tự phục hồi khi có sự thay đổi về hạ tầng mạng, thay đổi cổng hoặc IP.
- Không thể mở rộng quy mô (scale-out) nhiều thực thể Agent để chạy cân bằng tải (load balancing).

---

## BÀI TẬP CỘNG ĐIỂM (LATENCY OPTIMIZATION)

### 1. Chỉ số Latency mặc định
- **Đo lường ban đầu**: **67.90 giây** để hoàn thành chu trình.
- **Nguyên nhân chính**: Việc sử dụng một LLM Node riêng biệt để định tuyến các agent chuyên trách (`tax_agent`, `compliance_agent`) tiêu tốn 10 - 15 giây gọi mạng và xử lý prompt.

### 2. Phương án tối ưu hóa & Kết quả
- **Đề xuất**: Thay thế LLM Routing bằng **Rule-based Keyword Routing** trong `law_agent/graph.py` dùng các biểu thức chính quy (Regex) hoặc tìm kiếm từ khóa trực tiếp trên câu hỏi người dùng.
- **Kết quả thực tế**: Latency giảm xuống còn **56.96 giây** (tiết kiệm được **10.94 giây**, cải thiện hiệu năng ~16%).
- **Demo**: Giao diện điều khiển Web Console (Vite/React) tích hợp sẵn nút bật/tắt tối ưu hóa này để so sánh trực tiếp số lượng hops giảm từ 6 xuống 4 và latency tức thời.
