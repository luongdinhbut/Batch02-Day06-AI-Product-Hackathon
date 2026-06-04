# HaNoi Guide - AI Travel Itinerary Chatbot

> Day 06 AI Product Hackathon - Track: Travel & Hospitality

> Nhóm: B2

> Sản phẩm: chatbot AI tạo lịch trình 1 ngày cho khách lần đầu đến Hà Nội.

## Thành Viên

| Mã học viên | Họ và tên | Git author / bằng chứng commit |
|---|---|---|
| 2A202600920 | Nguyễn Hải An | `AnOreo0207 <pejij2009@gmail.com>` |
| 2A202600865 | Lương Đình Bút | `luongdinhbut <luongdinhbutdv1234@gmail.com>` |
| 2A202600964 | Đoàn Thị Thu Linh | `ThuLinh3009 <linhdoanarmy3009@gmail.com>` |
| 2A202600885 | Nguyễn Duy Đức | `duyduc/cocooda <ddnguyen4779@gmail.com/bachduc.june@gmail.com>` |
| 2A202600554 | Lê Văn Quang | `dangquangmedia <25410011@ms.uit.edu.vn>` |

## Mô Tả Ngắn

**HaNoi Guide** giúp khách du lịch lần đầu đến Hà Nội lên lịch trình trong vài phút thay vì tự ghép thông tin từ Google Maps, Foody, TripAdvisor và blog du lịch.

Chatbot hỏi 5 câu về sở thích ăn uống, loại điểm tham quan, phong cách trải nghiệm, ngân sách và ngày đến. Sau đó hệ thống dùng AI kết hợp với dataset Hà Nội gồm **179 records** để tạo lịch trình 1 ngày theo khung sáng, trưa, chiều, tối và đêm nếu user muốn nightlife.

Điểm quan trọng của prototype là không chỉ tạo lịch trình đẹp, mà còn có guardrail để tránh các lỗi demo chính: input mơ hồ, AI gợi ý địa điểm đóng cửa, AI gợi ý ngoài dataset, hoặc user muốn chỉnh lịch trình sau khi đã có kết quả.

## Product Canvas

| Mục | Nội dung |
|---|---|
| Target user | Khách du lịch lần đầu đến Hà Nội, chuẩn bị chuyến đi 1-2 ngày |
| Pain point | User thiếu context địa phương, phải tự lọc quá nhiều nguồn, dễ chọn nơi không hợp lifestyle hoặc nơi đóng cửa |
| Insight | Người mới đến Hà Nội thường không biết phải hỏi "đi đâu"; họ dễ trả lời hơn nếu chatbot hỏi theo habit: ăn gì, thích vibe nào, ngân sách bao nhiêu |
| Solution | Chatbot hỏi 5 preference questions rồi tạo lịch trình cá nhân hóa dựa trên dataset địa điểm thật |
| AI role | AI draft lịch trình và xử lý correction; Python guardrail kiểm tra output trước khi trả cho user |
| Data asset | `codebase/data/hanoi_places.json`: 55 places, 71 restaurants, 53 bars |
| Core value | Lịch trình gộp tham quan + ăn uống + nightlife, có thời gian, giá tham khảo, rating, district và warning |
| Human control | User có thể yêu cầu chỉnh lịch trình mà không phải trả lời lại từ đầu |
| Failure handling | Hỏi lại khi input mơ hồ, cảnh báo địa điểm đóng cửa, retry khi AI output không an toàn, fallback local khi provider lỗi |
| Demo win | Show được happy path, AI uncertain path, closed-place path và user correction path |

## Tính Năng Hiện Có

- Chatbot hỏi đủ 5 câu preference theo flow trong SPEC.
- Backend FastAPI có API `/api/start`, `/api/chat`, `/api/closed-places`.
- Frontend Next.js hiển thị chat, sidebar preference cards, warning địa điểm đóng cửa và nút reset.
- Gọi AI thật qua Fireworks, Gemini hoặc custom OpenAI-compatible endpoint.
- Có local fallback itinerary khi thiếu API key hoặc AI provider lỗi.
- Validator sau LLM kiểm tra required time blocks, địa điểm ngoài dataset, địa điểm đóng cửa, budget mismatch, nightlife không phù hợp.
- Nếu AI trả kết quả không an toàn, hệ thống retry một lần với feedback rồi mới fallback.
- Closed-place guardrail dùng `closed_on` trong dataset và gợi ý alternative cùng category / district / area.
- Correction mode: sau khi có itinerary, user có thể yêu cầu đổi khu vực, thêm/bỏ quán ăn, bỏ nightlife... mà không restart onboarding.
- Có test cho provider config, fallback, closed-place detection và itinerary validator.
- Vẫn giữ `app.py` Streamlit như prototype cũ, nhưng flow chính hiện tại là FastAPI + Next.js.

## Demo Paths

| Path | Cách demo | Kết quả mong đợi |
|---|---|---|
| Happy path | Trả lời rõ 5 câu: street food, văn hóa, local, 700k, đi thứ 7 | AI tạo lịch trình 1 ngày có sáng/trưa/chiều/tối, nếu có nightlife thì thêm đêm |
| AI uncertain | Trả lời kiểu "ăn gì cũng được", "tùy bạn" | Bot hỏi lại một câu cụ thể thay vì tự tin tạo lịch trình |
| AI wrong / closed place | Chọn đi thứ 2, ưu tiên văn hóa/lịch sử | Sidebar và itinerary cảnh báo các điểm đóng cửa, đề xuất nơi thay thế đang mở |
| User correction | Sau itinerary, nhập "bỏ bar, đổi chiều sang Tây Hồ" | Bot cập nhật lịch trình dựa trên context cũ, không hỏi lại 5 câu |

## Tech Stack

| Layer | Công nghệ | Ghi chú |
|---|---|---|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS | UI chính trong `codebase/frontend` |
| Backend API | FastAPI, Uvicorn, Pydantic | Entry point `codebase/main.py` |
| Legacy UI | Streamlit | Entry point phụ `codebase/app.py` |
| AI provider | Fireworks AI, Gemini, Custom OpenAI-compatible | Chọn qua `LLM_PROVIDER` |
| Data | Local JSON | `codebase/data/hanoi_places.json` |
| Tests | Python `unittest` | `codebase/tests/test_itinerary.py` |

## Cấu Trúc Repo

```txt
Batch02-Day06-AI-Product-Hackathon/
|-- README.md
|-- AGENTS.md
|-- hackathon-rules.md
|-- spec.md
|-- project_overview.md
|-- spec/
|   |-- README.md
|   `-- spec.md
`-- codebase/
    |-- README.md
    |-- requirements.txt
    |-- main.py
    |-- app.py
    |-- data/
    |   `-- hanoi_places.json
    |-- src/
    |   |-- agent/
    |   |   `-- itinerary_agent.py
    |   |-- core/
    |   |   |-- llm.py
    |   |   `-- schemas.py
    |   |-- services/
    |   |   |-- chat_engine.py
    |   |   |-- data_loader.py
    |   |   |-- failure_checker.py
    |   |   |-- fallback_builder.py
    |   |   |-- itinerary_validator.py
    |   |   |-- onboarding.py
    |   |   |-- preference_mapper.py
    |   |   `-- prompt_builder.py
    |   `-- utils/
    |       `-- date_utils.py
    |-- tests/
    |   |-- test_cases.md
    |   `-- test_itinerary.py
    `-- frontend/
        |-- package.json
        |-- public/
        |   `-- robot.jpg
        `-- src/
            `-- app/
                |-- page.tsx
                |-- globals.css
                `-- layout.tsx
```

## Cách Chạy Demo

### 1. Backend FastAPI

```powershell
cd codebase
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Backend chạy tại:

```txt
http://localhost:8000
```

### 2. Frontend Next.js

Mở terminal khác:

```powershell
cd codebase\frontend
npm install
npm run dev
```

Frontend chạy tại:

```txt
http://localhost:3000
```

### 3. Cấu Hình AI

Không có API key thì app vẫn chạy bằng fallback local. Để demo flow có AI call thật, tạo `.env` trong `codebase/`.

Fireworks:

```env
LLM_PROVIDER=fireworks
FIREWORKS_API_KEY=your_key_here
FIREWORKS_MODEL=accounts/fireworks/models/deepseek-v4-pro
```

Gemini:

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.0-flash
```

Multi-provider fallback:

```env
LLM_PROVIDER=fireworks,gemini
FIREWORKS_API_KEY=your_fireworks_key
GEMINI_API_KEY=your_gemini_key
```

Custom OpenAI-compatible endpoint:

```env
LLM_PROVIDER=custom
CUSTOM_API_KEY=your_key_here
CUSTOM_BASE_URL=https://your-provider.example.com/v1
CUSTOM_MODEL=your_model_name
```

## Test

```powershell
cd codebase
python -m unittest discover -s tests
```

## Ghi Chú Quan Trọng

- `README.md` này là file nộp bài chính theo hướng dẫn hackathon.
- `project_overview.md` là bản nháp tổng quan cũ, chưa nên dùng làm tài liệu nộp chính.
- Prototype hiện chưa render ảnh riêng cho từng địa điểm trong itinerary; không nên claim tính năng này khi demo.
