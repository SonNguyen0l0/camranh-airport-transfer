# 📘 Hướng Dẫn Vận Hành & Nâng Cấp Bot Cam Ranh Transfer

## 🚀 Triển Khai Lên Render

### Bước 1 — Chuẩn bị GitHub
1. Tạo repo mới trên GitHub (ví dụ: `camranh-transfer-bot`)
2. Upload toàn bộ thư mục này lên repo

### Bước 2 — Tạo dịch vụ trên Render
1. Vào [render.com](https://render.com) → **New** → **Web Service**
2. Kết nối GitHub repo vừa tạo
3. Cấu hình:
   - **Name:** `camranh-transfer-bot`
   - **Root Directory:** *(để trống nếu repo chỉ có bot này)*
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
   - **Plan:** Free (đủ dùng cho bot Telegram)

### Bước 3 — Thiết lập biến môi trường (Secrets)
Trong Render → **Environment** → thêm 2 biến:

| Tên biến | Giá trị |
|---|---|
| `BOT_TOKEN` | Token từ @BotFather trên Telegram |
| `ADMIN_CHAT_ID` | Chat ID của bạn (lấy từ @userinfobot) |

### Bước 4 — Deploy
Nhấn **Deploy Web Service**. Bot sẽ chạy sau 1-2 phút.

> ⚠️ **Lưu ý Render Free:** Render Free tắt sau 15 phút không có request. Để bot chạy 24/7, dùng [UptimeRobot](https://uptimerobot.com) ping URL Render mỗi 10 phút, hoặc nâng lên Render Paid ($7/tháng).

---

## 📁 Cấu Trúc File

```
camranh-airport-transfer-v2/
│
├── bot.py                  ← Khởi động bot, đăng ký handlers
├── config.json             ← Cài đặt ngân hàng, tiền cọc
├── routes.json             ← Danh sách tuyến đường & giá
│
├── handlers/
│   ├── booking.py          ← Toàn bộ luồng đặt xe (12 bước)
│   └── admin.py            ← Lệnh /admin, /broadcast, /users
│
├── languages/
│   ├── vi.json             ← Toàn bộ tin nhắn tiếng Việt
│   ├── en.json             ← Toàn bộ tin nhắn tiếng Anh
│   └── ru.json             ← Toàn bộ tin nhắn tiếng Nga
│
├── utils/
│   ├── messages.py         ← Hàm lấy tin nhắn theo ngôn ngữ
│   ├── pricing.py          ← Tính giá, lấy loại xe
│   ├── validation.py       ← Kiểm tra đầu vào (tên, SĐT, ngày...)
│   └── user_store.py       ← Lưu danh sách khách vào data/users.json
│
├── data/
│   └── users.json          ← Danh sách chat_id khách hàng (tự tạo)
│
└── requirements.txt        ← Thư viện Python cần thiết
```

---

## ✏️ Cách Sửa Tin Nhắn Bot

Tất cả câu chữ bot gửi nằm trong `languages/vi.json`, `en.json`, `ru.json`.

**Ví dụ — đổi lời chào:**
```json
// languages/vi.json
"welcome": "🚗 Xin chào! Chào mừng đến với *Cam Ranh Transfer*..."
```

Chỉnh sửa trực tiếp trong file JSON rồi deploy lại.

---

## 🛣️ Cách Thêm / Sửa Tuyến Đường

Mở file `routes.json`:

```json
{
  "routes": [
    {
      "id": "CXR_NHA",
      "label": {
        "vi": "Cam Ranh → Nha Trang",
        "en": "Cam Ranh → Nha Trang",
        "ru": "Кам Рань → Нячанг"
      },
      "prices": {
        "sedan": 250000,
        "suv":   350000,
        "van":   400000
      }
    }
  ]
}
```

**Để thêm tuyến mới:**
1. Copy một block `{}` hiện có
2. Đổi `id` (duy nhất, không dấu cách)
3. Điền tên tuyến theo 3 ngôn ngữ
4. Điền giá cho từng loại xe
5. Deploy lại

---

## 🚗 Cách Thêm / Sửa Loại Xe

Trong `routes.json`, các key giá xe là: `sedan`, `suv`, `van`.

Để thêm loại xe mới (ví dụ `limousine`):
1. Thêm `"limousine": 800000` vào mỗi tuyến trong `routes.json`
2. Trong `utils/pricing.py`, tìm dict `CAR_LABELS` và thêm:
   ```python
   "limousine": {"vi": "Limousine 6 chỗ", "en": "Limousine 6-seat", "ru": "Лимузин 6 мест"}
   ```
3. Trong `handlers/booking.py`, tìm phần tạo nút chọn xe và thêm nút `limousine`

---

## 💳 Cách Đổi Thông Tin Ngân Hàng (QR cọc)

Mở `config.json`:

```json
{
  "deposit": {
    "fixed_amount": 500000,
    "min_price_for_deposit": 500000,
    "bank_id": "MB",
    "account_number": "1234567890",
    "account_name": "NGUYEN VAN A"
  }
}
```

| Trường | Mô tả |
|---|---|
| `fixed_amount` | Số tiền cọc cố định (VND) |
| `min_price_for_deposit` | Giá tối thiểu để yêu cầu cọc |
| `bank_id` | Mã ngân hàng theo VietQR (VD: `MB`, `VCB`, `TCB`, `ACB`) |
| `account_number` | Số tài khoản thụ hưởng |
| `account_name` | Tên chủ tài khoản (IN HOA, không dấu) |

Danh sách mã ngân hàng VietQR: https://api.vietqr.io/v2/banks

---

## 👮 Lệnh Admin (Chỉ ADMIN_CHAT_ID Mới Dùng Được)

| Lệnh | Chức năng |
|---|---|
| `/admin` | Xem tất cả đơn đang chờ xử lý |
| `/admin_clear` | Xoá sạch danh sách đơn |
| `/users` | Xem tổng số khách đã đăng ký |
| `/broadcast <nội dung>` | Gửi tin nhắn tới TẤT CẢ khách |

**Ví dụ broadcast:**
```
/broadcast 🎉 Hôm nay giảm 20% tất cả các tuyến! Đặt xe: /start
```

---

## 🔧 Cách Thêm Câu Lệnh Bot Mới

**Ví dụ: thêm lệnh `/hotline` để bot trả lời số điện thoại**

1. Mở `handlers/admin.py` (hoặc tạo file handler mới)
2. Thêm hàm:
   ```python
   async def cmd_hotline(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
       await update.message.reply_text(
           "📞 *Hotline Cam Ranh Transfer:*\n"
           "• Điện thoại: 0825 779 413\n"
           "• WhatsApp: +84 825 779 413\n"
           "• Telegram: @CR_Airport_Transfer",
           parse_mode="Markdown"
       )
   ```
3. Đăng ký trong `build_admin_handlers()`:
   ```python
   CommandHandler("hotline", cmd_hotline),
   ```
4. Deploy lại

---

## 🌍 Cách Thêm Ngôn Ngữ Mới (Ví Dụ: Tiếng Trung)

1. Copy `languages/vi.json` → `languages/zh.json`
2. Dịch toàn bộ các giá trị sang tiếng Trung
3. Trong `handlers/booking.py`, hàm `start()`, thêm nút:
   ```python
   InlineKeyboardButton("🇨🇳 中文", callback_data="lang_zh"),
   ```
4. Deploy lại

---

## 📦 Cập Nhật Thư Viện

Nếu cần cập nhật phiên bản, sửa `requirements.txt`:

```
python-telegram-bot==20.7
python-dotenv==1.0.0
```

---

## 🐞 Xem Log Khi Có Lỗi

Trên Render: vào **Dashboard** → chọn service → tab **Logs**

Các lỗi thường gặp:
- `BOT_TOKEN is not set` → Chưa thêm biến môi trường trong Render
- `Conflict: terminated by other getUpdates` → Đang chạy bot 2 nơi cùng lúc, tắt bớt 1
- `Chat not found` khi broadcast → Khách đã block bot, bình thường

---

## 📞 Thông Tin Liên Hệ Được Hiển Thị Trong Bot

Muốn đổi số điện thoại/Telegram hiển thị, tìm trong `languages/*.json`:
```json
"booking_confirmed_no_deposit": "...• Telegram: @CR_Airport_Transfer\n• WhatsApp: +84 825 779 413..."
```
Sửa ở cả 3 file: `vi.json`, `en.json`, `ru.json`.
