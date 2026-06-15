# Backend Tests

## Chạy test

```bash
cd backend
python3.13 -m venv .venv          # Python 3.14 thiếu ensurepip → dùng 3.13
.venv/bin/pip install -r requirements.txt -r requirements-dev.txt
.venv/bin/python -m pytest
```

Test **không cần** PostgreSQL hay Gemini API thật: DB session và `gemini_service` được mock,
HTTP test chạy trực tiếp qua ASGI transport (`httpx.ASGITransport`).

## Cấu trúc

| File | Loại | Phạm vi |
|---|---|---|
| `test_library_service.py` | Unit | Cosine similarity, dựng similarity map, threshold 0.65 |
| `test_auth_tokens.py` | Unit | JWT encode/decode, expiry, refresh token, gemini-key guard |
| `test_gemini_service.py` | Unit | Chunking, parse JSON output (strip ```json fence), stream tokens |
| `test_schemas_config.py` | Unit | Pydantic validation (password, email, file_type), origins parsing |
| `test_auth_api.py` | Integration | `/api/auth/*` — register/login/refresh, status code, cookie |
| `test_qa_api.py` | Integration | `/qa` + `/qa/stream` SSE format, guard 403/400/404 |
| `test_library_api.py` | Integration | `/api/library/similarity-map` |
| `test_documents_api.py` | Integration | CRUD documents, `detect_sections`, validation 422 |

## ⚠️ Lưu ý dependency (BUG đã báo cáo)

`requirements.txt` pin `passlib==1.7.4` nhưng **không pin `bcrypt`** → clean install lấy
`bcrypt==5.0.0`, không tương thích với passlib 1.7.4 (raise `ValueError` khi hash password).
Cần pin `bcrypt==4.0.1` trong `requirements.txt` (hoặc nâng passlib). Xem báo cáo Tester.
Venv test hiện dùng `bcrypt==4.0.1`.
