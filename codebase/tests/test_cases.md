# Test Cases - Chatbot gợi ý lịch trình Hà Nội

> kiểm thử happy path, failure path "thứ 2 đóng cửa", preference mơ hồ và user correction. Các test case này dùng dataset `codebase/data/hanoi_places.json` làm nguồn kiểm chứng.

## Tổng quan kiểm thử

| ID | Path | Mục tiêu | Kết quả pass |
|---|---|---|---|
| TC-01 | Happy Path | User trả lời rõ 5 câu preference | Chatbot trả lịch trình 1 ngày 5-7 điểm, có khung giờ, mô tả, không chứa điểm đóng cửa vào ngày đi |
| TC-02 | AI Wrong / Failure Path | User đi vào thứ 2, nhiều điểm văn hóa-lịch sử đóng cửa | Chatbot cảnh báo rõ các điểm `closed_on: ["Monday"]` và đề xuất thay thế đang mở |
| TC-03 | AI Uncertain | Preference mơ hồ, không đủ tín hiệu cá nhân hóa | Chatbot hỏi thêm 1 câu làm rõ hoặc tạo lịch trình balanced kèm disclaimer |
| TC-04 | User Correction | User muốn sửa lịch trình sau khi nhận kết quả | Chatbot cập nhật lịch trình theo yêu cầu, giữ thông tin cũ còn phù hợp, không bắt đầu lại từ đầu |

---

## TC-01 - Happy path: lịch trình rõ preference

**Mục tiêu**

Kiểm tra chatbot có thể nhận đủ 5 câu trả lời rõ ràng, match với dataset và tạo lịch trình cá nhân hóa theo khung giờ thực tế.

**Input mẫu**

```text
Tôi lần đầu đến Hà Nội, đi 1 ngày vào thứ 7 ngày 2026-06-06.
Tôi thích ăn local/đường phố, muốn tham quan văn hóa-lịch sử,
ưu tiên trải nghiệm local hơn tourist, ngân sách khoảng 700.000 VNĐ/ngày.
Tôi muốn lịch trình quanh khu trung tâm để dễ đi bộ.
```

**Bước kiểm thử**

1. Nhập input trên vào chatbot.
2. Kiểm tra chatbot có dùng đủ preference: ăn local, văn hóa-lịch sử, local experience, ngân sách, ngày đi.
3. Kiểm tra lịch trình có 5-7 điểm hoặc hoạt động trong 1 ngày.
4. Kiểm tra mỗi điểm có khung giờ hoặc thứ tự sáng/trưa/chiều/tối.
5. Đối chiếu dataset để đảm bảo các điểm được chọn không đóng cửa vào thứ 7.

**Expected result**

- Có lịch trình 1 ngày rõ ràng, ví dụ gồm Hồ Hoàn Kiếm, Phố Cổ, điểm văn hóa-lịch sử, quán ăn/cafe phù hợp ngân sách.
- Có mô tả ngắn cho từng điểm và lý do phù hợp với preference.
- Không có cảnh báo đóng cửa không cần thiết.
- Không chọn các địa điểm ngoài dataset nếu prototype được yêu cầu chỉ dùng `hanoi_places.json`.

**Pass/Fail**

- Pass nếu lịch trình cá nhân hóa, có thời gian, có mô tả, và không vi phạm ngày đóng cửa.
- Fail nếu chỉ trả list generic, thiếu thời gian, hoặc chọn điểm đóng cửa vào ngày user đi.

---

## TC-02 - Failure path: thứ 2 có địa điểm đóng cửa

**Mục tiêu**

Kiểm tra chatbot phát hiện ngày thứ 2 và không âm thầm đưa user đến địa điểm có `closed_on` chứa `Monday`.

**Input mẫu**

```text
Tôi đi Hà Nội 1 ngày vào thứ 2 ngày 2026-06-08.
Tôi thích văn hóa-lịch sử, muốn đi Văn Miếu, Nhà tù Hỏa Lò và bảo tàng.
Ngân sách 500.000 VNĐ/ngày, ưu tiên khu trung tâm.
```

**Dữ liệu cần kiểm chứng**

Các địa điểm trong dataset đóng cửa thứ 2 gồm:

- `Văn Miếu - Quốc Tử Giám` - `closed_on: ["Monday"]`
- `Nhà tù Hỏa Lò` - `closed_on: ["Monday"]`
- `Bảo tàng Dân tộc học Việt Nam` - `closed_on: ["Monday"]`
- `Bảo tàng Lịch sử Quốc gia` - `closed_on: ["Monday"]`
- `Hoàng thành Thăng Long` - `closed_on: ["Monday"]`
- `Bảo tàng Phụ nữ Việt Nam` - `closed_on: ["Monday"]`
- `Bảo tàng Mỹ thuật Việt Nam` - `closed_on: ["Monday"]`

**Bước kiểm thử**

1. Nhập input trên vào chatbot.
2. Kiểm tra chatbot xác định `2026-06-08` là thứ 2.
3. Kiểm tra chatbot cảnh báo rõ địa điểm user yêu cầu nhưng đóng cửa.
4. Kiểm tra chatbot không đưa các điểm đóng thứ 2 vào lịch trình chính.
5. Kiểm tra chatbot đề xuất 1-2 thay thế tương đương đang mở, ví dụ Hồ Hoàn Kiếm, Phố Cổ, Chùa Một Cột, Chùa Trấn Quốc, Cầu Long Biên hoặc Hồ Tây tùy preference.

**Expected result**

Chatbot cần có thông điệp tương đương:

```text
Cảnh báo: Văn Miếu - Quốc Tử Giám và Nhà tù Hỏa Lò đóng cửa vào thứ 2.
Mình sẽ thay bằng các điểm đang mở và vẫn phù hợp văn hóa-lịch sử như Chùa Một Cột / Chùa Trấn Quốc / Hồ Hoàn Kiếm.
```

**Pass/Fail**

- Pass nếu chatbot nêu cảnh báo rõ, loại điểm đóng cửa khỏi lịch trình chính, và đưa thay thế hợp lý.
- Fail nếu chatbot vẫn xếp Văn Miếu, Hỏa Lò hoặc bảo tàng đóng thứ 2 vào lịch trình mà không cảnh báo.

---

## TC-03 - AI uncertain: preference mơ hồ

**Mục tiêu**

Kiểm tra chatbot không quá tự tin khi user trả lời mơ hồ và thiếu tín hiệu cá nhân hóa.

**Input mẫu**

```text
Tôi đi Hà Nội 1 ngày, ăn gì cũng được, đi đâu cũng được.
Tôi không biết thích văn hóa hay thiên nhiên, ngân sách sao cũng được.
Bạn tự chọn giúp tôi.
```

**Bước kiểm thử**

1. Nhập input trên vào chatbot.
2. Kiểm tra chatbot nhận ra preference chưa đủ rõ.
3. Kiểm tra chatbot hỏi thêm 1 câu làm rõ hoặc đưa lịch trình balanced với disclaimer.
4. Nếu chatbot chọn trả lịch trình balanced, kiểm tra lịch trình có đủ nhóm trải nghiệm: biểu tượng lần đầu đến HN, local food, văn hóa nhẹ, chiều/tối dễ đi.

**Expected result**

Một trong hai hướng đều được tính là đúng:

- Hỏi thêm 1 câu làm rõ, ví dụ: "Bạn muốn ngày này nghiêng về văn hóa-lịch sử, ăn uống local, hay thư giãn chụp ảnh?"
- Hoặc trả lịch trình balanced kèm disclaimer: "Vì preference còn mơ hồ, mình chọn lịch trình phổ biến cho người lần đầu đến Hà Nội."

**Pass/Fail**

- Pass nếu chatbot thể hiện độ không chắc bằng câu hỏi làm rõ hoặc disclaimer.
- Fail nếu chatbot trả kết quả rất tự tin nhưng không giải thích giả định, hoặc lịch trình không dựa vào preference nào.

---

## TC-04 - User correction: đổi khu vực và thêm ăn tối

**Mục tiêu**

Kiểm tra chatbot cập nhật lịch trình sau phản hồi của user mà không bắt user nhập lại toàn bộ 5 câu hỏi.

**Tiền điều kiện**

Đã chạy TC-01 hoặc đã có một lịch trình 1 ngày quanh khu trung tâm.

**Input correction mẫu**

```text
Tôi muốn đổi buổi chiều sang khu Tây Hồ và thêm một quán ăn/cafe buổi tối.
Giữ ngân sách khoảng 700.000 VNĐ/ngày.
```

**Bước kiểm thử**

1. Sau khi chatbot trả lịch trình ban đầu, nhập correction trên.
2. Kiểm tra chatbot giữ các thông tin cũ còn hợp lệ: đi 1 ngày, ngân sách, thích local, ngày đi.
3. Kiểm tra chatbot cập nhật buổi chiều sang khu Tây Hồ.
4. Kiểm tra chatbot thêm hoạt động/quán ăn/cafe buổi tối phù hợp giờ mở cửa.
5. Kiểm tra chatbot không hỏi lại toàn bộ onboarding 5 câu.

**Expected result**

- Lịch trình mới có phần chiều/tối ở Tây Hồ, ví dụ Hồ Tây, Chùa Trấn Quốc, cafe view hồ hoặc quán ăn phù hợp dataset.
- Các điểm còn lại nếu không mâu thuẫn vẫn được giữ hoặc sắp xếp lại hợp lý.
- Có thông báo ngắn về phần đã thay đổi.

**Pass/Fail**

- Pass nếu chatbot cập nhật đúng yêu cầu, giữ context cũ và không restart flow.
- Fail nếu chatbot bỏ qua correction, hỏi lại từ đầu, hoặc tạo lịch trình mới trái với ngân sách/ngày đi ban đầu.

---

