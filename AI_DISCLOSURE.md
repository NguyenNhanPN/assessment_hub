# Bản Công Bố Sử Dụng AI (AI Disclosure)
> **Dự án**: Assessment Hub — Module Frappe Framework v16 & Partner REST API  
> **Cấp bậc đánh giá**: Full Module Frappe Developer  
> **Mục tiêu**: Minh bạch công cụ hỗ trợ, prompt mẫu và quy trình kiểm soát chất lượng mã nguồn.

---

## 1. Công Cụ Hỗ Trợ Sử Dụng

Trong quá trình phân tích và xây dựng ứng dụng, các công cụ AI và IDE sau đã được sử dụng:
- **Công cụ AI chính**: Antigravity AI Coding Assistant (mô hình Gemini 3.8 Flash)
- **Môi trường IDE**: VS Code & Terminal Command Line Tools
- **Framework & Runtime**: Frappe Framework v16, Python 3.11+, MariaDB 10.6+, Redis

---

## 2. Các Prompt Mẫu Đã Sử Dụng

### Prompt 1: Phân tích tài liệu yêu cầu & Lập kế hoạch kiến trúc
> *"Đọc và phân tích yêu cầu trong file Bai_Test_Frappe16_Assessment_Module.pdf. Lập file kế hoạch implement.md chi tiết theo thứ tự từ trên xuống dưới bao gồm mô hình DocType, phân quyền Roles, tự động hóa fixtures/hooks và chuẩn Partner REST API Contract."*

### Prompt 2: So sánh kiến trúc Child Table vs Standalone DocType
> *"Phân tích ưu và nhược điểm giữa 2 phương án: Assessment Answer là Child Table của Question hay DocType độc lập có Link field? Đánh giá theo tiêu chuẩn Frappe Desk UX, toàn vẹn dữ liệu CSDL và Atomic REST API transaction."*

### Prompt 3: Thiết kế Naming Rule tự động theo Expression
> *"Thiết lập Naming Rule tự sinh mã theo Expression cho Assessment (dạng ASM-YYYY-#####) và Question (dạng QST-#####) chuẩn theo engine naming của Frappe v16."*

### Prompt 4: Xử lý Atomic Transaction và Response Wrapper cho REST API
> *"Xây dựng API decorator để chuẩn hóa phản hồi REST API: Thành công trả về `{"data": ...}`, thất bại trả về `{"errors": [{"message": "...", "code": "..."}]}`, bắt buộc Token Auth và thực hiện Atomic Transaction với `frappe.db.savepoint` khi tạo Question kèm Answers."*

---

## 3. Các Phần Mã Nguồn Được Lập Trình Viên Trực Tiếp Rà Soát, Tinh Chỉnh & Kiểm Thử

Mặc dù có sự hỗ trợ của công cụ AI để sinh khung sườn (boilerplate), toàn bộ các phần cốt lõi sau đây đã được **lập trình viên trực tiếp review, tinh chỉnh kỹ thuật và kiểm chứng thực tế trên hệ thống**:

1. **Cơ chế Naming Expression trên Frappe v16**:
   - *Vấn đề phát hiện*: Chuỗi `format:ASM-.YYYY.-.#####` không kích hoạt regex biến đổi của Frappe do thiếu dấu ngoặc nhọn `{...}` dẫn đến lưu chuỗi thô.
   - *Tinh chỉnh*: Trực tiếp debug mã nguồn `frappe/model/naming.py`, chuyển sang đúng cú pháp `format:ASM-{YYYY}-{#####}` và `format:QST-{#####}`.
2. **Xử lý Response Format & Werkzeug Response**:
   - *Vấn đề*: Frappe mặc định bọc dữ liệu trả về trong `{"message": ...}`.
   - *Tinh chỉnh*: Sử dụng trực tiếp Werkzeug `Response` trong decorator `@partner_api` để trả về định dạng chuẩn xác `{"data": ...}` và `{"errors": [...]}` kèm các mã HTTP Status Code (200, 201, 400, 401, 403, 404, 500).
3. **Cơ chế Atomic Rollback**:
   - Tinh chỉnh savepoint `create_question_sp` và rollback an toàn để khi bất kỳ Answer nào gặp lỗi, toàn bộ Question không bị ghi vào DB.
4. **Viết và chạy toàn bộ Bộ Kiểm Thử Tự Động (Integration Tests)**:
   - Viết 13 integration test cases và trực tiếp chạy kiểm thử thực tế trên MariaDB qua lệnh `bench --site frappe.v16 run-tests --app assessment_hub`, đảm bảo 100% tests đạt trạng thái **PASS**.
