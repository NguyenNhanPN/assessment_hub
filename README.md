# Assessment Hub — Module Frappe Framework v16 & Partner REST API

Ứng dụng **Assessment Hub** được xây dựng trên nền tảng **Frappe Framework v16**, cung cấp hệ thống quản lý bài đánh giá phân cấp (**Assessment → Question → Answer**) dành cho vận hành nội bộ (Desk UI) và bộ **Partner REST API** bảo mật phục vụ các hệ thống tích hợp bên thứ ba (LMS, HR Portal...).

---

## 1. Hướng Dẫn Cài Đặt (Installation)

### Yêu cầu môi trường chuẩn:
- **Frappe Framework**: `version-16` (hoặc `version-15`)
- **Python**: 3.11+
- **Database**: MariaDB 10.6+ (utf8mb4)
- **Node.js**: 18+ (LTS 20/24), Yarn 1.22+
- **Cache/Queue**: Redis 6+

### Các bước cài đặt:
1. Di chuyển vào thư mục bench của bạn:
   ```bash
   cd /path/to/your/frappe-bench
   ```
2. Tải app vào bench từ repository:
   ```bash
   bench get-app <repo_url> --branch version-16
   ```
3. Cài đặt app lên site mục tiêu:
   ```bash
   bench --site <site_name> install-app assessment_hub
   ```
4. Thực hiện migrate để đồng bộ DocType, Roles và Workspace tự động:
   ```bash
   bench --site <site_name> migrate
   ```

> **Ghi chú về After Install & Fixtures**:
> Khi cài đặt lên site mới, app tự động kích hoạt hook `after_install` và `fixtures` để cấu hình sẵn:
> - Roles: `Assessment Manager`, `Assessment Viewer`
> - Workspaces & Number Cards: `Total Assessments`, `Total Questions`
> - Đảm bảo phân quyền chuẩn mà không cần thao tác thủ công.

---

## 2. Quyết Định Kiến Trúc DocType (Child Table vs Standalone DocType)

Mô hình dữ liệu lựa chọn thiết kế `Assessment Answer` là **Child Table (`istable = 1`)** gắn liền với DocType cha `Question` thay vì Standalone DocType.

### Cơ sở lập luận:
1. **Trải nghiệm Desk (UX) tối ưu**: Người dùng nhập trực tiếp danh sách đáp án, điểm số và sắp xếp thứ tự ngay trên bảng lưới (Grid Table) của Form Question mà không cần mở nhiều pop-up hay rời form.
2. **Bảo toàn toàn vẹn dữ liệu (Lifecycle Integrity)**: Đáp án chỉ có ý nghĩa khi gắn liền với câu hỏi cụ thể. Frappe ORM tự động áp dụng **Cascade Delete** khi câu hỏi bị xóa, triệt tiêu 100% nguy cơ dữ liệu mồ côi (orphaned records) hoặc lỗi ràng buộc khóa ngoại (Foreign Key) khi gỡ app.
3. **Giao dịch nguyên tử (Atomic API Transaction)**: Payload của endpoint `create_question` được gửi dạng JSON lồng nhau (`{"content": "...", "answers": [...]}`). ORM của Frappe tự động bundle Question và danh sách Answers trong cùng một Document Transaction, giúp cơ chế rollback và bảo toàn dữ liệu diễn ra tự nhiên, an toàn và chuẩn Frappe Idiom.

*(Xem chi tiết phân tích chuyên sâu tại file `architecture_decision.md`)*.

---

## 3. Hướng Dẫn Thử Nghiệm Partner REST API

### 3.1. Chuẩn Kết Nối & Xác Thực
- **Base URL**: `/api/method/assessment_hub.api.v1`
- **Cơ chế xác thực**: Token Auth chuẩn của Frappe qua HTTP Header:
  ```http
  Authorization: token <api_key>:<api_secret>
  ```
- **Định dạng phản hồi**:
  - **Thành công (200/201 OK)**:
    ```json
    {"data": ...}
    ```
  - **Thất bại (4xx/5xx)**:
    ```json
    {"errors": [{"message": "Chi tiết lỗi", "code": "ERROR_CODE"}]}
    ```

### 3.2. Tài Khoản & Token Mẫu Để Thử Nghiệm

Bạn có thể sinh nhanh token bằng lệnh:
```bash
bench --site <site_name> execute assessment_hub.api.v1.utils.create_test_credentials
```

Hoặc sử dụng tài khoản mẫu đã tạo:
- **Assessment Manager**:
  - Token: `e0eefa347afe06c1:4338ea41e82be585`
  - Quyền: Quản trị bài đánh giá, thêm/sửa câu hỏi & đáp án, duyệt trạng thái.
- **Assessment Viewer**:
  - Token: `91ab41adf7bb0fd4:21df595b9c839b15`
  - Quyền: Chỉ xem danh sách và chi tiết bài đánh giá/câu hỏi.

---

### 3.3. Chi Tiết Các Endpoints & Lệnh cURL Mẫu

#### Endpoint 1: Danh sách Bài đánh giá
- **Method**: `GET`
- **Route**: `/api/method/assessment_hub.api.v1.assessments.list_assessments`
- **Query params**: `page_length`, `start`, `page`, `status`, `title`, `updated_since`
- **cURL Mẫu**:
  ```bash
  curl -X GET "http://localhost:8000/api/method/assessment_hub.api.v1.assessments.list_assessments?status=Published&page_length=10" \
    -H "Host: <site_name>" \
    -H "Authorization: token 91ab41adf7bb0fd4:21df595b9c839b15"
  ```

#### Endpoint 2: Chi tiết 1 Bài đánh giá (Kèm câu hỏi & đáp án)
- **Method**: `GET`
- **Route**: `/api/method/assessment_hub.api.v1.assessments.get_assessment`
- **Query params**: `id` (bắt buộc), `include_questions` (`1` hoặc `0`)
- **cURL Mẫu**:
  ```bash
  curl -X GET "http://localhost:8000/api/method/assessment_hub.api.v1.assessments.get_assessment?id=ASM-2026-00034&include_questions=1" \
    -H "Host: <site_name>" \
    -H "Authorization: token 91ab41adf7bb0fd4:21df595b9c839b15"
  ```

#### Endpoint 3: Tạo mới Câu hỏi Atomic (Question kèm Answers con)
- **Method**: `POST`
- **Route**: `/api/method/assessment_hub.api.v1.questions.create_question`
- **Yêu cầu Role**: `Assessment Manager`
- **Xử lý Atomic**: Nếu một Answer lỗi (ví dụ thiếu content hoặc score không hợp lệ), rollback toàn bộ Question.
- **cURL Mẫu**:
  ```bash
  curl -X POST "http://localhost:8000/api/method/assessment_hub.api.v1.questions.create_question" \
    -H "Host: <site_name>" \
    -H "Authorization: token e0eefa347afe06c1:4338ea41e82be585" \
    -H "Content-Type: application/json" \
    -d '{
      "assessment": "ASM-2026-00034",
      "content": "Trong Frappe v16, ORM Query Builder chuẩn là gì?",
      "sort_order": 1,
      "status": "Active",
      "answers": [
        {"content": "frappe.qb", "score": 10, "sort_order": 1},
        {"content": "Raw SQL concatenation", "score": 0, "sort_order": 2},
        {"content": "Django ORM", "score": 0, "sort_order": 3}
      ]
    }'
  ```

#### Endpoint 4: Danh sách Câu hỏi thuộc Bài đánh giá
- **Method**: `GET`
- **Route**: `/api/method/assessment_hub.api.v1.questions.list_questions`
- **Query params**: `assessment_id` (bắt buộc)
- **Sắp xếp**: Tăng dần theo `sort_order`
- **cURL Mẫu**:
  ```bash
  curl -X GET "http://localhost:8000/api/method/assessment_hub.api.v1.questions.list_questions?assessment_id=ASM-2026-00034" \
    -H "Host: <site_name>" \
    -H "Authorization: token 91ab41adf7bb0fd4:21df595b9c839b15"
  ```

---

## 4. Chạy Kiểm Thử Tự Động (Automated Tests)

Ứng dụng bao gồm bộ test suite hoàn chỉnh (13 test cases) bao phủ:
- Unit tests cho DocType `Assessment` (status transition, auto-naming expression `ASM-{YYYY}-{#####}`).
- Unit tests cho DocType `Question` (chặn gán vào Archived Assessment, cascade delete child answers).
- Integration tests cho REST API (Authentication 401, Authorization 403, Atomic Transaction rollback, filters & sorting).

Chạy toàn bộ test suite bằng lệnh:
```bash
bench --site <site_name> run-tests --app assessment_hub
```

---

## 5. Postman Collection

File Postman collection mẫu đã được đính kèm tại:
`assessment_hub_postman_collection.json`
Bạn có thể import trực tiếp vào Postman, cấu hình biến `base_url` và `token` để chạy kiểm thử nhanh toàn bộ endpoints.
