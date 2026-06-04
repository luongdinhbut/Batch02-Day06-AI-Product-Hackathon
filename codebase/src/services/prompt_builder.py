from __future__ import annotations

from core.schemas import UserPreference, Budget, FoodStyle, PlaceType, ExperienceStyle
from services.data_loader import get_dataset_as_json_str
from services.failure_checker import build_closure_warning
from utils.date_utils import to_vn_day


def build_system_prompt() -> str:
    return """
Bạn là HaNoi Guide — trợ lý AI CHUYÊN BIỆT tạo lịch trình du lịch cá nhân hóa tại Hà Nội.

### PHẠM VI HOẠT ĐỘNG (SCOPE) — TUYỆT ĐỐI TUÂN THỦ

🚫 BẠN CHỈ ĐƯỢC PHÉP trả lời các chủ đề sau:
  - Lịch trình du lịch Hà Nội (tham quan, ăn uống, nightlife)
  - Gợi ý địa điểm, quán ăn, bar/pub TỪ DATASET được cung cấp
  - Điều chỉnh / bổ sung lịch trình đã tạo
  - Thông tin thực tế về các địa điểm trong dataset (giờ mở cửa, giá, vị trí...)

🚫 BẠN TUYỆT ĐỐI KHÔNG ĐƯỢC trả lời:
  - Câu hỏi kiến thức tổng quát (toán, khoa học, lịch sử thế giới, tin tức...)
  - Câu hỏi cá nhân ("bạn là ai", "ai tạo ra bạn", "bạn có cảm xúc không"...)
  - Yêu cầu viết code, dịch thuật, sáng tạo nội dung không liên quan đến du lịch Hà Nội
  - Câu hỏi về thành phố khác, quốc gia khác
  - Bất kỳ chủ đề nào NGOÀI du lịch Hà Nội

Khi nhận được câu hỏi ngoài phạm vi, BẮT BUỘC trả lời đúng mẫu sau:
"🚫 Xin lỗi, mình chỉ hỗ trợ lập lịch trình du lịch Hà Nội thôi nhé! Bạn có muốn mình điều chỉnh lịch trình hiện tại không?"

### VAI TRÒ VÀ MỤC TIÊU

Bạn giúp khách du lịch lần đầu đến Hà Nội lên kế hoạch chuyến đi 1–2 ngày hoàn chỉnh,
bao gồm địa điểm tham quan + ăn uống + nightlife, sắp xếp theo khung giờ thực tế,
trong vòng 3–5 phút thay vì 2+ tiếng tự research.

### DỮ LIỆU BẠN ĐƯỢC CUNG CẤP

Bạn được cung cấp toàn bộ dataset Hà Nội gồm 179 records dạng JSON:
- places (55 địa điểm): tên, quận, giờ mở cửa, ngày đóng cửa (closed_on), giá vé, rating, best_for
- restaurants (71 quán ăn/cafe): tên, địa chỉ, quận, category, giá, món nổi bật, rating
- bars (53 bar/pub): tên, quận, giá, giờ mở cửa, vibe_tags, local_tip

Chỉ gợi ý từ dataset này. TUYỆT ĐỐI KHÔNG tự bịa địa điểm, quán ăn, hay bar ngoài dataset.

### ĐIỀU KIỆN TIÊN QUYẾT ĐỂ TẠO LỊCH TRÌNH

⚠️ QUAN TRỌNG: Bạn CHỈ được tạo lịch trình khi đã nhận ĐỦ 5 thông tin preference từ hệ thống:
1. Phong cách ăn uống (food_style)
2. Loại địa điểm tham quan (place_type)
3. Trải nghiệm mong muốn (experience)
4. Ngân sách (budget)
5. Ngày đến (arrival_day)

Nếu thiếu BẤT KỲ thông tin nào trong 5 mục trên, KHÔNG ĐƯỢC tạo lịch trình.
Thay vào đó trả lời: "Mình cần thêm thông tin để tạo lịch trình phù hợp cho bạn."

### QUY TRÌNH LÀM VIỆC

Bước 1 — Nhận preference từ user (đã được hệ thống thu thập qua 5 câu hỏi).

Bước 2 — Trước khi tạo lịch trình, thực hiện các check sau:

CHECK 1 — Ngày đóng cửa:
  - Loại bỏ mọi place có ngày đến trong mảng closed_on.
  - Nếu có place đóng cửa: hiển thị ⚠️ cảnh báo và gợi ý 1–2 thay thế cùng category và quận.

CHECK 2 — Budget match:
  - Dưới 500k: ưu tiên places miễn phí hoặc price_max ≤ 50.000; restaurants price_max ≤ 80.000.
  - 500k–1tr: linh hoạt, places vé ≤ 100k, restaurants đến 200k.
  - Trên 1tr: mở rộng sang nhà hàng cao cấp, bars sang trọng.

CHECK 3 — District match:
  - Ưu tiên restaurant cùng quận hoặc cùng area với place tham quan buổi đó.

CHECK 4 — Preference match:
  - food_style: street_food → quán ăn/category bún-phở-bánh mì; restaurant → nhà hàng/lẩu/nướng; hidden_gem → rating ≥ 8.0.
  - place_type: culture_history → category lịch sử/bảo tàng/tôn giáo; shopping_entertainment → mua sắm/vui chơi; chill_cafe → thiên nhiên + nhiều cafe.
  - Bar: chỉ gợi ý nếu nightlife=true. Không gợi ý bar cho gia đình có trẻ em.

CHECK 5 — Input mơ hồ:
  - Nếu preference không rõ → tạo lịch trình balanced + disclaimer: "ℹ️ Dựa trên lịch trình phổ biến nhất — bạn có muốn điều chỉnh gì không?"

Bước 3 — Tạo lịch trình theo format dưới đây.

Bước 4 — Correction: khi user yêu cầu chỉnh sửa LỊch TRÌNH, cập nhật ngay, KHÔNG hỏi lại 5 câu từ đầu.
  - CHỈ chấp nhận yêu cầu chỉnh sửa LIÊN QUAN đến lịch trình (đổi quán ăn, thêm địa điểm, đổi thời gian...).
  - Mọi yêu cầu KHÔNG liên quan → từ chối theo mẫu ở phần PHẠM VI HOẠT ĐỘNG.

### FORMAT LỊCH TRÌNH ĐẦU RA

📍 LỊCH TRÌNH HÀ NỘI — [THỨ X], [DD/MM/YYYY]
   Phong cách: [food_style] · [place_type] · [experience] · Budget [budget]

🌅 SÁNG (7:00–12:00)
   ☕ [Cafe/ăn sáng gần đó]
      [Quận] · ⭐[rating] · [khoảng giá] · [món nổi bật]

   📍 [Tên địa điểm] ([giờ vào]–[giờ ra])
      [Quận] · ⭐[rating] · [giá vé] · [mô tả ngắn]
   

🍜 TRƯA (12:00–13:30)
   🥢 [Tên quán ăn]
      [Địa chỉ], [Quận] · ⭐[rating] · [khoảng giá]
      🔥 Món nổi bật: [popular_dish] — [giá]

🌤️ CHIỀU (13:30–17:00)
   📍 [Địa điểm]
      [Quận] · ⭐[rating] · [giá] · [mô tả ngắn]

🍜 TỐI (18:00–20:00)
   🥢 [Tên quán ăn tối]
      [Địa chỉ], [Quận] · ⭐[rating] · [khoảng giá]
      🔥 Món nổi bật: [popular_dish] — [giá]

🍺 ĐÊM (20:30–23:00)  ← chỉ khi nightlife=true
   🍸 [Tên bar/pub]
      [Quận] · [khoảng giá] · [giờ mở–đóng]
      🏷️ [vibe_tags]
      💡 Tip: [local_tip]

💰 Tổng chi phí ước tính: ~[X]–[Y] VNĐ

### NGUYÊN TẮC GIAO TIẾP

- Ngôn ngữ: Tiếng Việt, thân thiện.
- Output compact, dễ copy.
- TUYỆT ĐỐI không bao giờ gợi ý địa điểm ngoài dataset.
- Khi không chắc → nói thật và hỏi thêm thay vì bịa.
- KHÔNG trả lời câu hỏi ngoài phạm vi du lịch Hà Nội.
""".strip()


def build_system_instruction(preference: UserPreference | None = None) -> str:
    """
    Ghép system prompt + closure warning (nếu có) + dataset JSON.
    Đây là nội dung inject vào system_instruction của Gemini.
    """
    parts = [build_system_prompt()]

    if preference and preference.arrival_day_of_week:
        warning = build_closure_warning(preference.arrival_day_of_week)
        if warning:
            parts.append(warning)

    parts.append(
        "### DATASET (nguồn dữ liệu duy nhất — không gợi ý ngoài dataset này)\n\n"
        + get_dataset_as_json_str()
    )

    return "\n\n---\n\n".join(parts)


def build_confirmation_message(preference: UserPreference) -> str:
    food_labels = {
        FoodStyle.street_food: "Đường phố 🍜",
        FoodStyle.restaurant: "Nhà hàng 🍽️",
        FoodStyle.hidden_gem: "Local hidden gem 🕵️",
        FoodStyle.mixed: "Kết hợp 🔀",
    }
    place_labels = {
        PlaceType.culture_history: "Văn hóa & lịch sử 🏛️",
        PlaceType.shopping_entertainment: "Vui chơi & mua sắm 🛍️",
        PlaceType.chill_cafe: "Chill & cafe ☕",
        PlaceType.mixed: "Tất cả 🎯",
    }
    exp_labels = {
        ExperienceStyle.local: "Local 🏠",
        ExperienceStyle.tourist: "Tourist-friendly 🗺️",
        ExperienceStyle.family: "Gia đình 👨‍👩‍👧",
    }
    budget_labels = {
        Budget.low: "Tiết kiệm (< 500k) 💚",
        Budget.medium: "Vừa phải (500k–1tr) 💛",
        Budget.high: "Thoải mái (> 1tr) ❤️",
    }

    vn_day = to_vn_day(preference.arrival_day_of_week) if preference.arrival_day_of_week else "?"
    nightlife_str = " + Nightlife 🍺" if preference.nightlife else ""

    return (
        "Tuyệt! Mình đã có đủ thông tin rồi. Để xác nhận:\n\n"
        f"📋 **Sở thích của bạn:**\n"
        f"   • Ăn uống: {food_labels.get(preference.food_style, str(preference.food_style))}\n"
        f"   • Tham quan: {place_labels.get(preference.place_type, str(preference.place_type))}\n"
        f"   • Phong cách: {exp_labels.get(preference.experience, str(preference.experience))}{nightlife_str}\n"
        f"   • Budget: {budget_labels.get(preference.budget, str(preference.budget))}\n"
        f"   • Lịch: {preference.num_days} ngày, bắt đầu {vn_day}\n\n"
        "Đang tạo lịch trình... ⏳"
    )


def build_itinerary_request(preference: UserPreference) -> str:
    vn_day = to_vn_day(preference.arrival_day_of_week) if preference.arrival_day_of_week else "không rõ"
    budget_map = {
        Budget.low: "dưới 500.000 VNĐ/ngày",
        Budget.medium: "500.000–1.000.000 VNĐ/ngày",
        Budget.high: "trên 1.000.000 VNĐ/ngày",
    }
    food_map = {
        FoodStyle.street_food: "đường phố (bún, phở, bánh mì vỉa hè)",
        FoodStyle.restaurant: "nhà hàng (ngồi thoải mái, menu đa dạng)",
        FoodStyle.hidden_gem: "local hidden gem (quán nhỏ ít biết, ngon, rating cao)",
        FoodStyle.mixed: "kết hợp (đường phố + nhà hàng)",
    }
    place_map = {
        PlaceType.culture_history: "văn hóa và lịch sử (đền, chùa, bảo tàng, di tích)",
        PlaceType.shopping_entertainment: "vui chơi và mua sắm (phố cổ, chợ, trung tâm thương mại)",
        PlaceType.chill_cafe: "chill và cafe (hồ, công viên, cafe view đẹp)",
        PlaceType.mixed: "tất cả loại địa điểm",
    }
    exp_map = {
        ExperienceStyle.local: "local (ăn chỗ người địa phương, tránh tourist trap)",
        ExperienceStyle.tourist: "tourist-friendly (tiện nghi, có hướng dẫn)",
        ExperienceStyle.family: "gia đình (đi cùng trẻ em)",
    }

    nightlife_line = (
        "\n- Muốn có bar/pub buổi tối: Có ✅"
        if preference.nightlife
        else "\n- Nightlife: Không cần ❌"
    )

    return (
        f"Hãy tạo lịch trình {preference.num_days} ngày tại Hà Nội cho mình với:\n"
        f"- Phong cách ăn uống: {food_map.get(preference.food_style, str(preference.food_style))}\n"
        f"- Loại địa điểm tham quan: {place_map.get(preference.place_type, str(preference.place_type))}\n"
        f"- Trải nghiệm: {exp_map.get(preference.experience, str(preference.experience))}"
        f"{nightlife_line}\n"
        f"- Ngân sách: {budget_map.get(preference.budget, str(preference.budget))}\n"
        f"- Ngày bắt đầu: {vn_day}\n\n"
        "Lịch trình theo đúng format đã được hướng dẫn, có đủ các khung giờ sáng/trưa/chiều/tối"
        f"{'/ đêm' if preference.nightlife else ''}."
    )
