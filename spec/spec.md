# SPEC Day 06

> Nhóm: 4
> Thành viên: Nguyễn Hải An · Lương Đình Bút · Đoàn Thị Thu Linh · Nguyễn Duy Đức · Lê Văn Quang
> Ngày: Day 06

---

## 1. Bằng chứng

### Track, product và user
- Track: Travel / Du lịch
- Product/app thật: Chatbot gợi ý lịch trình tham quan Hà Nội
- User cụ thể: Khách du lịch lần đầu đến Hà Nội, lên kế hoạch chuyến đi 1–2 ngày
- Nguồn bằng chứng: quan sát thực tế nhóm, review Google Maps Văn Miếu, comment YouTube, group Facebook du lịch HN, forum TripAdvisor

### Tóm tắt bằng chứng chính

| Evidence | Nguồn | Ý nghĩa cho SPEC |
|---|---|---|
| “Không biết chỗ ăn ngon thật sự của người địa phương” | Facebook group “Du lịch HN tự túc” | User cần local experience và insider lens, không chỉ loại địa điểm |
| Địa điểm đóng cửa thứ 2 nhưng app không cảnh báo | Review Google Maps Văn Miếu | Failure mode nghiêm trọng; phải kiểm tra giờ mở cửa và cảnh báo |
| “App du lịch hỏi bạn muốn đi đâu nhưng tôi không biết HN có gì” | Comment YouTube vlog HN | Cold-start: không nên hỏi địa điểm cụ thể, phải hỏi preference/habit |
| Vietnam Tourism DB không có filter theo sở thích; Foody trả hàng trăm kết quả | Self-use | Data cần được cá nhân hóa bằng AI, không chỉ trả list chung |
| Khách quốc tế mất 2 tiếng lên kế hoạch 1 ngày vì blog mâu thuẫn | TripAdvisor forum | Cần lịch trình có giờ mở cửa xác nhận và sắp xếp theo khung giờ thực tế |

### Pain statement

```
Khách du lịch lần đầu đến Hà Nội đang gặp khó ở bước lên kế hoạch chuyến đi,
vì họ không có đủ context về thành phố để tự lọc hàng trăm gợi ý từ blog/app,
và không biết địa điểm nào phù hợp với lifestyle của họ (ăn gì, ở đâu, trải nghiệm gì).
Dẫn tới: mất nhiều giờ research, lịch trình generic không phù hợp, hoặc đến nơi thì địa điểm đóng cửa.
```

---

## 2. Lát cắt để build

Cho khách du lịch lần đầu đến Hà Nội đang lên kế hoạch chuyến đi 1–2 ngày,
prototype chatbot sẽ:

1. Hỏi 5 câu về habit/preference:
   - Thích ăn uống thế nào — đường phố / nhà hàng / local
   - Muốn tham quan văn hóa-lịch sử hay khu vui chơi-mua sắm
   - Ưu tiên trải nghiệm local hay tiện nghi tourist
   - Ngân sách/ngày ước tính
   - Ngày và số ngày đến Hà Nội

2. Dùng AI để match habit với địa điểm từ Vietnam Tourism DB + Foody.
3. Sắp xếp lịch trình theo khung giờ thực tế (sáng / trưa / chiều / tối) kèm ảnh minh họa.
4. Trả về lịch trình 1 ngày cá nhân hóa dạng text + ảnh có thể copy/share.
5. Xử lý failure mode “địa điểm đóng cửa đúng ngày khách đến” bằng cảnh báo rõ ràng và gợi ý 1–2 địa điểm thay thế tương đương.

---

## 3. AI Product Canvas

### Problem
- User lần đầu đến Hà Nội không có đủ context để lọc hàng trăm gợi ý.
- User không biết local spots, không biết điểm nào phù hợp với sở thích.
- User dễ trúng lịch trình chứa địa điểm đóng cửa.

### Solution
- Chatbot hỏi preference/habit thay vì yêu cầu user chọn địa điểm.
- AI match preference với địa điểm thực tế từ Vietnam Tourism DB + Foody.
- Tạo lịch trình theo thời điểm trong ngày với cảnh báo giờ mở cửa.

### Value
- Giảm thời gian research cho user.
- Tăng tính cá nhân hóa cho lịch trình.
- Tránh đưa user đến địa điểm đóng cửa.

### Key win
- Lịch trình 1 ngày phù hợp hơn với user first-time, có thời gian và ảnh minh họa.
- AI chịu trách nhiệm draft, user vẫn quyết định và điều chỉnh.

---

## 4. Tăng năng lực hay tự động hóa

### Mức độ AI
- **Conditional automation**: AI tự tạo lịch trình trong case rõ preference và địa điểm mở cửa.
- **Augmentation**: AI gợi ý/draft/phân loại, user quyết cuối cùng.
- Nếu input mơ hồ hoặc có rủi ro (địa điểm đóng cửa, ngày lễ, preference không rõ) thì hỏi lại hoặc đưa disclaimer.

### Vai trò human
- User là reviewer: duyệt lịch trình, điều chỉnh yêu cầu thêm/bớt, hoặc đổi khu vực.
- Prototype cần hiển thị output AI rõ ràng và cho user quyền chỉnh sửa.

---

## 5. Bốn đường đi của trải nghiệm

| Path | Prototype phải thể hiện |
|---|---|
| **Happy Path** | User trả lời 5 câu rõ ràng → AI trả lịch trình 1 ngày đầy đủ (5–7 địa điểm), có khung giờ, ảnh, địa điểm mở cửa đúng ngày → User hài lòng, copy lịch trình |
| **AI Uncertain** | User trả lời mơ hồ (ví dụ: “tôi ăn được hết” hoặc không có preference rõ) → AI hỏi thêm 1 câu làm rõ hoặc trả lịch trình balanced với disclaimer “dựa trên sở thích phổ biến nhất” |
| **AI Wrong** | User nhập ngày thứ 2 → AI detect các địa điểm như Văn Miếu/Bảo tàng đóng cửa → cảnh báo rõ “⚠️ [Tên địa điểm] đóng cửa vào thứ 2 — đề xuất thay thế: [...]” |
| **User Correction** | User muốn điều chỉnh (“thêm quán ăn buổi tối”, “đổi khu vực từ Hoàn Kiếm sang Tây Hồ”) → AI update lịch trình theo yêu cầu mà không hỏi lại từ đầu |

---

## 6. Những kiểu lỗi đáng lo nhất

1. **Không kiểm tra giờ mở cửa / ngày đóng cửa**
   - Ví dụ: Văn Miếu, Bảo tàng, bảo tàng nhà nước đóng thứ 2.
   - Hậu quả: user đến nơi không vào được, mất thời gian và niềm tin.
   - Prototype yêu cầu cross-check ngày đến với lịch đóng cửa và hiện cảnh báo rõ.

2. **Trả lịch trình generic, không cá nhân hóa**
   - Nếu AI chỉ list địa điểm chung mà không match habit, user vẫn mất thời gian chọn lựa.
   - Phải dùng 5 câu preference để tạo lịch trình đúng nhu cầu.

3. **Xử lý mơ hồ không đủ rõ**
   - Khi user trả lời chưa rõ, prototype phải hỏi thêm hoặc gắn disclaimer.
   - Tránh trả output quá tự tin khi data không đủ.

---

## 7. Kế hoạch kiểm thử và bằng chứng demo

### Kế hoạch kiểm thử
- Test happy path: user trả lời rõ preference, nhận lịch trình 1 ngày hợp lý.
- Test low-confidence path: user trả lời mơ hồ, AI hỏi thêm hoặc hiển thị disclaimer.
- Test failure path: user nhập ngày thứ 2, hệ thống cảnh báo địa điểm đóng cửa và đề xuất thay thế.
- Test correction path: user yêu cầu điều chỉnh lịch trình sau khi xem output.

### Bằng chứng demo
- Show Product Canvas và nỗi đau user.
- Demo full luồng end-to-end với ít nhất một flow AI chạy thật.
- Show cả happy path và error path đang xử lý giờ mở cửa.
- Chứng minh prototype trả lịch trình có khung giờ, ảnh minh họa, và cảnh báo đóng cửa khi cần.

---

## 8. Phân công

| Thành viên | Vai trò | Việc phụ trách | Bằng chứng cần có |
|---|---|---|---|
| Thành viên 1 | Research lead | Scrape/chuẩn bị seed data từ Vietnam Tourism DB + Foody (10–15 địa điểm HN có giờ mở cửa, loại, ảnh) | `/data/hanoi_places.json` với ít nhất 15 địa điểm đầy đủ field |
| Thành viên 2 | SPEC + Prompt | Viết system prompt cho LLM, thiết kế 5 câu hỏi chatbot, viết final SPEC Day 06 | `/prompts/system_prompt.md`, `spec/spec.md` |
| Thành viên 3 | Prototype dev | Build chatbot flow, tích hợp LLM API, kết nối data JSON | `/codebase/` — demo chạy được locally |
| Thành viên 4 | Test + Failure path | Viết test cases, kiểm thử path thứ 2 đóng cửa, path preference mơ hồ, path correction | `/tests/test_cases.md` hoặc tương đương |
| Thành viên 5 | Demo + Repo | Viết demo script 3–5 phút, chuẩn bị repo nộp bài đúng cấu trúc, README hướng dẫn chạy | `README.md`, demo script |
