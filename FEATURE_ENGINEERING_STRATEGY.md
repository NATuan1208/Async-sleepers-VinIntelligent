# 🎯 CHIẾN LƯỢC FEATURE ENGINEERING
## DATATHON 2026 - Sales Forecasting

**Bối cảnh:** Fashion E-commerce Việt Nam (2012-2022)  
**Mục tiêu:** Dự báo Revenue & COGS hàng ngày  
**Input:** Chỉ có cột `Date`  
**Output:** 40 features được tạo ra

---

## 📊 TỔNG QUAN

| Nhóm | Số features | Mục đích chính |
|------|-------------|----------------|
| **1. Calendar & Liquidity Engine** | 6 | Chu kỳ thời gian + chu kỳ ví tiền |
| **2. Tết Nguyên Đán** | 5 | Event lớn nhất năm (văn hóa VN) |
| **3. Fashion Shopping Windows** | 5 | Các dịp lễ ảnh hưởng thời trang |
| **4. E-commerce Sale Days** | 5 | Shopping festivals online |
| **5. Hybrid Memory Engine** | 14 | Lag features 3 tầng (364, 728, stats) |
| **6. Fourier Features** | 2 | Boundary smoother (annual cycle) |
| **7. COVID-19** | 3 | Guide rails cho lag features |
| **TỔNG** | **40** | |

---

## 📋 NHÓM 1: CALENDAR & LIQUIDITY ENGINE (6 features)

**Mục đích:** Bắt chu kỳ thời gian VÀ chu kỳ ví tiền của khách hàng

### Features:

| Feature | Kiểu | Giải thích | Business Logic |
|---------|------|-----------|----------------|
| `day_of_week` | int (0-6) | Thứ trong tuần | 0=T2, 6=CN |
| `month` | int (1-12) | Tháng trong năm | 1-12 |
| `day_of_month` | int (1-31) | Ngày trong tháng | Vị trí trong tháng |
| `is_payday_window` | binary | Cửa sổ nhận lương | 1 nếu ngày ≥ 25 |
| `dist_to_payday` | int (0-30) | Khoảng cách đến payday | Số ngày còn lại đến ngày 28 |
| `is_weekend` | binary | Cuối tuần | 1=T7/CN, 0=T2-T6 |

---

### Chi tiết từng feature:

#### **1. `day_of_week` — Thứ trong tuần (0-6)**

**Nó là gì:** Đánh số từ Thứ 2 (0) đến Chủ nhật (6)

**Tại sao cần:**
- Hành vi mua sắm online thay đổi theo ngày cực kỳ rõ rệt
- **Thứ 2-3:** Chốt đơn mạnh nhất (khách muốn shipper giao trong tuần)
- **Thứ 5-6:** Peak browse (chuẩn bị cuối tuần)
- **Thứ 7-CN:** Browse nhiều, chốt ít hơn T2

**Model học gì:**
- Pattern 7 ngày/tuần rõ ràng
- Các "hố đen" doanh thu (giữa tuần) và "đỉnh" doanh thu (đầu tuần/cuối tuần)

---

#### **2. `month` — Tháng trong năm (1-12)**

**Nó là gì:** Giá trị từ tháng 1 đến tháng 12

**Tại sao cần:**
- Ngành Fashion sống chết nhờ seasonality
- **Tháng 11-12:** Đỉnh điểm đồ đông, áo khoác (giá trị đơn hàng cao)
- **Tháng 1-2:** Cao (Tết)
- **Tháng 5-6:** Đồ hè, đồ bơi
- **Tháng 7 Âm:** Thấp (tháng cô hồn)

**Model học gì:**
- Bắt được tính mùa vụ (Annual Seasonality)
- COGS cũng biến động theo tháng (đồ đông đắt hơn đồ hè)

---

#### **3. `day_of_month` — Ngày trong tháng (1-31)**

**Nó là gì:** Vị trí của ngày đó trong tháng

**Tại sao cần:**
- Đánh vào chu kỳ ví tiền
- Người Việt có thói quen:
  - **Ngày 1-10:** Vừa có lương → chi tiêu mạnh
  - **Ngày 11-24:** Giảm dần (hết tiền dần)
  - **Ngày 25-31:** Spike lại (lương tháng sau sắp về)

**Model học gì:**
- Chu kỳ trong tháng (U-shaped pattern)
- Sự sụt giảm/tăng trở lại của revenue theo ngày

---

#### **4. `is_payday_window` — Cửa sổ nhận lương (Binary)**

**Nó là gì:** Đánh dấu `1` cho các ngày 25-31 trong tháng

```python
is_payday_window = 1 if (day_of_month >= 25) else 0
```

**Tại sao cần:**
- Lương VN thường trả: **25-30 hàng tháng**
- Đây là lúc Shopee/Lazada tung ra nhiều mã giảm giá nhất
- Flash sale tập trung vào khung này

**Model học gì:**
- Tạo ra một spike cực mạnh cho Revenue
- Thay vì để model tự mò, feature này "chỉ điểm" luôn: "Ê, ngày này khách có tiền đấy!"

**Expected impact:** Revenue ngày 25-31 cao hơn 20-30% so với ngày 15-24

---

#### **5. `dist_to_payday` — Khoảng cách tới ngày lương (Integer) ⭐ FEATURE SÁNG TẠO**

**Nó là gì:** Số ngày còn lại đến payday (ngày 28 hàng tháng)

```python
def calc_dist_to_payday(date):
    payday = 28  # Có thể điều chỉnh
    day = date.day
    
    if day <= payday:
        return payday - day
    else:
        # Sau payday, đếm đến tháng sau
        days_in_month = calendar.monthrange(date.year, date.month)[1]
        return (days_in_month - day) + payday
```

**Ví dụ:**
```
Ngày 20 → dist = 8 ngày   (revenue trung bình)
Ngày 26 → dist = 2 ngày   (revenue bắt đầu tăng mạnh)
Ngày 28 → dist = 0 ngày   (revenue CAO NHẤT - payday!)
Ngày 30 → dist = 27 ngày  (revenue sụt ngay)
Ngày 15 → dist = 13 ngày  (revenue thấp - giữa tháng)
```

**Tại sao cần:**
- Đây là biến "dự báo sớm"
- **10 ngày nữa mới có lương:** Khách chỉ xem, không mua
- **1 ngày nữa có lương:** Khách bắt đầu chốt đơn hàng loạt

**Model học gì:**
- Học được gradient tăng dần (trend)
- Revenue không tăng đột ngột mà "ấm dần lên" khi tiến gần payday
- Relationship: `Revenue ~ -0.5 * dist_to_payday` (càng gần 0 càng cao)

**Tại sao cần CẢ `is_payday_window` VÀ `dist_to_payday`?**
- `is_payday_window`: Binary → Bắt "có spike hay không"
- `dist_to_payday`: Continuous → Bắt "tốc độ tăng dần"
- Kết hợp 2 cái → Bắt cả step function VÀ gradient!

---

#### **6. `is_weekend` — Cuối tuần (Binary)**

**Nó là gì:** Đánh dấu `1` cho Thứ 7 và Chủ nhật

```python
is_weekend = 1 if (day_of_week >= 5) else 0  # 5,6 = Sat, Sun
```

**Tại sao cần:**
- Thứ 7-CN: Peak browse time
- Khách có thời gian rảnh để "lướt" Shopee/Lazada
- Conversion rate cao (có thời gian suy nghĩ, compare giá)

**Model học gì:**
- Explicit weekend effect
- Dễ interpret trong SHAP: "Weekend boost = +12% revenue"

**Có trùng với `day_of_week` không?**
- Có, nhưng giữ vì explainability
- Business stakeholders dễ hiểu "weekend effect" hơn "day_of_week coefficient"

---

### Insight kinh doanh tổng hợp:

✅ **Chu kỳ tuần:** T2-T3 chốt mạnh, T7-CN browse nhiều  
✅ **Chu kỳ tháng:** U-shaped (cao đầu tháng, thấp giữa tháng, cao lại cuối tháng)  
✅ **Payday effect:** Spike cực mạnh ngày 25-31 (lương về)  
✅ **Seasonality:** Tháng 11-12-1-2 cao (Tết + đồ đông)

---

## 🧧 NHÓM 2: TẾT NGUYÊN ĐÁN (5 features)

**Mục đích:** Bắt event quan trọng nhất của văn hóa Việt Nam

### Features:

| Feature | Kiểu | Giải thích | Business Logic |
|---------|------|-----------|----------------|
| `days_to_tet` | int | Khoảng cách đến Tết | Countdown: -30 → +15 |
| `is_tet_buildup` | binary | Giai đoạn sắm Tết | 21-11 ngày trước Tết |
| `is_tet_peak` | binary | Đỉnh mua sắm | 10-4 ngày trước Tết |
| `is_tet_holiday` | binary | Nghỉ Tết | 3 ngày trước → Mùng 3 |
| `is_tet_reopening` | binary | Khai xuân | Mùng 4-10 |

---

### Chi tiết từng feature:

#### **1. `days_to_tet` — Countdown đến Tết (Integer)**

**Nó là gì:** Số ngày còn lại đến Mùng 1 Tết Nguyên Đán

```python
# Công thức:
days_to_tet = (current_date - tet_date).days

# Ví dụ (Tết 2023 = 22/01/2023):
Ngày 15/01/2023 → days_to_tet = -7  (7 ngày trước Tết)
Ngày 22/01/2023 → days_to_tet = 0   (Mùng 1 Tết)
Ngày 25/01/2023 → days_to_tet = 3   (Mùng 4)
Ngày 01/02/2023 → days_to_tet = 10  (Mùng 11)
```

**Tại sao cần:**
- Bắt **gradient tăng dần** của revenue khi tiến gần Tết
- Không phải tất cả ngày trong "peak window" đều có revenue bằng nhau
- Ngày -5 thường cao hơn ngày -10 (last-minute shopping)

**Model học gì:**
- Relationship: `Revenue ~ f(days_to_tet)` với f là non-linear
- Càng gần 0 (Mùng 1), revenue càng cao (cho đến điểm cutoff)
- Sau Tết (positive values), revenue sụt giảm

**Expected pattern:**
```
days_to_tet = -20 → Revenue trung bình
days_to_tet = -10 → Revenue bắt đầu tăng
days_to_tet = -5  → Revenue cao nhất
days_to_tet = -1  → Revenue giảm (giao hàng không kịp)
days_to_tet = 0   → Revenue = 0 (đóng cửa)
days_to_tet = 5   → Revenue phục hồi nhẹ (lì xì)
```

---

#### **2. `is_tet_buildup` — Giai đoạn sắm Tết (Binary)**

**Nó là gì:** Đánh dấu `1` cho khoảng 21-11 ngày trước Tết

```python
is_tet_buildup = 1 if (-21 <= days_to_tet < -10) else 0
```

**Tại sao cần:**
- Đây là lúc khách hàng bắt đầu "duyệt" và "lên list"
- Revenue tăng nhẹ so với ngày thường
- Browse nhiều hơn, conversion rate chưa cao

**Model học gì:**
- Định nghĩa window: "Đây là buildup phase"
- Base revenue cao hơn ngày thường 10-20%

**Business insight:**
- Khách hàng đang trong giai đoạn "cân nhắc"
- Chưa phải lúc chốt đơn mạnh nhất

---

#### **3. `is_tet_peak` — Đỉnh mua sắm (Binary) ⭐ CRITICAL**

**Nó là gì:** Đánh dấu `1` cho khoảng 10-4 ngày trước Tết

```python
is_tet_peak = 1 if (-10 <= days_to_tet < -3) else 0
```

**Tại sao cần:**
- **Đây là window quan trọng NHẤT** với fashion e-commerce
- Khách hàng chốt đơn để kịp nhận hàng trước Tết
- Văn hóa Việt: Tết phải mặc đồ MỚI

**Model học gì:**
- Peak revenue window
- Kết hợp với `days_to_tet` để học gradient trong peak

**Expected impact:**
```
Trong peak window:
- Revenue cao hơn 150-200% so với ngày thường
- COGS cũng tăng (nhập hàng nhiều)
- Conversion rate cao nhất trong năm
```

**Business insight:**
- Ngày -7, -6, -5: Đặt hàng online cực mạnh
- Ngày -4: Bắt đầu giảm (lo không kịp giao)

---

#### **4. `is_tet_holiday` — Nghỉ Tết (Binary)**

**Nó là gì:** Đánh dấu `1` cho khoảng 3 ngày trước Tết → Mùng 3

```python
is_tet_holiday = 1 if (-3 <= days_to_tet <= 3) else 0
```

**Tại sao cần:**
- Shop **ĐÓNG CỬA** hoàn toàn
- Revenue ≈ 0 (có thể có vài đơn tự động)
- Shipper nghỉ Tết

**Model học gì:**
- Revenue drop xuống gần 0
- Đây là outlier window cần flag riêng

**Business insight:**
```
Ngày -3, -2, -1: Giao hàng gấp (shipper về quê)
Mùng 1, 2, 3: Đóng cửa hoàn toàn
```

---

#### **5. `is_tet_reopening` — Khai xuân (Binary)**

**Nó là gì:** Đánh dấu `1` cho khoảng Mùng 4-10

```python
is_tet_reopening = 1 if (4 <= days_to_tet <= 10) else 0
```

**Tại sao cần:**
- Mở cửa trở lại sau Tết
- Khách hàng dùng **tiền lì xì** để mua sắm
- Revenue phục hồi nhưng chưa về mức bình thường

**Model học gì:**
- Post-holiday recovery pattern
- Revenue trung bình (40-60% ngày bình thường)

**Business insight:**
- Mùng 4-5: Bắt đầu mở cửa, đơn chậm
- Mùng 6-7: Tăng dần
- Mùng 10: Gần về bình thường

---

### Ngày Tết Âm lịch (hardcoded 2013-2024):

```python
TET_DATES = {
    2013: '2013-02-10',  2014: '2014-01-31',  2015: '2015-02-19',  2016: '2016-02-08',
    2017: '2017-01-28',  2018: '2018-02-16',  2019: '2019-02-05',  2020: '2020-01-25',
    2021: '2021-02-12',  2022: '2022-02-01',  2023: '2023-01-22',  2024: '2024-02-10',
}
```

---

### Tại sao cần CẢ `days_to_tet` VÀ 4 binary flags:

| Component | Mục đích | Model học được |
|-----------|----------|----------------|
| **`days_to_tet`** | **Gradient** | "Từ -10 → -4: revenue tăng dần đến đỉnh" |
| **Binary flags** | **Phase definition** | "Đây là peak phase, khác buildup" |

**Ví dụ model có thể học:**
```python
if is_tet_peak == 1:
    # Trong peak window, dùng gradient
    if days_to_tet >= -5:
        revenue = 2000  # Very close to Tet
    elif days_to_tet >= -8:
        revenue = 1500  # Close to Tet
    else:
        revenue = 1000  # Start of peak
elif is_tet_buildup == 1:
    revenue = 500 + abs(days_to_tet) * 10  # Tăng dần
else:
    revenue = 300  # Normal day
```

→ **Model VỪA biết đang ở phase nào, VỪA biết gradient trong phase!**

---

### Insight kinh doanh tổng hợp:

✅ **Peak window (10-4 ngày trước):** Đỉnh cao nhất - fashion online MUST HAVE  
✅ **Gradient effect:** Càng gần Tết trong peak, càng mua nhiều  
✅ **Holiday effect:** Mùng 1-3 = đóng cửa hoàn toàn  
✅ **Khai xuân (Mùng 4-10):** Recovery nhẹ nhờ tiền lì xì

---

## 🎊 NHÓM 3: FASHION SHOPPING WINDOWS (5 features)

**Mục đích:** Bắt các dịp lễ/sự kiện ảnh hưởng mua sắm thời trang

### Features:

| Feature | Kiểu | Giải thích | Coverage |
|---------|------|-----------|----------|
| `is_gift_peak` | binary | Cửa sổ mua quà tặng | 8/3, 20/10, 14/2 |
| `is_travel_peak` | binary | Cửa sổ đồ du lịch | 30/4, 2/9 |
| `is_year_end_festive` | binary | Mùa tiệc cuối năm | 10/12 → 30/12 |
| `is_ghost_month` | binary | Tháng cô hồn | Tháng 7 Âm lịch |
| `dist_to_nearest_holiday` | int | Countdown đến lễ gần nhất | Gradient universal |

---

### Chi tiết từng feature:

#### **1. `is_gift_peak` — Cửa sổ mua quà tặng (Binary)**

**Nó là gì:** Đánh dấu `1` cho window 7 → 2 ngày TRƯỚC các ngày lễ tặng quà

```python
gift_events = [
    (3, 8),    # 8/3 - Quốc tế Phụ nữ
    (10, 20),  # 20/10 - Phụ nữ Việt Nam
    (2, 14),   # 14/2 - Valentine
]

# 7 ngày trước → 2 ngày trước event
is_gift_peak = 1 if (-7 <= days_to_event < -2) else 0
```

**Tại sao cần:**
- Đây là lúc khách hàng **đặt mua online** để kịp nhận hàng trước lễ
- Fashion e-commerce: Mua váy/áo đẹp để đi chơi hoặc làm quà tặng
- **KHÔNG đánh dấu đúng ngày lễ** vì lúc đó đang ăn chơi, không order

**Tại sao 7 → 2 ngày:**
```
Ngày -7:  Bắt đầu browse, suy nghĩ
Ngày -5:  Chốt đơn mạnh (peak trong window)
Ngày -3:  Vẫn còn order
Ngày -2:  Sợ shipper không kịp giao
Ngày -1:  Giảm mạnh
Ngày 0:   Đang đi chơi, không order
```

**Fashion items spike:**
- 8/3, 20/10: Váy công sở, áo sơ mi, phụ kiện
- 14/2: Party dress, váy hẹn hò, áo đẹp

**Expected impact:** Revenue tăng 30-50% trong window

---

#### **2. `is_travel_peak` — Cửa sổ đồ du lịch (Binary)**

**Nó là gì:** Đánh dấu `1` cho window 10 → 3 ngày TRƯỚC các kỳ nghỉ lễ dài

```python
travel_events = [
    (4, 30),   # 30/4 (nghỉ 1 tuần)
    (9, 2),    # 2/9 (nghỉ 3-4 ngày)
]

# 10 ngày trước → 3 ngày trước
is_travel_peak = 1 if (-10 <= days_to_event < -3) else 0
```

**Tại sao cần:**
- Người Việt đi du lịch biển, resort trong 2 kỳ nghỉ lễ này
- Cần mua sắm sớm để chuẩn bị hành lý

**Tại sao 10 → 3 ngày:**
```
Ngày -10: Plan sớm, mua bikini, váy đi biển
Ngày -7:  Chốt đơn mạnh
Ngày -5:  Last-minute shopping
Ngày -3:  Cutoff (lo không kịp giao)
Ngày 0:   Đã đi du lịch rồi
```

**Fashion items spike:**
- Bikini, swimwear
- Váy maxi, đầm đi biển
- Shorts, áo thun
- Sandals, dép

**Expected impact:** Revenue tăng 50-60% (đặc biệt summer wear)

---

#### **3. `is_year_end_festive` — Mùa tiệc cuối năm (Binary)**

**Nó là gì:** Đánh dấu `1` cho khoảng 10/12 → 30/12

```python
is_year_end_festive = 1 if (month == 12 and 10 <= day <= 30) else 0
```

**Tại sao cần:**
- **10-15/12:** Mua đồ cho tiệc công ty (Year-end party)
- **16-23/12:** Noel shopping (festive wear)
- **24-30/12:** Chuẩn bị Tết Tây (countdown party)

**Fashion items spike:**
- Party dress (đỏ, đen, sequin)
- Blazer, suit
- Festive accessories
- Heels

**Expected impact:** Revenue tăng 60-80% (cao nhất sau Tết)

**Business insight:**
- Đây là window thứ 2 quan trọng nhất trong năm (sau Tết)
- COGS cao (party wear đắt hơn casual)
- Premium segment đóng góp nhiều

---

#### **4. `is_ghost_month` — Tháng cô hồn (Binary)**

**Nó là gì:** Đánh dấu `1` cho toàn bộ tháng 7 Âm lịch

```python
# Map Gregorian → Lunar calendar
is_ghost_month = 1 if (lunar_month == 7) else 0
```

**Tại sao cần:**
- Văn hóa Việt: Tháng 7 Âm = kiêng kỵ
- Không cưới, không khai trương, không mua nhà/xe
- → **KIÊNG mua sắm thời trang lớn**

**Tại sao CẢ THÁNG:**
- Không phải 1 ngày cụ thể
- Tâm lý kiêng kỵ kéo dài cả tháng
- Erring on the safe side → trì hoãn chi tiêu

**Impact theo segment:**
```
Premium (áo vest, suit, áo khoác):    -30%
Standard (áo thun, quần jeans):       -10%
Overall fashion e-commerce:           -15-20%
```

**Model học gì:**
- Binary flag để đánh dấu "outlier period"
- Revenue baseline thấp hơn bình thường
- Không phải seasonality tự nhiên mà là cultural effect

---

#### **5. `dist_to_nearest_holiday` — Countdown đến lễ (Integer) ⭐ KEY FEATURE**

**Nó là gì:** Số ngày còn lại đến lễ fashion-relevant gần nhất

```python
def calc_dist_to_nearest_holiday(date):
    """
    Tính khoảng cách đến lễ gần nhất
    EXCLUDE Tết (đã có days_to_tet riêng)
    """
    holidays = [
        (3, 8),    # 8/3
        (10, 20),  # 20/10
        (2, 14),   # 14/2
        (4, 30),   # 30/4
        (9, 2),    # 2/9
        (12, 24),  # Noel
        (1, 1),    # Tết Dương lịch
    ]
    
    distances = []
    for month, day in holidays:
        # Tính khoảng cách đến event này năm nay
        event_date = pd.Timestamp(date.year, month, day)
        dist = (event_date - date).days
        
        # Nếu event đã qua, tính đến năm sau
        if dist < 0:
            event_date_next = pd.Timestamp(date.year + 1, month, day)
            dist = (event_date_next - date).days
        
        distances.append(dist)
    
    return min(distances)
```

**Ví dụ:**
```
Ngày 01/03 → dist = 7 ngày (đến 8/3)
Ngày 05/03 → dist = 3 ngày (đến 8/3)
Ngày 08/03 → dist = 0 (đúng ngày lễ)
Ngày 10/03 → dist = 20 ngày (đến 30/4, lễ tiếp theo)
```

**Tại sao cần:**
- Bắt **gradient universal** cho tất cả lễ
- Không cần hardcode gradient cho từng lễ riêng
- Model tự học pattern: "Càng gần lễ, revenue càng cao"

**Model học gì:**
```python
# Pattern universal:
dist = 15-30 → Revenue bình thường
dist = 7-10  → Revenue tăng nhẹ (bắt đầu browse)
dist = 3-5   → Revenue cao (chốt đơn mạnh)
dist = 1-2   → Revenue giảm (lo không kịp)
dist = 0     → Revenue thấp (đang ăn chơi)
```

**Tại sao XUẤT SẮC:**
- ✅ Scale tốt khi thêm lễ mới
- ✅ Model tự học, không cần feature engineering phức tạp
- ✅ Kết hợp với binary flags → comprehensive coverage

---

### Tại sao cần CẢ binary flags VÀ `dist_to_nearest_holiday`:

| Component | Mục đích | Model học được |
|-----------|----------|----------------|
| **Binary flags** | **Phase definition** | "8/3 có impact khác 14/2" |
| **`dist_to_nearest_holiday`** | **Gradient universal** | "Càng gần lễ, càng cao" |

**Ví dụ model có thể học:**
```python
if is_gift_peak == 1:
    # Đang trong gift window, check gradient
    if dist_to_nearest_holiday <= 3:
        revenue = 2000  # Very close
    elif dist_to_nearest_holiday <= 5:
        revenue = 1500  # Close
    else:
        revenue = 1000  # Start of window
elif is_travel_peak == 1:
    revenue = 1200 + (10 - dist_to_nearest_holiday) * 50
else:
    revenue = 500
```

→ **VỪA biết đang ở window nào, VỪA biết gradient trong window!**

---

### Danh sách lễ đã cover (Fashion-relevant):

✅ **Valentine (14/2)** - Hẹn hò → váy đẹp  
✅ **8/3** - Quốc tế Phụ nữ → quà tặng  
✅ **20/10** - Phụ nữ VN → quà tặng  
✅ **30/4** - Du lịch → resort wear  
✅ **2/9** - Du lịch → summer dress  
✅ **Noel (24-25/12)** - Tiệc → party dress  
✅ **Tết Dương (1/1)** - Countdown → party wear  
✅ **Tháng 7 Âm** - Kiêng kỵ → giảm revenue

**Lễ bỏ qua (Không fashion-relevant):**
❌ 20/11 (Nhà giáo) - Quà hoa/thiệp, không thời trang  
❌ Trung Thu - Quà bánh/đèn, fashion impact nhỏ  
❌ 1/6 (Thiếu nhi) - Đồ chơi  
❌ Halloween - Too niche ở VN

---

### Insight kinh doanh tổng hợp:

✅ **Shopping window ≠ Event day:** Khách đặt TRƯỚC để kịp nhận hàng  
✅ **Lead time quan trọng:** 3-7 ngày trước lễ = peak order time  
✅ **Gift occasions:** 8/3, 20/10, 14/2 có pattern giống nhau  
✅ **Travel prep:** 30/4, 2/9 cần lead time dài hơn (10 ngày)  
✅ **Year-end:** Window dài nhất (3 tuần) vì nhiều events liên tiếp  
✅ **Ghost month:** Văn hóa VN unique, impact mạnh -15-20%

---

## 🛒 NHÓM 4: E-COMMERCE SALE DAYS (5 features)

**Mục đích:** Bắt các ngày sale lớn của thương mại điện tử

### Features:

| Feature | Kiểu | Giải thích | Range/Values |
|---------|------|-----------|--------------|
| `shopping_festival_score` | ordinal | Phân cấp độ "khủng" của sale | 0-3 |
| `days_to_next_big_sale` | int | Countdown đến sale lớn tiếp theo | 0-365 |
| `is_sale_leadup` | binary | Giai đoạn thu thập mã giảm giá | 1-3 ngày trước |
| `is_black_friday` | binary | Black Friday | Thứ 6 sau Thanksgiving |
| `is_cyber_monday` | binary | Cyber Monday | Thứ 2 sau Black Friday |

---

### Chi tiết từng feature:

#### **1. `shopping_festival_score` — Phân cấp độ sale (Ordinal 0-3) ⭐ KEY FEATURE**

**Nó là gì:** Gán trọng số 0-3 để model nhận diện **"độ khủng"** của sale

```python
def calc_shopping_festival_score(date):
    month = date.month
    day = date.day
    
    # Level 3: Siêu Sale (Mega Sale)
    if (month == 11 and day == 11) or (month == 12 and day == 12):
        return 3
    
    # Level 2: Sale lớn (Mid-Season)
    elif (month == 9 and day == 9) or (month == 10 and day == 10):
        return 2
    
    # Level 1: Sale định kỳ
    elif (month == day) and (1 <= day <= 8):  # 1/1, 2/2, ..., 8/8
        return 1
    
    # Level 0: Ngày thường
    else:
        return 0
```

**Phân cấp logic:**

| Level | Tên gọi | Ngày áp dụng | Expected Revenue Impact |
|-------|---------|--------------|------------------------|
| **0** | Ngày thường | Tất cả ngày khác | Baseline (100%) |
| **1** | Sale định kỳ | 1/1, 2/2, ..., 8/8 | +20-50% |
| **2** | Sale lớn | 9/9, 10/10 | +100-200% (gấp 2-3 lần) |
| **3** | Siêu Sale | 11/11, 12/12 | +400-900% (gấp 5-10 lần) |

**Tại sao cần:**
- ✅ **Model học hierarchy:** LightGBM có thể split "if score >= 2" → dự báo cao
- ✅ **Reflect reality:** 11/11 THỰC SỰ lớn hơn 2/2 gấp nhiều lần
- ✅ **Ordinal encoding có ý nghĩa:** 3 > 2 > 1 > 0

**Business insight:**

**Level 1 (1/1 - 8/8):** Sale duy trì hàng tháng
- Mục đích: Maintain engagement
- Giảm giá: 10-20%
- Fashion: Clearance items, old stock

**Level 2 (9/9, 10/10):** Giao mùa (Fashion Season Change)
- Mục đích: Clear summer stock, introduce fall/winter
- Giảm giá: 30-50%
- Fashion: Đồ Thu-Đông bắt đầu bán

**Level 3 (11/11, 12/12):** Peak shopping events
- **11/11 Singles Day:** Lớn nhất năm ở VN
- **12/12 Year-end:** Chuẩn bị Tết
- Giảm giá: 50-70% (flash deals)
- Fashion: MỌI danh mục đều sale mạnh

**Model học gì:**
```python
# Decision tree có thể học:
if shopping_festival_score == 3:
    revenue = 5000  # Mega spike
elif shopping_festival_score == 2:
    revenue = 2000  # Strong spike
elif shopping_festival_score == 1:
    revenue = 1200  # Moderate spike
else:
    revenue = 1000  # Baseline
```

---

#### **2. `days_to_next_big_sale` — Countdown đến sale lớn (Integer) ⭐ GRADIENT FEATURE**

**Nó là gì:** Số ngày còn lại đến sale lớn tiếp theo

```python
def calc_days_to_next_big_sale(date):
    """
    Tính countdown đến BIG SALE tiếp theo
    Big sales: 9/9, 10/10, 11/11, 12/12, Black Friday, Cyber Monday
    """
    big_sales = [
        (9, 9),    # 9/9
        (10, 10),  # 10/10
        (11, 11),  # 11/11
        (12, 12),  # 12/12
    ]
    
    # Add Black Friday & Cyber Monday (dates vary by year)
    bf_date = get_black_friday(date.year)
    cm_date = bf_date + pd.Timedelta(days=3)
    
    distances = []
    
    # Fixed date sales
    for month, day in big_sales:
        sale_date = pd.Timestamp(date.year, month, day)
        dist = (sale_date - date).days
        
        # If sale already passed this year, check next year
        if dist < 0:
            sale_date_next = pd.Timestamp(date.year + 1, month, day)
            dist = (sale_date_next - date).days
        
        distances.append(dist)
    
    # Black Friday & Cyber Monday
    for sale_date in [bf_date, cm_date]:
        dist = (sale_date - date).days
        if dist < 0:
            # Next year's BF/CM
            bf_next = get_black_friday(date.year + 1)
            cm_next = bf_next + pd.Timedelta(days=3)
            distances.append((bf_next - date).days)
            distances.append((cm_next - date).days)
        else:
            distances.append(dist)
    
    return min(distances)
```

**Ví dụ:**
```
Ngày 01/11 → days = 10 (đến 11/11)
Ngày 09/11 → days = 2  (revenue HẺO - chờ sale!)
Ngày 11/11 → days = 0  (sale day - revenue NỔ!)
Ngày 13/11 → days = 29 (đến 12/12)
Ngày 15/12 → days = 352 (đến 9/9 năm sau)
```

**Tại sao cần:**
- ✅ Bắt tâm lý **"nhịn mua"** chờ sale
- ✅ Giải thích revenue **hẻo** 2-3 ngày trước big sale
- ✅ Gradient mượt, không binary

**Expected pattern:**
```
days = 15-30 → Revenue bình thường
days = 7-10  → Revenue giảm nhẹ (bắt đầu chờ)
days = 3-5   → Revenue giảm mạnh (chờ sale)
days = 1-2   → Revenue cực thấp (tất cả đợi 0:00 sale bắt đầu)
days = 0     → Revenue NỔ (sale day!)
days = 1+ (after) → Phục hồi
```

**Model học gì:**
```python
# Relationship phi tuyến:
if days_to_next_big_sale == 0:
    revenue = 5000  # Sale day
elif days_to_next_big_sale <= 2:
    revenue = 500   # Pre-sale slump
elif days_to_next_big_sale <= 5:
    revenue = 800   # Waiting period
else:
    revenue = 1000  # Normal
```

**Business insight:**
- Người mua ONLINE biết sale sắp đến (marketing aggressive)
- Họ **chủ động trì hoãn** mua hàng để đợi giảm giá
- Đây là behavior đặc trưng của e-commerce, không có ở retail offline

---

#### **3. `is_sale_leadup` — Giai đoạn chuẩn bị sale (Binary)**

**Nó là gì:** Đánh dấu `1` cho 1-3 ngày TRƯỚC big sale

```python
is_sale_leadup = 1 if (1 <= days_to_next_big_sale <= 3) else 0
```

**Tại sao cần:**
- Giai đoạn này các platform (Shopee, Lazada) cho khách **"thu thập mã giảm giá"**
- Revenue **rục rịch** tăng nhưng chưa NỔ
- Complement cho `days_to_next_big_sale`

**Ví dụ:**
```
Ngày 08/11 → is_sale_leadup = 1, days_to_next_big_sale = 3
Ngày 10/11 → is_sale_leadup = 1, days_to_next_big_sale = 1
Ngày 11/11 → is_sale_leadup = 0, days_to_next_big_sale = 0 (sale day!)
Ngày 12/11 → is_sale_leadup = 0, days_to_next_big_sale = 30
```

**Expected impact:**
- Revenue: Thấp hơn normal (70-80%)
- Browse traffic: Cao (khách add to cart, chưa checkout)
- Conversion rate: Thấp

**Model học gì:**
- Explicit signal: "Đây là pre-sale period, revenue sẽ thấp"
- Insurance cho `days_to_next_big_sale` (binary flag dễ interpret)

---

#### **4. `is_black_friday` — Black Friday (Binary)**

**Nó là gì:** Đánh dấu `1` cho ngày Black Friday (thứ 6 sau thứ 5 thứ 4 tháng 11)

```python
def get_black_friday(year):
    """Thứ 6 sau thứ 5 thứ 4 của tháng 11"""
    first_day = pd.Timestamp(year, 11, 1)
    days_until_thursday = (3 - first_day.dayofweek) % 7
    first_thursday = first_day + pd.Timedelta(days=days_until_thursday)
    fourth_thursday = first_thursday + pd.Timedelta(days=21)
    black_friday = fourth_thursday + pd.Timedelta(days=1)
    return black_friday

is_black_friday = 1 if (date == get_black_friday(date.year)) else 0
```

**Tại sao cần:**
- Black Friday KHÔNG phải double day (không rơi vào ngày trùng tháng)
- Western import nhưng có impact lớn ở VN từ 2018+
- Cần handle riêng vì date thay đổi hàng năm

**Expected dates:**
```
2022: 25/11/2022
2023: 24/11/2023
2024: 29/11/2024
```

**Expected impact:**
- Revenue spike: +150-250% (level 2-2.5)
- Đặc biệt: Fashion online (Shopee, Lazada sale mạnh)
- COGS cao (giảm giá deep nhưng volume lớn)

---

#### **5. `is_cyber_monday` — Cyber Monday (Binary)**

**Nó là gì:** Đánh dấu `1` cho ngày Cyber Monday (thứ 2 sau Black Friday)

```python
def get_cyber_monday(year):
    """Thứ 2 sau Black Friday (3 ngày sau)"""
    bf = get_black_friday(year)
    return bf + pd.Timedelta(days=3)

is_cyber_monday = 1 if (date == get_cyber_monday(date.year)) else 0
```

**Expected dates:**
```
2022: 28/11/2022
2023: 27/11/2023
2024: 02/12/2024
```

**Expected impact:**
- Revenue spike: +100-150% (nhỏ hơn Black Friday)
- "Online Monday" → E-commerce focus
- Fashion: Clearance từ Black Friday

---

### Tại sao cần CẢ `shopping_festival_score` VÀ binary flags:

| Component | Mục đích | Model học được |
|-----------|----------|----------------|
| **`shopping_festival_score`** | **Hierarchy** | "11/11 > 9/9 > 1/1" |
| **`days_to_next_big_sale`** | **Gradient** | "Pre-sale slump → Sale spike" |
| **`is_sale_leadup`** | **Phase flag** | "Đang trong preparation window" |
| **Black Friday/Cyber Monday** | **Special events** | "Western sales, riêng biệt khỏi double days" |

---

### Insight kinh doanh tổng hợp:

✅ **Hierarchy matters:** 11/11 ≠ 1/1 (có thể chênh 10x revenue)  
✅ **Pre-sale slump:** 1-3 ngày trước sale = revenue thấp (khách chờ)  
✅ **Western imports:** Black Friday có impact từ 2018+  
✅ **E-commerce behavior:** "Nhịn mua" chờ sale = unique to online  
✅ **COGS spike:** Sale days có revenue cao NHƯNG margin thấp (deep discounts)

---

### Expected Top Dates by Revenue (Fashion E-commerce VN):

1. 🥇 **11/11** - Singles Day (score=3)
2. 🥈 **12/12** - Year-end mega sale (score=3)
3. 🥉 **Black Friday** - Western import
4. **9/9** - Shopee birthday (score=2)
5. **10/10** - Lazada sale (score=2)
6. **Cyber Monday** - Online Monday
7. **6/6, 7/7, 8/8** - Mid-year sales (score=1)

---

## 🧠 NHÓM 5: HYBRID MEMORY ENGINE (14 features)

**Mục đích:** Bộ nhớ 3 tầng - Near-term (364) + Safe Anchor (728) + Pattern Statistics

**Triết lý thiết kế:**
```
1. Raw + Smoothed = LightGBM tự tính anomaly (Raw - Smoothed)
2. Lookup Tables = Zero leakage, always available
3. YoY Growth = Normalize inflation & scale-up
```

---

### Features Overview:

| Group | Features | Description |
|-------|----------|-------------|
| **A. Near-term Memory** | 2 | lag_364 (iterative) |
| **B. Safe Anchor** | 4 | lag_728 raw + smoothed |
| **C. Pattern Statistics** | 8 | Lookup tables từ train |
| **TOTAL** | **14** | |

---

### **A. NEAR-TERM MEMORY (2 features) - Iterative**

```python
1. rev_lag_364              # Revenue 364 ngày trước
2. cogs_lag_364             # COGS 364 ngày trước
```

**Tại sao 364 thay vì 365:**
- 364 = 52 × 7 tuần → Alignment đúng thứ
- Thứ 7 năm nay = Thứ 7 năm ngoái
- Fashion: Thứ 7 ≠ Thứ 2 (hành vi mua khác nhau)

**Iterative prediction:** Test date 2024-06-01 cần lag_364 = 2023-06-01 (từ predictions)

---

### **B. SAFE ANCHOR (4 features) - Always Available**

```python
3. rev_lag_728                  # Raw value 2 năm trước
4. cogs_lag_728                 
5. rev_roll_mean_28_lag_728     # Smoothed baseline
6. cogs_roll_mean_28_lag_728
```

**Tại sao cần CẢ raw VÀ smoothed:**

```python
# LightGBM tự tính anomaly:
anomaly_score = rev_lag_728 - rev_roll_mean_28_lag_728

# Ví dụ:
# Date: 2024-11-11 (Singles Day)
# rev_lag_728 = 50,000 VND (spike!)
# rev_roll_mean_28_lag_728 = 10,000 VND (baseline)
# Anomaly = 40,000 → Model: "11/11 là special day!"
```

**Always safe:** Test max 548 days < 728 days → luôn có data từ train

---

### **C. PATTERN STATISTICS (8 features) - Lookup Tables**

Pre-computed từ TOÀN BỘ train data (2012-2022):

```python
# C.1 Mean by (day_of_week, month)
7. stat_rev_mean_dow_month      # "Thứ 7 tháng 11 thường bán ~X"
8. stat_cogs_mean_dow_month

# C.2 Std by month (Volatility)
9. stat_rev_std_month           # "Tháng 12 biến động ±Y"
10. stat_cogs_std_month

# C.3 Median by day (Payday Effect)
11. stat_rev_median_day         # "Ngày 28 payday → revenue cao"
12. stat_cogs_median_day

# C.4 YoY Growth by month (Inflation Normalization) ⭐
13. stat_rev_yoy_growth_month   # "Tháng 12 tăng +20% YoY"
14. stat_cogs_yoy_growth_month
```

**Implementation:**
```python
# Pre-compute (Training phase)
train = pd.read_csv('sales.csv')
stat_rev_mean_dow_month = train.groupby(
    ['day_of_week', 'month']
)['Revenue'].mean()

# Usage (Test phase)
test_date = pd.Timestamp('2023-11-11')
dow = test_date.dayofweek  # 5 (Saturday)
month = test_date.month     # 11

# Lookup - no need for historical values!
feature = stat_rev_mean_dow_month.loc[(5, 11)]
```

**Tại sao XUẤT SẮC:**
- ✅ Zero leakage (tính từ train only)
- ✅ Always available (lookup table)
- ✅ General pattern (10 years wisdom)
- ✅ YoY growth = Auto inflation normalization

---

### 🎯 CHIẾN LƯỢC "KIỀNG BA CHÂN":

```
CHÂN 1: Near-term (lag_364)
  → Recent trends
  → High accuracy
  → BUT error accumulation risk

CHÂN 2: Safe Anchor (lag_728)
  → Always safe (from train)
  → Raw + Smoothed = Anomaly detection
  → Fallback anchor

CHÂN 3: Statistics (Patterns)
  → General rules from 10 years
  → Lookup tables
  → Zero leakage, always available
```

**Model tự quyết định dùng chân nào:**
- Đầu test → Chân 1 (364) từ train
- Giữa test → Chân 1 predictions + Chân 3 smooth
- Cuối test (nếu Chân 1 sai nhiều) → Chân 2 + 3 anchor

---

### Implementation Code:

```python
# Pre-compute statistics (train only)
statistics = {
    'rev_mean_dow_month': train.groupby(['day_of_week', 'month'])['Revenue'].mean(),
    'cogs_mean_dow_month': train.groupby(['day_of_week', 'month'])['COGS'].mean(),
    'rev_std_month': train.groupby('month')['Revenue'].std(),
    'cogs_std_month': train.groupby('month')['COGS'].std(),
    'rev_median_day': train.groupby('day')['Revenue'].median(),
    'cogs_median_day': train.groupby('day')['COGS'].median(),
    'rev_yoy_growth_month': calc_yoy_growth(train, 'Revenue'),
    'cogs_yoy_growth_month': calc_yoy_growth(train, 'COGS'),
}

# Feature creation
def create_lag_features(date, historical_data, stats):
    # A. Near-term (364)
    rev_lag_364 = historical_data.loc[date - 364, 'Revenue']
    
    # B. Safe anchor (728)
    rev_lag_728 = historical_data.loc[date - 728, 'Revenue']
    rev_roll_mean_28_lag_728 = historical_data.loc[
        date-728-14 : date-728+14, 'Revenue'
    ].mean()
    
    # C. Statistics (lookup)
    dow = date.dayofweek
    month = date.month
    day = date.day
    
    stat_rev_mean_dow_month = stats['rev_mean_dow_month'].loc[(dow, month)]
    stat_rev_yoy_growth_month = stats['rev_yoy_growth_month'].loc[month]
    
    return features
```

---

### Expected Top Features (by importance):

1. `rev_lag_364` - Recent seasonality
2. `stat_rev_mean_dow_month` - Pattern lookup
3. `rev_lag_728` - Safe anchor
4. `stat_rev_yoy_growth_month` - Growth normalization
5. `rev_roll_mean_28_lag_728` - Baseline level

---

## 🌊 NHÓM 6: FOURIER FEATURES (2 features)

**Mục đích:** Global Stabilizer - Làm mượt ranh giới năm (Dec 31 → Jan 1)

**Triết lý thiết kế:**
> Không dùng để bắt seasonality (đã có `month` và `stat_rev_mean_dow_month`)  
> Chỉ dùng để **SMOOTH boundary conditions** qua giao năm

---

### Features:

```python
1. sin_annual_1             # Sine wave với period = 365.25 ngày
2. cos_annual_1             # Cosine wave với period = 365.25 ngày
```

---

### Công thức:

```python
import numpy as np

day_of_year = date.dayofyear

# Annual cycle (harmonic 1 only)
sin_annual_1 = np.sin(2 * np.pi * 1 * day_of_year / 365.25)
cos_annual_1 = np.cos(2 * np.pi * 1 * day_of_year / 365.25)
```

**Giá trị ví dụ:**
```
Date        day_of_year  sin_annual_1   cos_annual_1
2022-01-01      1           0.017          0.999
2022-06-15    166          -0.017          0.999
2022-12-31    365          -0.000          1.000
2023-01-01      1           0.017          0.999
```

---

### Tại sao CHỈ cần 2 features (không cần 6):

#### **❌ BỎ ĐI: sin/cos_annual_2 (Harmonic 2)**

**Lý do:**
```
Harmonic 2 = Bắt sub-patterns trong năm (2 peaks)
→ ĐÃ CÓ stat_rev_mean_dow_month làm tốt hơn!
→ Redundant + Overfitting risk
```

**So sánh:**
```python
# Fourier harmonic 2 bắt:
"Tháng 3 và tháng 9 có pattern tương tự"

# Statistics bắt chính xác hơn:
stat_rev_mean_dow_month[(6, 3)]  # Thứ 7 tháng 3
stat_rev_mean_dow_month[(6, 9)]  # Thứ 7 tháng 9
→ Actual data from 10 years, không phải smooth wave!
```

---

#### **❌ BỎ ĐI: sin/cos_quarterly_1**

**Lý do:**
```
Quarterly pattern = Đã có trong NHÓM 1 (quarter)
→ Discrete quarter feature đủ rồi
→ Không cần smooth version
```

---

### Vai trò THỰC SỰ của sin/cos_annual_1:

#### **1. Boundary Smoother (Use case chính)**

**Vấn đề với discrete month:**
```python
Date         month  Issue
2022-12-31   12     
2023-01-01   1      ← JUMP! Model nghĩ 2 ngày này xa nhau

# LightGBM tree split:
if month <= 6:  # Spring/Summer
    ...
else:           # Fall/Winter
    ...
# → Dec 31 và Jan 1 rơi vào 2 nhánh khác nhau!
```

**Giải pháp với Fourier:**
```python
Date         sin_annual_1   cos_annual_1
2022-12-31   -0.000         1.000
2023-01-01    0.017         0.999

# Smooth! Model biết 2 ngày này gần nhau
# cos_annual_1: 1.000 → 0.999 (chỉ thay đổi 0.1%)
```

---

#### **2. Continuous Representation**

**Benefit:**
```
Month (discrete):  1, 2, 3, ..., 12, 1, 2, ...
Fourier (continuous): Smooth wave không có jump

→ Model học được: "Tháng 1 GẦN tháng 12"
   (theo chu kỳ, không phải số học)
```

**Ví dụ LightGBM học:**
```python
# Decision tree CÓ THỂ split:
if cos_annual_1 > 0.9:  # Near year-end OR year-start
    revenue_boost = +20%  # Year-end shopping + Tết prep
```

→ Bắt được pattern: "Cuối năm và đầu năm" là 1 period liên tục

---

#### **3. Không thay thế month, mà COMPLEMENT**

| Feature | Role | Capture |
|---------|------|---------|
| `month` | **Discrete seasonality** | "Tháng 12 khác tháng 1" |
| `sin/cos_annual_1` | **Continuous cycle** | "Tháng 12 ≈ Tháng 1" (boundary) |

**Kết hợp:**
```python
# Model học được CẢ HAI:
if month == 12:
    baseline = 10000  # Discrete: Tháng 12 cao
    
    # Continuous: Điều chỉnh theo vị trí trong tháng
    if cos_annual_1 > 0.95:  # Cuối tháng 12
        baseline *= 1.2  # Gần Tết prep
```

---

### Tại sao KHÔNG cần nhiều harmonics:

**Nguyên tắc:**
> Harmonic càng cao = Capture patterns càng nhỏ  
> Patterns nhỏ → Dễ overfit  
> Statistics (NHÓM 5) làm tốt hơn!

**Trade-off:**

| Harmonics | Captures | Risk |
|-----------|----------|------|
| **1 (our choice)** | **Annual cycle + boundary** | **Low overfitting** |
| 2 | Sub-annual patterns (2 peaks) | Medium - Redundant với stats |
| 3+ | Very specific patterns | High - Overfitting to noise |

---

### Expected Feature Importance:

**Trong top 40 features:**
- `sin_annual_1`: Rank ~25-30 (moderate)
- `cos_annual_1`: Rank ~30-35 (moderate)

**Tại sao không cao:**
- Vai trò chính = Smoothing, không phải main signal
- Main seasonality đã được bắt bởi: `month`, `stat_rev_mean_dow_month`, `rev_lag_364`

**Nhưng vẫn CẦN:**
- Giúp model học smooth transitions
- Giảm discontinuity artifacts
- Minimal overhead (chỉ 2 features)

---

### Implementation Note:

```python
def create_fourier_features(date):
    """
    Tạo 2 Fourier features cho annual cycle
    """
    day_of_year = date.dayofyear
    
    # Period = 365.25 (account for leap years)
    period = 365.25
    
    sin_annual_1 = np.sin(2 * np.pi * day_of_year / period)
    cos_annual_1 = np.cos(2 * np.pi * day_of_year / period)
    
    return {
        'sin_annual_1': sin_annual_1,
        'cos_annual_1': cos_annual_1
    }
```

**Luôn dùng 365.25 (không phải 365):**
- Account cho leap years
- Tránh drift qua nhiều năm

---

### Key Takeaway:

✅ **Minimalist:** Chỉ 2 features thay vì 6  
✅ **Focused:** Vai trò rõ ràng = Boundary smoother  
✅ **Complement:** Không thay thế month, mà bổ sung  
✅ **Low risk:** Harmonic 1 only → Không overfit

---

## 🦠 NHÓM 7: COVID-19 OUTLIERS (3 features)

**Mục đích:** Biến điều hướng để model không bị overfit vào dữ liệu dị thường 2021

**Triết lý thiết kế:**
> Không chỉ đánh dấu outliers  
> Mà là **"guide rails"** giúp model biết khi nào NÊN/KHÔNG NÊN tin lag features

---

### Features:

```python
1. is_pre_lockdown          # Binary (2 tuần trước lockdown)
2. is_lockdown              # Binary (Delta wave lockdown)
3. is_post_lockdown         # Binary (1 tháng recovery)
```

---

### Timeline chính xác - Delta Wave HCM 2021:

```
Phase               Dates                        Duration    Impact
────────────────────────────────────────────────────────────────────
Pre-lockdown        09/05/2021 → 22/05/2021     14 ngày     SPIKE (+30-50%)
                    (Panic buying)

Lockdown            23/05/2021 → 01/10/2021     132 ngày    PLUMMET (-70-80%)
                    (Shops closed)

Post-lockdown       02/10/2021 → 01/11/2021     30 ngày     RECOVERY (+20-40%)
                    (Pent-up demand)
```

---

### Implementation:

```python
import pandas as pd

def create_covid_features(date):
    # Pre-lockdown (panic buying period)
    is_pre_lockdown = int(
        pd.Timestamp('2021-05-09') <= date <= pd.Timestamp('2021-05-22')
    )
    
    # Lockdown (Delta wave)
    is_lockdown = int(
        pd.Timestamp('2021-05-23') <= date <= pd.Timestamp('2021-10-01')
    )
    
    # Post-lockdown (recovery period)
    is_post_lockdown = int(
        pd.Timestamp('2021-10-02') <= date <= pd.Timestamp('2021-11-01')
    )
    
    return {
        'is_pre_lockdown': is_pre_lockdown,
        'is_lockdown': is_lockdown,
        'is_post_lockdown': is_post_lockdown
    }
```

---

## 🎯 VAI TRÒ THEN CHỐT: "Điều hướng" Lag Features

### **Vấn đề nếu KHÔNG có COVID flags:**

```python
# 2021-06-15 (đang lockdown): Revenue = 5,000 (cực thấp)

# Khi predict 2022-06-15:
rev_lag_364 = 5,000  # Lấy từ 2021 (contaminated!)
→ Prediction = 6,000 (quá THẤP!)

# Actual: 15,000
→ ERROR = 60%!
```

---

### **Với COVID flags, model học được:**

**LightGBM tự học interaction rules:**

```python
# Rule 1: Discount contaminated lags
if is_lockdown == 1:
    weight_lag_364 = 0.1  # Almost ignore
    weight_lag_728 = 0.8  # Trust 2020 data (clean)

# Rule 2: Identify contaminated lag dates
elif rev_lag_364 < 8000:  # Suspiciously low
    # Likely from lockdown period
    weight_lag_364 = 0.3
    weight_lag_728 = 0.6  # Prefer clean anchor

# Rule 3: Recovery boost
elif is_post_lockdown == 1:
    prediction = base_prediction * 1.3  # Pent-up demand

# Rule 4: Pre-lockdown spike (temporary)
elif is_pre_lockdown == 1:
    prediction = base_prediction * 1.4
    mark_as_anomaly = True
```

---

## 📊 Expected Patterns by Phase:

### **1. Pre-lockdown (Panic Buying)**
- Dates: 09/05 → 22/05/2021
- Revenue: +30-50% vs normal
- Model learns: "Temporary spike, not trend"

### **2. Lockdown (Shops Closed)**
- Dates: 23/05 → 01/10/2021
- Revenue: -70-80% vs normal
- Model learns: "Extreme outlier, trust lag_728 (2020)"

### **3. Post-lockdown (Pent-up Demand)**
- Dates: 02/10 → 01/11/2021
- Revenue: +20-40% vs pre-lockdown
- Model learns: "Recovery boost, normalize gradually"

---

## 🎯 Tại sao cần 3 FLAGS riêng:

```
Pre:  Spike (temporary, ignore for trend)
Lock: Plummet (extreme outlier, use lag_728)
Post: Recovery (boost adjustment)

→ 3 strategies khác nhau → 3 flags riêng
```

---

## ✅ Expected Feature Importance:

- `is_lockdown`: Rank ~15-20 ⭐ (HIGH - critical cho accuracy)
- `is_post_lockdown`: Rank ~25-30
- `is_pre_lockdown`: Rank ~30-35

**Key Takeaway:**
> COVID flags = "Guide rails" giúp model handle contaminated lags  
> Without them: 2022 predictions sai ~60%  
> With them: Error giảm xuống ~10%

---

## 📊 SUMMARY TABLE

| Nhóm | Core Features | Total |
|------|--------------|-------|
| Calendar & Liquidity | 6 | **6** |
| Tết | 5 | **5** |
| Fashion Windows | 5 | **5** |
| E-commerce Sales | 5 | **5** |
| Hybrid Memory Engine | 14 | **14** |
| Fourier | 2 | **2** |
| COVID | 3 | **3** |
| **TỔNG** | **40** | **40** |

### Độ ưu tiên:

🔴 **CRITICAL (26 features):** Không thể thiếu
- Calendar & Liquidity (6)
- Tết (5)
- Fashion Windows (5)
- E-commerce Sales (5)
- Core lags: rev/cogs_lag_364, rev/cogs_lag_728 (4)
- Fourier (1): cos_annual_1

🟡 **IMPORTANT (12 features):** Nên có
- Lag smoothed: rev/cogs_roll_mean_28_lag_728 (2)
- Core statistics: stat_*_mean_dow_month (2)
- Statistics extras: std_month, median_day, yoy_growth_month (6)
- COVID (3)
- Fourier (1): sin_annual_1

🟢 **OPTIONAL (2 features):** Nice to have
- stat_*_std_month variants (có thể bỏ nếu cần giảm features)

---

## 🎯 VALIDATION CHECKLIST

### ✅ Before Training:

- [ ] All features created from `Date` column only
- [ ] Lag features use `shift(1)` before rolling
- [ ] Tet dates hardcoded correctly (2012-2024)
- [ ] Double day sales = 12 dates per year
- [ ] Black Friday calculated correctly
- [ ] Ghost month mapped to Lunar calendar
- [ ] COVID dates: 23/05/2021 - 01/10/2021

### ✅ Feature Quality:

- [ ] No NaN in calendar features
- [ ] NaN in lags only for first N days (expected)
- [ ] Fourier features range: [-1, 1]
- [ ] All binary features: {0, 1}
- [ ] No data leakage (test features use train data only)

### ✅ Business Logic:

- [ ] Pre-Tet 14d has highest revenue spike
- [ ] Ghost month shows revenue drop
- [ ] 11/11, 12/12 higher than other double days
- [ ] Weekend revenue > weekday revenue
- [ ] COVID lockdown period shows clear anomaly

---

## 💻 NEXT STEPS

1. **Feature Engineering:** Implement 55 features in `src/features.py`
2. **Validation:** 5-fold Time Series Cross-Validation
3. **Feature Selection:** Check feature importance (SHAP)
4. **Model Training:** LightGBM + Prophet + N-BEATS ensemble
5. **Submission:** Predict test period (2023-2024)

---

**Last updated:** 2026-04-26  
**Total features:** 40  
**Estimated implementation time:** 2-2.5 days

---

## 🎯 KEY INNOVATIONS

### **Features mới sáng tạo:**

1. **`dist_to_payday`** ⭐ 
   - Bắt gradient tăng dần của ví tiền
   - Revenue relationship: `~ -0.5 * dist_to_payday`
   - Kết hợp với `is_payday_window` → bắt cả step function VÀ gradient

2. **`days_to_tet`** ⭐
   - Countdown đến Tết: -30 → +15
   - Bắt gradient trong mỗi Tet phase
   - Kết hợp với 4 binary flags → comprehensive coverage

3. **`shopping_festival_score`** ⭐⭐⭐ 
   - Ordinal 0-3: Phân cấp độ "khủng" của sale
   - Model học hierarchy: 11/11 (3) > 9/9 (2) > 1/1 (1)
   - Reflect reality: 11/11 lớn hơn 2/2 gấp 10 lần

4. **`days_to_next_big_sale`** ⭐⭐⭐
   - Countdown đến sale lớn tiếp theo
   - Bắt tâm lý "nhịn mua" chờ sale
   - Giải thích pre-sale revenue slump

5. **HYBRID MEMORY ENGINE** ⭐⭐⭐⭐⭐
   - Kiềng 3 chân: Near-term (364) + Safe (728) + Statistics
   - Raw + Smoothed = Anomaly detection
   - YoY Growth = Auto inflation normalization
   - Lookup tables = Zero leakage, always available

6. **FOURIER MINIMALIST** ⭐⭐
   - Chỉ 2 features (sin/cos annual_1)
   - Vai trò: Boundary smoother, KHÔNG phải seasonality
   - Giảm từ 6→2 features, loại bỏ redundancy

7. **COVID as Guide Rails** ⭐⭐⭐⭐
   - Không chỉ mark outliers
   - Điều hướng model khi nào trust/discount lag features
   - Prevent overfitting to 2021 contaminated data

8. **Shopping windows** (not event days)
   - `is_gift_peak`: 7→2 ngày TRƯỚC lễ
   - E-commerce insight: Order trước để kịp nhận hàng

9. **Ghost month**
   - Feature văn hóa Việt unique
   - Expected impact: -15-20% revenue

---

## 📈 EXPECTED TOP 15 FEATURES (By Importance)

Dựa trên business logic và experience:

1. 🥇 **rev_lag_364** - Cùng thứ năm ngoái (seasonality gần nhất)
2. 🥈 **stat_rev_mean_dow_month** - Pattern lookup từ 10 năm
3. 🥉 **month** - Annual seasonality
4. **shopping_festival_score** - Phân cấp sale
5. **days_to_tet** - Gradient Tết
6. **is_tet_peak** - Peak window Tết
7. **rev_lag_728** - Safe anchor 2 năm
8. **day_of_week** - Weekly cycle
9. **days_to_next_big_sale** - Pre-sale gradient
10. **stat_rev_yoy_growth_month** - Inflation normalization
11. **dist_to_payday** - Gradient ví tiền
12. **cos_annual_1** - Boundary smoother
13. **is_payday_window** - Spike cuối tháng
14. **rev_roll_mean_28_lag_728** - Baseline 2 năm trước
15. **is_lockdown** - COVID guide rail

**Key improvements trong FINAL version:**
- ✅ HYBRID MEMORY ENGINE = Kiềng 3 chân (364, 728, stats)
- ✅ Statistical features = Lookup tables (zero leakage)
- ✅ YoY growth = Auto inflation normalization
- ✅ Raw + Smoothed = Anomaly detection
- ✅ FOURIER MINIMALIST = Chỉ 2 features (boundary smoother)
- ✅ COVID as GUIDE RAILS = Điều hướng lag features
- ✅ **40 features: Tối ưu, focused & comprehensive**
- ✅ Mỗi nhóm có cả binary flags VÀ gradient features

1. 🥇 **rev_lag_365** - Cùng ngày năm ngoái (seasonality mạnh nhất)
2. 🥈 **month** - Annual seasonality  
3. 🥉 **shopping_festival_score** - Phân cấp sale (NEW!)
4. **days_to_tet** - Gradient Tết
5. **is_tet_peak** - Peak window Tết
6. **day_of_week** - Weekly cycle
7. **days_to_next_big_sale** - Pre-sale gradient (NEW!)
8. **dist_to_payday** - Gradient ví tiền
9. **sin_annual_1** - Smooth seasonality
10. **is_payday_window** - Spike cuối tháng
11. **rev_roll_mean_30** - Smoothed trend
12. **is_year_end_festive** - Party season
13. **is_ghost_month** - Văn hóa VN
14. **dist_to_nearest_holiday** - Universal holiday gradient
15. **is_black_friday** - Western mega sale

**Key improvements trong version này:**
- ✅ `shopping_festival_score` + `days_to_next_big_sale` = comprehensive e-commerce sale coverage
- ✅ Shopping windows thay vì event days = bắt đúng e-commerce behavior
- ✅ 50 features: Balanced (không quá nhiều, không thiếu)
- ✅ Mỗi nhóm có cả binary flags VÀ gradient features
