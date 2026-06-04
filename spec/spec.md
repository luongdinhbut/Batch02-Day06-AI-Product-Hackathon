# SPEC Day 06

> Nhóm: 5
> Thành viên: Nguyễn Hải An · Lương Đình Bút · Đoàn Thị Thu Linh · Nguyễn Duy Đức · Lê Văn Quang
> Ngày: Day 06

---

## 1. Bằng chứng

### Track, product và user

- **Track:** Travel / Du lịch
- **Product/app thật:** Chatbot AI gợi ý lịch trình tham quan + ăn uống + nightlife tại Hà Nội
- **User cụ thể:** Khách du lịch lần đầu đến Hà Nội, đang lên kế hoạch chuyến đi 1–2 ngày
- **Nguồn bằng chứng:** quan sát thực tế nhóm, review Google Maps Văn Miếu, comment YouTube, group Facebook "Du lịch HN tự túc", forum TripAdvisor, self-use Vietnam Tourism DB + Foody

### Tóm tắt bằng chứng chính

| Evidence | Nguồn | Ý nghĩa cho SPEC |
|---|---|---|
| "Không biết chỗ ăn ngon thật sự của người địa phương" | Facebook group "Du lịch HN tự túc" | User cần local experience kèm gợi ý ăn uống gần điểm tham quan |
| Địa điểm đóng cửa thứ 2 nhưng app không cảnh báo | Review Google Maps Văn Miếu | Failure mode nghiêm trọng; phải cross-check ngày đến vs lịch đóng cửa |
| "App du lịch hỏi bạn muốn đi đâu nhưng tôi không biết HN có gì" | Comment YouTube vlog HN | Cold-start: hỏi habit/lifestyle thay vì hỏi địa điểm cụ thể |
| Vietnam Tourism DB không có filter theo sở thích; Foody trả hàng trăm kết quả | Self-use | Data cần được cá nhân hóa bằng AI, không chỉ trả list chung |
| Khách quốc tế mất 2 tiếng lên kế hoạch 1 ngày vì blog mâu thuẫn | TripAdvisor forum | Lịch trình phải có giờ mở cửa xác nhận + sắp xếp theo khung giờ thực tế |
| Không app nào gợi ý cả tham quan + ăn uống + bar gần nhau trong cùng 1 lịch trình | Competitor analysis (Google Maps, TripAdvisor, Klook) | **USP**: kết hợp places + restaurants + bars theo quận/khu vực |

### Pain statement

```
Khách du lịch lần đầu đến Hà Nội đang gặp khó ở bước lên kế hoạch chuyến đi,
vì họ không có đủ context về thành phố để tự lọc hàng trăm gợi ý từ blog/app,
không biết địa điểm nào phù hợp với lifestyle (ăn gì, đi đâu, chơi gì buổi tối),
và phải dùng 3–4 app khác nhau (Google Maps, Foody, TripAdvisor, blog) để ghép 1 lịch trình.
Dẫn tới: mất nhiều giờ research, lịch trình generic thiếu cá nhân hóa,
hoặc đến nơi thì địa điểm đóng cửa.
```

---

## 2. Lát cắt để build (Build Slice)

Cho khách du lịch lần đầu đến Hà Nội đang lên kế hoạch chuyến đi 1–2 ngày,
prototype chatbot sẽ:

1. **Hỏi 5 câu về habit/preference:**
   - Q1: Thích ăn uống thế nào — đường phố / nhà hàng / local hidden gem
   - Q2: Muốn tham quan gì — văn hóa-lịch sử / vui chơi-mua sắm / chill cafe
   - Q3: Ưu tiên trải nghiệm local hay tiện nghi tourist
   - Q4: Ngân sách ước tính / ngày (dưới 500k / 500k–1tr / trên 1tr VNĐ)
   - Q5: Ngày và số ngày đến Hà Nội

2. **Dùng AI (Gemini API) match habit với data thực:**
   - 📍 55 địa điểm tham quan (`places`) — có giờ mở cửa, ngày đóng cửa, rating
   - 🍜 71 quán ăn/cafe (`restaurants`) — có quận, giá, món nổi bật, rating
   - 🍺 53 bar/pub (`bars`) — có vibe tags, local tips, khung giờ đêm

3. **Sắp xếp lịch trình theo khung giờ thực tế** kèm gợi ý ăn uống + nightlife:
   - 🌅 SÁNG (7:00–12:00): Địa điểm tham quan + gợi ý ăn sáng gần đó
   - 🍜 TRƯA (12:00–13:30): Quán ăn phù hợp preference + cùng quận
   - 🌤️ CHIỀU (13:30–17:00): Địa điểm tham quan + cafe nghỉ chân
   - 🍜 TỐI (18:00–20:00): Quán ăn tối theo budget + preference
   - 🍺 ĐÊM (20:00+): Bar/pub phù hợp vibe (nếu user muốn)

4. **Trả về lịch trình 1 ngày cá nhân hóa** dạng text có thể copy/share.

5. **Xử lý failure mode** "địa điểm đóng cửa đúng ngày khách đến" bằng cảnh báo ⚠️ và gợi ý 1–2 địa điểm thay thế tương đương.

### Điểm khác biệt so với app hiện có (USP)

| App hiện tại | Hạn chế | Chatbot của nhóm |
|---|---|---|
| Google Maps | Gợi ý theo vị trí, không hỏi habit, không có lịch trình | Hỏi 5 câu → tạo lịch trình cá nhân hóa |
| TripAdvisor | User tự chọn từ danh sách, không có AI matching | AI match habit → địa điểm + quán ăn + bar |
| ChatGPT/Claude | Không có data thực về giờ mở cửa, không có quán ăn cụ thể | Data thực 179 records, giờ mở cửa, giá, rating |
| Klook/GetYourGuide | Chỉ bán tour, không gợi ý ăn uống + bar | **Tham quan + ăn uống + nightlife trong 1 lịch trình** |
| Foody | Chỉ ăn uống, không có tham quan | Kết hợp cả 3 loại trải nghiệm |

---

## 3. AI Product Canvas

### Problem
- User lần đầu đến Hà Nội không có đủ context để lọc hàng trăm gợi ý (cold-start problem).
- Phải dùng nhiều app khác nhau để ghép lịch trình tham quan + ăn uống + nightlife.
- Dễ trúng lịch trình có địa điểm đóng cửa, đặc biệt thứ 2.

### Solution
- Chatbot hỏi preference/habit thay vì yêu cầu user tự biết Hà Nội.
- AI match preference với **179 records data thực** (55 places + 71 restaurants + 53 bars).
- Tạo lịch trình trọn vẹn: **đi đâu + ăn gì + chơi đêm ở đâu** — theo khung giờ thực tế, có cảnh báo đóng cửa.

### Data Assets

| Dataset | Records | Fields chính | Nguồn |
|---|---|---|---|
| `places` | 55 | name, category, district, area, open/close time, closed_on, price_min/max, rating, best_for, highlights | Vietnam Tourism DB + Google Maps + nhập tay |
| `restaurants` | 71 | name, address, district, area, category, rating, price_min/max, popular_dish | Foody + nhập tay + LLM augment |
| `bars` | 53 | name, category, district, area, price_min/max, open/close time, vibe_tags, local_tip | Foody Bar + nhập tay |

### Value
- **Giảm thời gian** lên kế hoạch từ 2+ tiếng xuống 3–5 phút.
- **Tăng tính cá nhân hóa** — lịch trình match đúng lifestyle của user.
- **Tránh failure mode** — cảnh báo địa điểm đóng cửa.
- **Trải nghiệm trọn vẹn** — tham quan + ăn uống + nightlife trong 1 output duy nhất.

### Key Win
- Lịch trình 1 ngày với đủ sáng/trưa/chiều/tối/đêm — AI chịu trách nhiệm draft, user quyết cuối.
- Gợi ý quán ăn **gần vị trí tham quan** (cùng quận) — không cần user tự tìm thêm.
- Bar/pub phù hợp vibe user (jazz, rooftop, craft beer...) — không app du lịch nào làm được.

---

## 4. Tăng năng lực hay tự động hóa

### Mức độ AI
- **Conditional automation**: AI tự tạo lịch trình khi preference rõ ràng và địa điểm mở cửa.
- **Augmentation**: Khi input mơ hồ hoặc có rủi ro → AI hỏi lại, đưa disclaimer, hoặc đề xuất "balanced".

### Vai trò human
- User là **reviewer**: duyệt lịch trình, yêu cầu chỉnh sửa (thêm/bớt/đổi).
- Prototype hiển thị output rõ ràng và cho user quyền correction.

### AI Decision Flow

```
User input 5 preferences
       │
       ▼
  ┌─ Preference rõ ràng? ─┐
  │ YES                    │ NO
  ▼                        ▼
AI tự tạo              AI hỏi thêm 1 câu
lịch trình             hoặc tạo lịch trình
đầy đủ                 "balanced" + disclaimer
  │                        │
  ▼                        ▼
Check ngày đến ──► Có địa điểm đóng cửa?
                   │ YES           │ NO
                   ▼               ▼
              ⚠️ Cảnh báo     ✅ Output
              + Thay thế      lịch trình
```

---

## 5. Bốn đường đi của trải nghiệm

| Path | Prototype phải thể hiện |
|---|---|
| **Happy Path** | User trả lời 5 câu rõ ràng → AI trả lịch trình 1 ngày đầy đủ: 5–7 địa điểm tham quan + 2–3 quán ăn gần đó + 1 bar/pub buổi tối, có khung giờ, giá, rating → User hài lòng, copy lịch trình |
| **AI Uncertain** | User trả lời mơ hồ ("tôi ăn được hết", "cái gì cũng thích") → AI hỏi thêm 1 câu cụ thể ("Nếu chỉ có 3 tiếng buổi sáng, bạn chọn đi chùa hay ngồi cafe?") hoặc trả lịch trình balanced với disclaimer " Dựa trên sở thích phổ biến nhất" |
| **AI Wrong** | User nhập ngày thứ 2 → AI detect Văn Miếu, Bảo tàng Lịch sử, Hoàng Thành... đóng cửa → cảnh báo " Văn Miếu đóng cửa thứ 2 — đề xuất thay thế: Nhà tù Hỏa Lò (cùng quận, mở thứ 2)" + tự động điều chỉnh lịch trình |
| **User Correction** | User muốn chỉnh: "thêm quán cafe buổi chiều", "bỏ bar", "đổi sang khu Tây Hồ" → AI update lịch trình theo yêu cầu mà KHÔNG hỏi lại 5 câu từ đầu, giữ nguyên context |

---

## 6. Những kiểu lỗi đáng lo nhất

### 1. Không kiểm tra giờ mở cửa / ngày đóng cửa
- **Ví dụ:** Văn Miếu, Bảo tàng Dân tộc học, Hoàng Thành, Bảo tàng Lịch sử, Nhà tù Hỏa Lò đều đóng thứ 2; Bảo tàng Quân sự đóng cả thứ 2 và thứ 3.
- **Hậu quả:** User đến nơi không vào được → mất thời gian, tiền xe, và niềm tin.
- **Xử lý:** Cross-check ngày đến (từ Q5) với field `closed_on` trong data → cảnh báo + gợi ý thay thế cùng category và quận.

### 2. Gợi ý quán ăn/bar không match quận với địa điểm tham quan
- **Ví dụ:** Buổi sáng tham quan ở Hoàn Kiếm nhưng gợi ý ăn trưa ở Cầu Giấy → user phải đi xa 7km.
- **Xử lý:** Match `district` / `area` giữa places và restaurants/bars khi xây dựng lịch trình.

### 3. Trả lịch trình generic, không cá nhân hóa
- **Ví dụ:** User thích street food nhưng AI gợi ý nhà hàng Wagyu 800k.
- **Xử lý:** Match `food_style` preference với `category` + `price_min`/`price_max` của restaurants.

### 4. Xử lý mơ hồ không đủ rõ
- **Ví dụ:** AI tự tin trả lịch trình khi user chưa nói rõ preference.
- **Xử lý:** Detect ≥2 câu trả lời generic → hỏi thêm hoặc gắn disclaimer.

### 5. Gợi ý bar/pub khi user không muốn
- **Ví dụ:** User đi cùng gia đình nhỏ, không cần nightlife.
- **Xử lý:** Chỉ gợi ý bar nếu user có tín hiệu muốn (preference hoặc hỏi thêm). Mặc định không gợi ý bar cho user có trẻ em.

---

## 7. Stack kỹ thuật

| Component | Lựa chọn | Lý do |
|---|---|---|
| **LLM** | Google Gemini 2.0 Flash (free tier) | Miễn phí 1500 req/ngày, context 1M tokens, hỗ trợ tiếng Việt tốt |
| **Data store** | `hanoi_places.json` (179 records) | 55 places + 71 restaurants + 53 bars — inject thẳng vào prompt (~16k tokens, chỉ 1.6% context) |
| **UI** | Streamlit | Nhanh nhất cho prototype chat UI, có `st.chat_message`, deploy local |
| **Failure detection** | Python logic | Check ngày trong tuần vs `closed_on` — đơn giản, reliable |
| **Chi phí** | **$0** | Gemini free tier hoàn toàn đủ cho prototype + demo |

---

## 8. Kế hoạch kiểm thử và bằng chứng demo

### Kế hoạch kiểm thử

| Test case | Input | Expected output |
|---|---|---|
| **Happy path** | Preference rõ: street food + văn hóa + local + 500k + Thứ 4 | Lịch trình 1 ngày: 5–7 places + 2–3 quán ăn + 1 bar, tất cả mở cửa thứ 4 |
| **Low-confidence** | "Tôi ăn được hết", "cái gì cũng thích" | AI hỏi thêm 1 câu hoặc trả balanced + disclaimer |
| **Failure path** | Ngày đến = Thứ 2 | ⚠️ Cảnh báo Văn Miếu/Bảo tàng đóng cửa + gợi ý thay thế |
| **Correction** | "Thêm quán cafe buổi chiều" | Lịch trình updated, không hỏi lại từ đầu |
| **Budget match** | Budget dưới 500k | Chỉ gợi ý places miễn phí/rẻ + quán ăn dưới 100k |
| **District match** | Tham quan Hoàn Kiếm buổi sáng | Quán ăn trưa cũng ở Hoàn Kiếm (33 quán) |

### Bằng chứng demo (3–5 phút)

1. **Mở đầu (30s):** Show Pain Statement + USP "tham quan + ăn uống + nightlife".
2. **Demo Happy Path (2 phút):** Trả lời 5 câu → nhận lịch trình đầy đủ sáng/trưa/chiều/tối/đêm.
3. **Demo Failure Path (1 phút):** Nhập thứ 2 → AI cảnh báo + thay thế.
4. **Demo Correction (30s):** Yêu cầu chỉnh → AI update ngay.
5. **Kết (30s):** So sánh với competitor + hướng phát triển.

---

## 9. Phân công

| Thành viên | Vai trò | Việc phụ trách | Bằng chứng cần có |
|---|---|---|---|
| Nguyễn Hải An | Data + Frontend | Chuẩn bị/kiểm tra dataset, hỗ trợ mapping dữ liệu và build giao diện Next.js kết nối FastAPI | `codebase/data/hanoi_places.json`, `codebase/frontend/src/app/page.tsx`, `codebase/frontend/src/app/globals.css` |
| Lương Đình Bút | SPEC + Prompt + MVP | Cải thiện system prompt, chuẩn bị data và hoàn thành MVP có AI call thật với Fireworks/DeepSeek | `spec.md`, `codebase/src/services/prompt_builder.py`, `codebase/data/hanoi_places.json` |
| Đoàn Thị Thu Linh | Prompt + Prototype UX | Thiết kế system prompt ban đầu và prototype UX theo hướng chat-driven để dẫn user qua 5 câu hỏi | `codebase/src/app.py`, `codebase/src/services/onboarding.py`, `codebase/src/services/prompt_builder.py`, `codebase/src/core/llm.py` |
| Nguyễn Duy Đức | Prototype + AI Safety + Docs | Dựng mockup prototype ban đầu, thêm LLM provider switcher, fallback itinerary, validator, slide/demo material và README | `codebase/src/core/llm.py`, `codebase/src/agent/itinerary_agent.py`, `codebase/src/services/fallback_builder.py`, `codebase/src/services/itinerary_validator.py`, `README.md` |
| Lê Văn Quang | Test + Failure | Viết test cases, code failure detection logic (check thứ + closed_on), kiểm thử 4 paths | `codebase/tests/test_cases.md` — ít nhất 6 test cases |

---

## 10. Output mẫu kỳ vọng

```
📍 LỊCH TRÌNH HÀ NỘI — THỨ 4, 11/06/2026
   Phong cách: Street food · Văn hóa-lịch sử · Local · Budget 500k

🌅 SÁNG (8:00–11:30)
   📍 Văn Miếu - Quốc Tử Giám (8:00–9:00)
      Đống Đa · ⭐4.6 · 30.000đ/vé · Di tích lịch sử quốc gia
   📍 Hồ Hoàn Kiếm & Đền Ngọc Sơn (9:30–11:00)
      Hoàn Kiếm · ⭐4.7 · 30.000đ/vé đền · Biểu tượng Hà Nội
   ☕ Cà Phê Phố Cổ Legend (11:00–11:30)
      Hoàn Kiếm · ⭐8.0 · 20k–60k · Cà phê đen đá 25k

🍜 TRƯA (11:30–13:00)
   🥢 Bún Chả Đắc Kim
      1 Hàng Mành, Hoàn Kiếm · ⭐8.8 · 50k–80k
      🔥 Món nổi bật: Bún chả với nem — 65.000đ

🌤️ CHIỀU (13:30–17:00)
   📍 Nhà tù Hỏa Lò (13:30–14:30)
      Hoàn Kiếm · ⭐4.5 · 30.000đ · Lịch sử chiến tranh
   📍 Nhà thờ Lớn Hà Nội (15:00–15:30)
      Hoàn Kiếm · ⭐4.6 · Miễn phí · Kiến trúc Gothic
   📍 Phố Cổ Hà Nội (15:30–17:00)
      Hoàn Kiếm · ⭐4.5 · Miễn phí · 36 phố phường nghìn năm

🍜 TỐI (18:00–20:00)
   🥢 Phở Sướng
      24B Trung Yên, Hoàn Kiếm · ⭐8.6 · 40k–70k
      🔥 Món nổi bật: Phở bò tái — 55.000đ

🍺 ĐÊM (20:30–23:00)
   🍸 Polite & Co
      Hoàn Kiếm · 80k–300k · 17:00–02:00
      🏷️ Jazz, Cocktail, Nhạc sống, Hẹn hò
      💡 Tip: Nhạc Jazz nhẹ nhàng buổi tối

💰 Tổng chi phí ước tính: ~350.000–450.000 VNĐ
```
