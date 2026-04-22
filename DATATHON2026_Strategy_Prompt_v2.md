# 🏆 DATATHON 2026 — Round 1 Master Strategy Prompt (v2.0)

## Nhiệm vụ của bạn (Model đang đọc prompt này)

Bạn là **Senior Lead Data Scientist với 15 năm kinh nghiệm trong retail và e-commerce Đông Nam Á**, đang tư vấn chiến lược toàn diện cho một team dự thi **DATATHON 2026 — The Gridbreaker** của VinTelligence / VinUniversity.

**Khi review prompt này, hãy đánh giá theo 7 trục:**
1. Tính chặt chẽ của lý luận MCQ (có câu nào reasoning yếu?)
2. Độ phủ của EDA narrative (có insight quan trọng nào bị bỏ sót?)
3. Rủi ro data leakage trong feature engineering (có lỗ hổng ẩn nào?)
4. Sự phù hợp của model stack với team profile
5. Tính khả thi của timeline với >5 ngày làm việc
6. Điểm mạnh/yếu của cấu trúc báo cáo NeurIPS
7. Rủi ro kỹ thuật nào có thể khiến team mất điểm oan?

---

## 👥 Team Profile (đã được calibrate)

| Thuộc tính | Giá trị |
|---|---|
| Quy mô | 2–3 người |
| Background | Thiên về DS/ML |
| Tech stack | Python (pandas, sklearn), SQL, PyTorch (beginner) |
| TS Experience | **Có kinh nghiệm ensemble & stacking** |
| Thời gian còn lại | **> 5 ngày** |
| Mục tiêu | **Top 3 — vào Chung kết bằng mọi giá** |
| Data status | Đã có data, chưa explore |

> **Implication quan trọng:** Team này có nền tảng đủ mạnh để thực thi pipeline phức tạp. Với > 5 ngày, không cần shortcut — mọi quyết định phải hướng tới **điểm tối đa tuyệt đối**, không phải "đủ nộp bài".

---

## 📋 Bối cảnh cuộc thi

### Phân bổ điểm — Hiểu đúng để phân bổ effort đúng

| Phần | Nội dung | Điểm | Trọng số | Effort đề xuất |
|------|----------|------|----------|----------------|
| 1 | Trắc nghiệm MCQ (10 câu) | 20đ | 20% | **10%** thời gian |
| 2 | EDA + Visualization + Business Insights | 60đ | **60%** | **55%** thời gian |
| 3 | Sales Forecasting (Kaggle) | 20đ | 20% | **35%** thời gian |

> ⚠️ **Nghịch lý thường thấy ở DS team:** Người giỏi ML thường dành 70% thời gian cho model và 10% cho EDA. Đây là **chiến lược thua điểm** với rubric này. Với team có ensemble experience, model tốt đến 90 điểm trong 2 ngày — nhưng EDA xuất sắc cần 3–4 ngày đầu tư thực sự.

### Dataset — Fashion E-commerce Việt Nam (2012–2022)

**15 file CSV, 4 lớp:**

```
MASTER (tham chiếu)          TRANSACTION (giao dịch)
├── products.csv             ├── orders.csv
├── customers.csv            ├── order_items.csv
├── promotions.csv           ├── payments.csv
└── geography.csv            ├── shipments.csv
                             ├── returns.csv
ANALYTICAL                   └── reviews.csv
├── sales.csv (train)
└── sample_submission.csv    OPERATIONAL
                             ├── inventory.csv
                             ├── inventory_enhanced.csv
                             └── web_traffic.csv
```

**Forecasting split:**
- Train: `sales.csv` — 04/07/2012 → 31/12/2022 (~3,833 ngày)
- Test: `sales_test.csv` — 01/01/2023 → 01/07/2024 (~548 ngày)

---

## ⚡ Day 0 — Data Audit (Làm ngay khi có data, trước khi explore)

Đây là bước **nhiều team bỏ qua và hối hận**. Dành 2–3 giờ đầu tiên để audit toàn bộ data quality. Kết quả audit sẽ ảnh hưởng mọi quyết định sau.

```python
import pandas as pd
import numpy as np

# Load tất cả tables
tables = {
    'products':    pd.read_csv('products.csv'),
    'customers':   pd.read_csv('customers.csv', parse_dates=['signup_date']),
    'promotions':  pd.read_csv('promotions.csv', parse_dates=['start_date','end_date']),
    'geography':   pd.read_csv('geography.csv'),
    'orders':      pd.read_csv('orders.csv', parse_dates=['order_date']),
    'order_items': pd.read_csv('order_items.csv'),
    'payments':    pd.read_csv('payments.csv'),
    'shipments':   pd.read_csv('shipments.csv', parse_dates=['ship_date','delivery_date']),
    'returns':     pd.read_csv('returns.csv', parse_dates=['return_date']),
    'reviews':     pd.read_csv('reviews.csv', parse_dates=['review_date']),
    'sales':       pd.read_csv('sales.csv', parse_dates=['Date']),
    'inventory':   pd.read_csv('inventory.csv', parse_dates=['snapshot_date']),
    'web_traffic': pd.read_csv('web_traffic.csv', parse_dates=['date']),
}

# Audit report
for name, df in tables.items():
    print(f"\n{'='*50}")
    print(f"📁 {name}: {df.shape[0]:,} rows × {df.shape[1]} cols")
    print(f"   Date range: {df.select_dtypes('datetime').apply(lambda c: f'{c.min()} → {c.max()}').to_dict()}")
    print(f"   Nulls: {df.isnull().sum()[df.isnull().sum()>0].to_dict()}")
    print(f"   Duplicates: {df.duplicated().sum()}")

# Kiểm tra referential integrity
print("\n🔗 FK Integrity Checks:")
orphan_orders = ~tables['order_items']['order_id'].isin(tables['orders']['order_id'])
print(f"   order_items orphan orders: {orphan_orders.sum()}")

orphan_products = ~tables['order_items']['product_id'].isin(tables['products']['product_id'])
print(f"   order_items orphan products: {orphan_products.sum()}")

# Verify sales continuity
sales = tables['sales'].set_index('Date').sort_index()
date_range = pd.date_range(sales.index.min(), sales.index.max())
missing_dates = date_range.difference(sales.index)
print(f"\n📅 Sales missing dates: {len(missing_dates)} days")
if len(missing_dates) > 0:
    print(f"   First few: {missing_dates[:5].tolist()}")

# Verify constraint: cogs < price
violation = tables['products'][tables['products']['cogs'] >= tables['products']['price']]
print(f"\n💰 products cogs >= price violations: {len(violation)}")
```

**Câu hỏi cần trả lời sau audit:**
- [ ] Sales có ngày nào bị missing không? (Nếu có → cần impute trước)
- [ ] Có outlier revenue ngày nào bất thường không? (spike bất thường → investigate)
- [ ] web_traffic có tất cả ngày trong training period không?
- [ ] inventory snapshot có monthly đủ từ 2012 không?
- [ ] FK joins có clean không hay có orphan records?

---

## Phần 1 — Câu hỏi Trắc nghiệm (20đ)

### Đáp án đề xuất + Code verify

> **Nguyên tắc:** Câu nào có thể verify bằng code trong < 5 phút → BẮT BUỘC verify. Không dùng intuition khi có data.

```python
# ── VERIFY SCRIPT — Chạy toàn bộ trong 1 notebook cell ──────────────────

orders      = pd.read_csv('orders.csv', parse_dates=['order_date'])
order_items = pd.read_csv('order_items.csv')
products    = pd.read_csv('products.csv')
customers   = pd.read_csv('customers.csv')
returns     = pd.read_csv('returns.csv')
web_traffic = pd.read_csv('web_traffic.csv')
payments    = pd.read_csv('payments.csv')
geography   = pd.read_csv('geography.csv')
sales       = pd.read_csv('sales.csv', parse_dates=['Date'])

# Q1 — Inter-order gap median
orders_s = orders.sort_values(['customer_id','order_date'])
orders_s['prev'] = orders_s.groupby('customer_id')['order_date'].shift(1)
orders_s['gap_days'] = (orders_s['order_date'] - orders_s['prev']).dt.days
multi = orders_s[orders_s['customer_id'].isin(
    orders.groupby('customer_id').size()[lambda x: x > 1].index
)]
q1_ans = multi['gap_days'].dropna().median()
print(f"Q1 Median inter-order gap: {q1_ans:.0f} days")

# Q2 — Gross margin by segment
products['margin'] = (products['price'] - products['cogs']) / products['price']
q2_ans = products.groupby('segment')['margin'].mean().idxmax()
print(f"Q2 Highest avg gross margin segment: {q2_ans}")

# Q3 — Return reason trong Streetwear
returns_full = returns.merge(products[['product_id','category']], on='product_id')
streetwear_returns = returns_full[returns_full['category'].str.lower() == 'streetwear']
q3_ans = streetwear_returns['return_reason'].value_counts().idxmax()
print(f"Q3 Top return reason in Streetwear: {q3_ans}")

# Q4 — Traffic source với bounce rate thấp nhất
q4_ans = web_traffic.groupby('traffic_source')['bounce_rate'].mean().idxmin()
print(f"Q4 Lowest avg bounce rate source: {q4_ans}")

# Q5 — % order_items có promo
q5_ans = order_items['promo_id'].notna().mean() * 100
print(f"Q5 % items with promo: {q5_ans:.1f}%")

# Q6 — Age group cao nhất avg orders per customer
cust_orders = orders.groupby('customer_id').size().reset_index(name='n_orders')
cust_full = customers.merge(cust_orders, on='customer_id', how='left').fillna({'n_orders': 0})
cust_valid = cust_full[cust_full['age_group'].notna()]
q6_ans = cust_valid.groupby('age_group')['n_orders'].mean().idxmax()
print(f"Q6 Age group with highest avg orders: {q6_ans}")

# Q7 — Region doanh thu cao nhất (cần join với geography qua zip của orders)
# Sales là aggregate nên không join trực tiếp — check xem geography có liên kết với sales không
# Thực ra sales.csv là aggregate daily — không có region. Đây là bẫy câu hỏi.
# Cần join: orders → geography → region → aggregate revenue từ order_items
order_rev = order_items.merge(orders[['order_id','zip','order_date']], on='order_id')
order_rev['revenue_line'] = order_rev['quantity'] * order_rev['unit_price'] - order_rev['discount_amount']
order_geo = order_rev.merge(geography[['zip','region']], on='zip')
q7_ans = order_geo.groupby('region')['revenue_line'].sum()
print(f"Q7 Revenue by region:\n{q7_ans.sort_values(ascending=False)}")

# Q8 — Payment method phổ biến nhất ở cancelled orders
cancelled = orders[orders['order_status'] == 'cancelled']
q8_ans = cancelled['payment_method'].value_counts().idxmax()
print(f"Q8 Most common payment in cancelled orders: {q8_ans}")

# Q9 — Size có return rate cao nhất
items_with_size = order_items.merge(products[['product_id','size']], on='product_id')
returns_with_size = returns.merge(products[['product_id','size']], on='product_id')

total_by_size = items_with_size[items_with_size['size'].isin(['S','M','L','XL'])]\
    .groupby('size').size()
returned_by_size = returns_with_size[returns_with_size['size'].isin(['S','M','L','XL'])]\
    .groupby('size').size()
return_rate_by_size = (returned_by_size / total_by_size).sort_values(ascending=False)
q9_ans = return_rate_by_size.idxmax()
print(f"Q9 Size with highest return rate: {q9_ans}")
print(return_rate_by_size)

# Q10 — Installment plan với avg payment value cao nhất
q10_ans = payments.groupby('installments')['payment_value'].mean().idxmax()
print(f"Q10 Installment plan with highest avg payment: {q10_ans} kỳ")
```

### Đáp án tham chiếu (trước khi chạy code)

| Câu | Đáp án dự đoán | Confidence | Note |
|-----|---------------|-----------|------|
| Q1 | **B) 90 ngày** | ★★★★☆ | Fashion SEA quarterly cycle |
| Q2 | **A) Premium** | ★★★★★ | Thiết kế pricing intrinsic |
| Q3 | **B) wrong_size** | ★★★★★ | #1 fashion return reason toàn cầu |
| Q4 | **C) email_campaign** | ★★★★★ | Warm audience, highest intent |
| Q5 | **C) 39%** | ★★★☆☆ | **PHẢI verify bằng code** |
| Q6 | **B) 25–34** | ★★★★☆ | Digital native + income sweet spot |
| Q7 | **Verify bằng code** | — | Không thể đoán dataset synthetic |
| Q8 | **B) cod** | ★★★★★ | COD = no-commitment, SEA pain point |
| Q9 | **D) XL** | ★★★★☆ | Extreme size fit variance cao nhất |
| Q10 | **D) 12 kỳ** | ★★★★★ | Selection bias: 12-kỳ → hàng đắt |

> 📌 **Sau khi chạy code, update bảng này với ground truth. Với team có SQL skill, có thể viết verify queries bằng DuckDB để cross-check.**

---

## Phần 2 — EDA & Visualization (60đ) — CHIẾN TRƯỜNG CHÍNH

### Framework tư duy tổng quát

**Không làm chart rời rạc. Xây dựng một "Business Intelligence Report" hoàn chỉnh.**

Rubric phân tầng bắt buộc:
```
Descriptive  → What happened?         Aggregation, summary stats, distribution
Diagnostic   → Why did it happen?     Correlation, segmentation, anomaly detection
Predictive   → What will happen?      Trend extrapolation, seasonality, leading indicators
Prescriptive → What should we do?     Actionable + quantified + trade-off aware
```

Mỗi chương phải đạt **cả 4 tầng**. Câu Prescriptive phải có con số cụ thể, không được chung chung.

---

### Kiến trúc 4 chương (upgrade từ 3 chương — tận dụng > 5 ngày)

---

#### 📖 Chương 1: "Revenue Pulse" — Temporal Health & Seasonality

**Mục đích:** Establish ground truth về temporal patterns — nền tảng cho mọi phân tích sau.

**Chart 1.1 — Revenue Trend với Regime Detection**
```python
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from statsmodels.tsa.seasonal import STL

sales = pd.read_csv('sales.csv', parse_dates=['Date']).set_index('Date').sort_index()

# STL decompose với period=365
stl = STL(sales['Revenue'], period=365, seasonal=13, robust=True)
result = stl.fit()

fig, axes = plt.subplots(4, 1, figsize=(14, 12), sharex=True)
axes[0].plot(sales['Revenue'], alpha=0.6, color='steelblue', linewidth=0.8)
axes[0].plot(result.trend, color='red', linewidth=2)
axes[0].set_title('Observed Revenue + Trend', fontweight='bold')

axes[1].plot(result.seasonal, color='green', linewidth=0.8)
axes[1].set_title('Seasonal Component (Annual)', fontweight='bold')

axes[2].plot(result.resid, color='orange', linewidth=0.8, alpha=0.7)
axes[2].axhline(0, color='black', linewidth=0.5)
axes[2].set_title('Residual — Identify Anomalies Here', fontweight='bold')

# Mark COVID period
axes[0].axvspan('2020-03-01', '2021-06-01', alpha=0.1, color='red', label='COVID Period')

plt.tight_layout()
```

**Prescriptive từ Chart 1.1:**
> *Dựa trên trend coefficient và seasonality amplitude, xác định: (1) Growth rate trung bình YoY là X%; (2) COVID tạo revenue loss ước tính Y tỷ VND trong N tháng; (3) Recovery về pre-COVID level mất M tháng — implication cho business continuity planning.*

**Chart 1.2 — Seasonality Heatmap (Month × Year)**
```python
import seaborn as sns

sales['month'] = sales.index.month
sales['year'] = sales.index.year
monthly = sales.groupby(['year','month'])['Revenue'].sum().reset_index()

# Normalize mỗi năm để loại bỏ trend effect, chỉ nhìn seasonality
monthly['revenue_norm'] = monthly.groupby('year')['Revenue'].transform(
    lambda x: (x - x.mean()) / x.std()
)
pivot = monthly.pivot(index='year', columns='month', values='revenue_norm')

fig, ax = plt.subplots(figsize=(14, 6))
sns.heatmap(pivot, cmap='RdYlGn', center=0, annot=True, fmt='.2f',
            xticklabels=['Jan','Feb','Mar','Apr','May','Jun',
                        'Jul','Aug','Sep','Oct','Nov','Dec'],
            ax=ax)
ax.set_title('Revenue Seasonality Heatmap (Z-score normalized per year)\n'
             'Green = above annual average, Red = below', fontweight='bold')
```

**Insight kỳ vọng:** Tết (Jan/Feb), 11.11 và 12.12 sẽ hiện rõ màu xanh. Q3 (Jul–Sep) thường đỏ với fashion VN. Prescriptive: timing inventory và marketing budget theo seasonal index.

**Chart 1.3 — Day-of-Week Revenue Pattern**
```python
# Weekly seasonality — ít team nghĩ đến nhưng quan trọng cho daily forecasting
sales['dow'] = sales.index.day_name()
dow_order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
dow_avg = sales.groupby('dow')['Revenue'].mean().reindex(dow_order)

# Bar chart với weekend highlight
colors = ['coral' if d in ['Saturday','Sunday'] else 'steelblue' for d in dow_order]
```

---

#### 📖 Chương 2: "Customer Intelligence" — Profitability & Lifetime Value

**Mục đích:** Tìm ra ai thực sự tạo ra value — sau khi trừ discounts và refunds.

**Key join pipeline — tính TRUE net revenue per customer:**
```python
# True CLV = gross revenue - discounts - refunds
items_agg = order_items.groupby('order_id').agg(
    gross_revenue = ('unit_price', lambda x: (x * order_items.loc[x.index, 'quantity']).sum()),
    total_discount = ('discount_amount', 'sum')
).reset_index()

refunds_agg = returns.groupby('order_id')['refund_amount'].sum().reset_index()

orders_enriched = (orders
    .merge(items_agg, on='order_id', how='left')
    .merge(refunds_agg, on='order_id', how='left')
    .merge(customers[['customer_id','age_group','gender',
                       'acquisition_channel','signup_date']], on='customer_id')
)
orders_enriched['refund_amount'] = orders_enriched['refund_amount'].fillna(0)
orders_enriched['net_revenue'] = (
    orders_enriched['gross_revenue'] 
    - orders_enriched['total_discount'] 
    - orders_enriched['refund_amount']
)

# CLV per customer
clv = orders_enriched.groupby('customer_id').agg(
    total_net_revenue = ('net_revenue', 'sum'),
    n_orders = ('order_id', 'count'),
    avg_order_value = ('net_revenue', 'mean'),
    first_order = ('order_date', 'min'),
    last_order = ('order_date', 'max')
)
clv['customer_lifespan_days'] = (clv['last_order'] - clv['first_order']).dt.days
```

**Chart 2.1 — RFM Segmentation**
```python
from datetime import datetime

snapshot_date = pd.Timestamp('2022-12-31')
rfm = orders_enriched.groupby('customer_id').agg(
    recency   = ('order_date', lambda x: (snapshot_date - x.max()).days),
    frequency = ('order_id', 'count'),
    monetary  = ('net_revenue', 'sum')
).reset_index()

# Quintile scoring 1–5
for col in ['recency','frequency','monetary']:
    rfm[f'{col}_score'] = pd.qcut(
        rfm[col] * (-1 if col == 'recency' else 1),
        q=5, labels=[1,2,3,4,5], duplicates='drop'
    ).astype(int)

rfm['rfm_segment'] = rfm.apply(lambda r: 
    'Champions'  if r.recency_score >= 4 and r.frequency_score >= 4 else
    'Loyal'      if r.frequency_score >= 3 else
    'At Risk'    if r.recency_score <= 2 and r.frequency_score >= 3 else
    'Lost'       if r.recency_score == 1 else 'Others', axis=1
)

# Bubble chart: Recency vs Frequency, size = Monetary
fig, ax = plt.subplots(figsize=(12, 8))
colors_map = {'Champions':'gold','Loyal':'steelblue','At Risk':'orange','Lost':'red','Others':'gray'}
for seg, grp in rfm.groupby('rfm_segment'):
    ax.scatter(grp['recency'], grp['frequency'],
               s=grp['monetary']/grp['monetary'].max()*500,
               alpha=0.4, label=seg, color=colors_map.get(seg,'gray'))
ax.set_xlabel('Recency (days since last purchase) — Lower is better')
ax.set_ylabel('Frequency (number of orders)')
ax.set_title('RFM Customer Segmentation\n(Bubble size = Net Revenue contribution)', fontweight='bold')
ax.legend()
```

**Chart 2.2 — Cohort Retention Heatmap**
```python
from operator import attrgetter

orders_enriched['cohort_month'] = orders_enriched.groupby('customer_id')['order_date']\
    .transform('min').dt.to_period('M')
orders_enriched['order_period'] = orders_enriched['order_date'].dt.to_period('M')
orders_enriched['period_number'] = (
    orders_enriched['order_period'] - orders_enriched['cohort_month']
).apply(attrgetter('n'))

cohort_data = orders_enriched.groupby(['cohort_month','period_number'])['customer_id']\
    .nunique().reset_index()
cohort_pivot = cohort_data.pivot(index='cohort_month', columns='period_number', values='customer_id')
cohort_pct = cohort_pivot.div(cohort_pivot[0], axis=0) * 100

# Plot
fig, ax = plt.subplots(figsize=(18, 10))
sns.heatmap(cohort_pct.iloc[:, :24],  # 24 tháng đầu
            annot=True, fmt='.0f', cmap='YlOrRd_r',
            vmin=0, vmax=100, ax=ax)
ax.set_title('Customer Cohort Retention Rate (%)\nMonth 0 = First Purchase', fontweight='bold')
```

**Chart 2.3 — Acquisition Channel ROI**
```python
# Net CLV theo acquisition channel — đây là Prescriptive mạnh nhất
channel_clv = (orders_enriched
    .merge(clv[['customer_id','total_net_revenue']], on='customer_id')
    .groupby(['customer_id','acquisition_channel'])['total_net_revenue']
    .first().reset_index()
    .groupby('acquisition_channel')['total_net_revenue']
    .agg(['mean','count','sum'])
)
# Prescriptive: "Nên rebalance marketing budget như thế nào?"
```

---

#### 📖 Chương 3: "Promotion Analytics" — True Lift vs Discount Cost

**Đây là chương tạo điểm sáng tạo cao nhất — kết hợp 4 bảng ít team nghĩ tới.**

**Core question:** Promotion nào thực sự tăng demand, promotion nào chỉ discount cho người đã mua anyway?

```python
# Join: order_items + promotions + orders + web_traffic
promo_analysis = order_items.merge(
    orders[['order_id','order_date']], on='order_id'
).merge(
    promotions[['promo_id','promo_type','discount_value','stackable_flag',
                'promo_name','applicable_category']], on='promo_id', how='left'
)

# Tính effective discount rate thực sự
promo_analysis['gross_line_revenue'] = (
    promo_analysis['quantity'] * promo_analysis['unit_price'] + 
    promo_analysis['discount_amount']
)
promo_analysis['effective_discount_pct'] = (
    promo_analysis['discount_amount'] / promo_analysis['gross_line_revenue']
).clip(0, 1)

# So sánh return rate: promo items vs non-promo items
returns_flag = returns[['order_id','product_id']].drop_duplicates()
returns_flag['was_returned'] = 1
promo_analysis = promo_analysis.merge(returns_flag, 
    on=['order_id','product_id'], how='left')
promo_analysis['was_returned'] = promo_analysis['was_returned'].fillna(0)

# Kết quả: items mua trong promo có return rate cao hơn không?
return_comparison = promo_analysis.groupby(promo_analysis['promo_id'].notna())\
    ['was_returned'].mean()
print("Return rate - No promo:", return_comparison[False])
print("Return rate - With promo:", return_comparison[True])
```

**Chart 3.1 — Promotion Lift Analysis (Event Study)**
```python
# Với mỗi promotion campaign: so sánh daily revenue 2 tuần trước, trong, và sau campaign
for promo_id in top_promos:
    promo_row = promotions[promotions['promo_id'] == promo_id].iloc[0]
    start, end = promo_row['start_date'], promo_row['end_date']
    
    window_before = sales.loc[start - pd.Timedelta(days=14) : start - pd.Timedelta(days=1), 'Revenue']
    window_during = sales.loc[start : end, 'Revenue']
    window_after  = sales.loc[end + pd.Timedelta(days=1) : end + pd.Timedelta(days=14), 'Revenue']
    
    # Lift = (during_mean - before_mean) / before_mean
    lift = (window_during.mean() - window_before.mean()) / window_before.mean()
    print(f"{promo_row['promo_name']}: lift = {lift*100:.1f}%")
```

**Prescriptive từ Chương 3:**
> *"Campaign X có revenue lift +Y% nhưng return rate tăng Z% → net margin impact chỉ còn W%. Khuyến nghị: tập trung budget vào campaign có stackable_flag=0 và applicable_category cụ thể — đây là campaigns có lift thực sự cao nhất với chi phí thấp nhất."*

---

#### 📖 Chương 4: "Operations Intelligence" — Inventory Leakage & Web Signal

**Core question:** Chúng ta đã mất bao nhiêu tiền vì hết hàng? Web traffic báo hiệu revenue ngày mai như thế nào?

**Chart 4.1 — Revenue Lost to Stockout (Quantified)**
```python
inventory = pd.read_csv('inventory.csv', parse_dates=['snapshot_date'])
products_price = products.set_index('product_id')[['price','cogs','category','segment']]

# Estimate daily revenue rate per product per month
inventory['avg_daily_units_sold'] = (
    inventory['units_sold'] / 
    (inventory['snapshot_date'].dt.daysinmonth - inventory['stockout_days'].clip(upper=28))
)

# Revenue lost = avg_daily_rate × stockout_days × price
inv_enriched = inventory.merge(
    products_price, left_on='product_id', right_index=True, how='left'
)
inv_enriched['estimated_revenue_lost'] = (
    inv_enriched['avg_daily_units_sold'] * 
    inv_enriched['stockout_days'] * 
    inv_enriched['price']
)

stockout_by_category = inv_enriched.groupby('category')['estimated_revenue_lost'].sum()
total_lost = stockout_by_category.sum()
print(f"Total estimated revenue lost to stockout: {total_lost:,.0f} VND")

# Visualize: Horizontal bar chart sorted by loss
stockout_by_category.sort_values().plot(kind='barh', figsize=(10,6), color='coral')
plt.title(f'Estimated Revenue Lost to Stockout by Category\nTotal: {total_lost/1e9:.1f} Billion VND',
          fontweight='bold')
```

**Chart 4.2 — Web Traffic as Leading Indicator**
```python
from scipy import signal

# Aggregate web traffic daily
web_daily = pd.read_csv('web_traffic.csv', parse_dates=['date'])
web_agg = web_daily.groupby('date').agg(
    sessions=('sessions', 'sum'),
    conversion_rate=('conversion_rate', 'mean')
).reindex(pd.date_range(sales.index.min(), sales.index.max())).ffill()

# Cross-correlation: tìm optimal lag
common_idx = sales.index.intersection(web_agg.index)
rev_series = sales.loc[common_idx, 'Revenue']
web_series = web_agg.loc[common_idx, 'sessions']

# Normalize
rev_norm = (rev_series - rev_series.mean()) / rev_series.std()
web_norm = (web_series - web_series.mean()) / web_series.std()

correlation = signal.correlate(rev_norm.fillna(0), web_norm.fillna(0), mode='full')
lags = signal.correlation_lags(len(rev_norm), len(web_norm), mode='full')
lag_df = pd.DataFrame({'lag': lags, 'correlation': correlation})

# Plot: peak correlation ở lag=? 
# Nếu peak ở lag=-2 → web traffic leads revenue by 2 days → dùng làm forecast feature!
lag_df[lag_df['lag'].between(-30,30)].plot(x='lag', y='correlation', figsize=(12,4))
plt.axvline(0, color='red', linestyle='--')
plt.title('Cross-correlation: Web Sessions → Revenue\n(Negative lag = web leads revenue)')
```

**Chart 4.3 — Overstock vs Stockout Risk Matrix**
```python
# Portfolio positioning: mỗi product ở quadrant nào?
latest_inv = inventory[inventory['snapshot_date'] == inventory['snapshot_date'].max()]

fig, ax = plt.subplots(figsize=(12, 8))
scatter = ax.scatter(
    latest_inv['days_of_supply'],
    latest_inv['sell_through_rate'],
    c=latest_inv['stockout_flag'],
    cmap='RdYlGn', alpha=0.6, s=50
)

# Quadrant lines
ax.axvline(30, color='gray', linestyle='--', alpha=0.5)   # 30 days supply threshold
ax.axhline(0.7, color='gray', linestyle='--', alpha=0.5)   # 70% sell-through threshold

# Quadrant labels
ax.text(5, 0.85, 'STOCKOUT RISK\n⚠️ Expedite reorder', fontsize=9, color='red',
        bbox=dict(boxstyle='round', facecolor='lightyellow'))
ax.text(60, 0.85, 'HEALTHY\n✅ Maintain', fontsize=9, color='green')
ax.text(5, 0.3, 'DEAD STOCK\n💀 Markdown needed', fontsize=9, color='darkred')
ax.text(60, 0.3, 'OVERSTOCK\n📦 Reduce reorder', fontsize=9, color='orange')

ax.set_xlabel('Days of Supply Remaining')
ax.set_ylabel('Sell-Through Rate')
ax.set_title('Inventory Health Matrix — Latest Snapshot\n(Color: Red = stockout occurred)',
             fontweight='bold')
```

---

## Phần 3 — Sales Forecasting (20đ)

### Bức tranh toàn cảnh về bài toán

- **Horizon:** 548 ngày (18 tháng) — đây là long-horizon forecast, không phải short-term
- **Granularity:** Daily — có strong weekly + annual seasonality
- **Gap:** Train kết thúc 31/12/2022, test bắt đầu 01/01/2023 — không có gap (liên tục)
- **Structural break:** COVID 2020 trong training data — cần xử lý cẩn thận

### Architecture quyết định — 3-model stack

Team có ensemble & stacking experience → không có lý do gì để chỉ dùng 1 model.

```
Layer 1 (Base Models):
├── LightGBM    — Tabular features, captures non-linear interactions
├── Prophet     — Handles holiday effects, changepoints tự động
└── N-BEATS     — Neural, học seasonality phức tạp không cần feature engineering

Layer 2 (Meta-learner):
└── Ridge Regression — Blend predictions từ 3 base models
    (Ridge thay vì linear regression để tránh overfitting)
```

**Tại sao N-BEATS thay vì LSTM/Transformer?**
- N-BEATS được thiết kế riêng cho univariate time series
- Không cần feature engineering phức tạp — học seasonality end-to-end
- Faster training hơn Transformer, ít hyperparameter hơn LSTM
- PyTorch implementation có sẵn qua `neuralforecast` library
- Team có PyTorch beginner experience — N-BEATS đủ accessible

### Step 1: Feature Engineering (Core work — 4–6 giờ)

```python
import pandas as pd
import numpy as np
from pathlib import Path

def build_feature_matrix(sales_df, web_df, inventory_df, promo_df, 
                          target_dates=None):
    """
    Xây dựng feature matrix cho forecasting.
    target_dates: DatetimeIndex của các ngày cần predict (test set)
    """
    if target_dates is None:
        idx = sales_df.index
    else:
        idx = target_dates
    
    df = pd.DataFrame(index=idx)
    
    # ════════════════════════════════════════════════════════════
    # BLOCK 1: CALENDAR FEATURES
    # ════════════════════════════════════════════════════════════
    df['day_of_week']   = idx.dayofweek       # 0=Mon
    df['day_of_month']  = idx.day
    df['week_of_year']  = idx.isocalendar().week.astype(int)
    df['month']         = idx.month
    df['quarter']       = idx.quarter
    df['year']          = idx.year
    df['is_weekend']    = (idx.dayofweek >= 5).astype(int)
    df['is_month_start'] = idx.is_month_start.astype(int)
    df['is_month_end']  = idx.is_month_end.astype(int)
    df['is_quarter_end'] = idx.is_quarter_end.astype(int)
    df['is_year_end']   = ((idx.month == 12) & (idx.day >= 25)).astype(int)
    
    # ════════════════════════════════════════════════════════════
    # BLOCK 2: VIETNAMESE CULTURAL CALENDAR
    # ════════════════════════════════════════════════════════════
    # Tet Nguyen Dan — ngày đầu năm Âm lịch (approx Gregorian dates)
    tet_dates = pd.to_datetime([
        '2013-02-10','2014-01-31','2015-02-19','2016-02-08',
        '2017-01-28','2018-02-16','2019-02-05','2020-01-25',
        '2021-02-12','2022-02-01','2023-01-22','2024-02-10'
    ])
    
    # Distance features tới/sau Tết
    def days_to_nearest_tet(date):
        diffs = [(date - t).days for t in tet_dates]
        return min(diffs, key=abs)
    
    df['days_from_tet'] = [days_to_nearest_tet(d) for d in idx]
    
    # Pre-Tet shopping windows (demand spike)
    for days_before in [45, 30, 21, 14, 7, 3]:
        df[f'pre_tet_{days_before}d'] = 0
        for tet in tet_dates:
            mask = ((idx >= tet - pd.Timedelta(days=days_before)) & 
                    (idx < tet))
            df.loc[mask, f'pre_tet_{days_before}d'] = 1
    
    # Post-Tet slump
    for days_after in [7, 14, 21]:
        df[f'post_tet_{days_after}d'] = 0
        for tet in tet_dates:
            mask = ((idx > tet) & 
                    (idx <= tet + pd.Timedelta(days=days_after)))
            df.loc[mask, f'post_tet_{days_after}d'] = 1
    
    # Shopping festivals
    df['is_830']  = ((idx.month == 8) & (idx.day == 30)).astype(int)
    df['is_99']   = ((idx.month == 9) & (idx.day == 9)).astype(int)
    df['is_1010'] = ((idx.month == 10) & (idx.day == 10)).astype(int)
    df['is_1111'] = ((idx.month == 11) & (idx.day == 11)).astype(int)
    df['is_1212'] = ((idx.month == 12) & (idx.day == 12)).astype(int)
    
    # Sale season windows (1 tuần quanh các ngày sale)
    for col in ['is_1111', 'is_1212']:
        base_dates = idx[df[col] == 1]
        df[f'{col}_window_7d'] = 0
        for d in base_dates:
            mask = (idx >= d - pd.Timedelta(days=3)) & (idx <= d + pd.Timedelta(days=3))
            df.loc[mask, f'{col}_window_7d'] = 1
    
    # ════════════════════════════════════════════════════════════
    # BLOCK 3: LAG FEATURES FROM REVENUE
    # ════════════════════════════════════════════════════════════
    if sales_df is not None:
        rev = sales_df['Revenue'].reindex(
            pd.date_range(sales_df.index.min(), idx.max())
        ).ffill()
        
        # Short-term lags
        for lag in [1, 2, 3, 4, 5, 6, 7]:
            df[f'rev_lag_{lag}'] = rev.shift(lag).reindex(idx).values
        
        # Medium-term lags
        for lag in [14, 21, 28, 30, 60, 90]:
            df[f'rev_lag_{lag}'] = rev.shift(lag).reindex(idx).values
        
        # Long-term: same day last year (critical for annual seasonality)
        for lag in [364, 365, 366]:
            df[f'rev_lag_{lag}'] = rev.shift(lag).reindex(idx).values
        
        # Rolling statistics (always shift(1) để tránh leakage)
        rev_s1 = rev.shift(1)
        for window in [7, 14, 30, 60, 90, 180]:
            df[f'rev_roll_mean_{window}'] = rev_s1.rolling(window).mean().reindex(idx).values
            df[f'rev_roll_std_{window}']  = rev_s1.rolling(window).std().reindex(idx).values
        
        # Momentum features
        df['rev_mom_7_30']   = (df['rev_roll_mean_7'] / df['rev_roll_mean_30'].replace(0, np.nan))
        df['rev_mom_30_90']  = (df['rev_roll_mean_30'] / df['rev_roll_mean_90'].replace(0, np.nan))
        df['rev_yoy_ratio']  = (df['rev_lag_7'] / df['rev_lag_372'].replace(0, np.nan))  # 365+7
    
    # ════════════════════════════════════════════════════════════
    # BLOCK 4: WEB TRAFFIC (Leading Indicator)
    # ════════════════════════════════════════════════════════════
    if web_df is not None:
        # Aggregate by date (multiple rows per date per source)
        web_daily = web_df.groupby('date').agg(
            sessions         = ('sessions', 'sum'),
            unique_visitors  = ('unique_visitors', 'sum'),
            page_views       = ('page_views', 'sum'),
            avg_bounce_rate  = ('bounce_rate', 'mean'),
            avg_conversion   = ('conversion_rate', 'mean'),
            avg_duration     = ('avg_session_duration_sec', 'mean')
        )
        web_daily = web_daily.reindex(pd.date_range(web_df['date'].min(), idx.max()))
        
        # Lag 1 day (web traffic là leading indicator — dùng lag=1 để predict ngày hôm sau)
        for col in web_daily.columns:
            for lag in [1, 2, 7]:
                df[f'web_{col}_lag{lag}'] = web_daily[col].shift(lag).reindex(idx).values
        
        # Rolling web features
        df['web_sessions_roll7_lag1'] = web_daily['sessions'].shift(1).rolling(7).mean().reindex(idx).values
    
    # ════════════════════════════════════════════════════════════
    # BLOCK 5: PROMOTION SCHEDULE
    # ════════════════════════════════════════════════════════════
    if promo_df is not None:
        promo_df = promo_df.copy()
        promo_df['start_date'] = pd.to_datetime(promo_df['start_date'])
        promo_df['end_date']   = pd.to_datetime(promo_df['end_date'])
        
        n_active      = []
        has_stackable = []
        
        for date in idx:
            active = promo_df[
                (promo_df['start_date'] <= date) & 
                (promo_df['end_date']   >= date)
            ]
            n_active.append(len(active))
            has_stackable.append(int(active['stackable_flag'].any() if len(active) > 0 else 0))
        
        df['n_active_promos']    = n_active
        df['has_stackable_promo'] = has_stackable
    
    # ════════════════════════════════════════════════════════════
    # BLOCK 6: INVENTORY SIGNALS (Monthly → Daily via ffill)
    # ════════════════════════════════════════════════════════════
    if inventory_df is not None:
        inv_monthly = inventory_df.groupby('snapshot_date').agg(
            avg_fill_rate     = ('fill_rate', 'mean'),
            pct_stockout      = ('stockout_flag', 'mean'),
            avg_sell_through  = ('sell_through_rate', 'mean'),
            avg_days_supply   = ('days_of_supply', 'mean'),
            pct_reorder       = ('reorder_flag', 'mean')
        )
        # Forward fill: tháng này apply cho toàn bộ ngày trong tháng tiếp theo
        inv_daily = inv_monthly.resample('D').ffill().shift(30)  # 30-day lag
        inv_daily = inv_daily.reindex(pd.date_range(inv_daily.index.min(), idx.max())).ffill()
        
        for col in inv_daily.columns:
            df[f'inv_{col}'] = inv_daily[col].reindex(idx).values
    
    return df


# Build features
X_train = build_feature_matrix(
    sales_df=sales, web_df=web_traffic, 
    inventory_df=inventory, promo_df=promotions,
    target_dates=sales.index
)
y_train = sales['Revenue']
```

### Step 2: Time-Aware Cross-Validation

```python
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# KHÔNG dùng random CV với time series — đây là lỗi nghiêm trọng
tscv = TimeSeriesSplit(
    n_splits=5,
    gap=30,          # 30-day gap giữa train và val để avoid look-ahead từ rolling features
    test_size=365    # Mỗi fold val = 1 năm
)

# Defensive assertion: verify không có leakage
for fold, (train_idx, val_idx) in enumerate(tscv.split(X_train)):
    X_tr, X_val = X_train.iloc[train_idx], X_train.iloc[val_idx]
    y_tr, y_val = y_train.iloc[train_idx], y_train.iloc[val_idx]
    
    # Fail loud nếu có leakage
    assert X_tr.index.max() < X_val.index.min(), \
        f"LEAKAGE DETECTED at fold {fold}! Train max: {X_tr.index.max()}, Val min: {X_val.index.min()}"
    
    print(f"Fold {fold+1}: Train {X_tr.index.min().date()} → {X_tr.index.max().date()} | "
          f"Val {X_val.index.min().date()} → {X_val.index.max().date()}")
```

### Step 3: Model Training

```python
import lightgbm as lgb
from prophet import Prophet

# ── MODEL 1: LightGBM ────────────────────────────────────────────────────
lgbm_params = {
    'objective': 'regression_l1',  # L1 = MAE objective — consistent với metric
    'metric': ['mae', 'rmse'],
    'learning_rate': 0.03,          # Thấp hơn → cần nhiều trees hơn nhưng stable hơn
    'num_leaves': 127,
    'min_child_samples': 30,
    'feature_fraction': 0.7,
    'bagging_fraction': 0.8,
    'bagging_freq': 5,
    'reg_alpha': 0.05,
    'reg_lambda': 0.1,
    'n_estimators': 5000,
    'early_stopping_rounds': 200,
    'verbose': -1,
    'random_state': 42,
    'n_jobs': -1
}

# ── MODEL 2: Prophet ────────────────────────────────────────────────────
def train_prophet(train_df):
    """train_df: DataFrame với columns [ds, y]"""
    m = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        seasonality_mode='multiplicative',   # Fashion → spike-heavy → multiplicative
        changepoint_prior_scale=0.05,        # Conservative vs COVID break
        seasonality_prior_scale=15.0,        # Allow strong seasonality
        holidays_prior_scale=20.0,
        interval_width=0.95,
        random_state=42
    )
    # Vietnamese holidays
    m.add_country_holidays(country_name='VN')
    
    # Custom Tet seasonality (Prophet's VN holiday không handle Tet tốt)
    m.add_seasonality(name='tet_season', period=354.37, fourier_order=5)
    
    m.fit(train_df)
    return m

# ── MODEL 3: N-BEATS (PyTorch via neuralforecast) ───────────────────────
# Cài: pip install neuralforecast
from neuralforecast import NeuralForecast
from neuralforecast.models import NBEATS

nbeats_model = NeuralForecast(
    models=[
        NBEATS(
            h=548,                    # Forecast horizon = test set length
            input_size=2*365,         # 2 năm lịch sử làm input
            stack_types=['trend', 'seasonality'],
            n_blocks=[3, 3],
            mlp_units=[[512, 512], [512, 512]],
            n_harmonics=2,
            n_polynomials=2,
            dropout_prob_theta=0.0,
            learning_rate=1e-3,
            max_steps=500,
            batch_size=32,
            random_seed=42,
            # Loss consistent với MAE metric
            loss=MAE()
        )
    ],
    freq='D'
)

# N-BEATS chỉ cần time series, không cần external features
nbeats_train_df = sales.reset_index().rename(columns={'Date':'ds','Revenue':'y'})
nbeats_train_df['unique_id'] = 'total_revenue'
```

### Step 4: Stacking Ensemble

```python
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

# Thu thập OOF (Out-of-Fold) predictions từ CV
oof_lgbm    = np.zeros(len(X_train))
oof_prophet = np.zeros(len(X_train))
# N-BEATS OOF phức tạp hơn — dùng holdout cuối nếu cần đơn giản hoá

for fold, (train_idx, val_idx) in enumerate(tscv.split(X_train)):
    # LightGBM OOF
    lgb_model = lgb.LGBMRegressor(**lgbm_params)
    lgb_model.fit(X_train.iloc[train_idx], y_train.iloc[train_idx],
                  eval_set=[(X_train.iloc[val_idx], y_train.iloc[val_idx])])
    oof_lgbm[val_idx] = lgb_model.predict(X_train.iloc[val_idx])
    
    # Prophet OOF
    prophet_train = pd.DataFrame({
        'ds': X_train.iloc[train_idx].index,
        'y': y_train.iloc[train_idx].values
    })
    prophet_model = train_prophet(prophet_train)
    future = pd.DataFrame({'ds': X_train.iloc[val_idx].index})
    prophet_preds = prophet_model.predict(future)['yhat'].values
    oof_prophet[val_idx] = np.clip(prophet_preds, 0, None)

# Stack: dùng OOF predictions làm features cho meta-learner
# Chỉ trên phần val (không phải full train để tránh overfitting)
val_start_idx = tscv.split(X_train).__next__()[1][0]  # First val index

meta_features = np.column_stack([
    oof_lgbm[val_start_idx:],
    oof_prophet[val_start_idx:],
    # Thêm N-BEATS OOF nếu đã train
])
meta_target = y_train.values[val_start_idx:]

# Ridge meta-learner
scaler = StandardScaler()
meta_features_scaled = scaler.fit_transform(meta_features)
meta_learner = Ridge(alpha=1.0)
meta_learner.fit(meta_features_scaled, meta_target)

print("Stack weights:", meta_learner.coef_)
# Kỳ vọng: LightGBM weight cao hơn vì xử lý external features tốt hơn
```

### Step 5: SHAP Analysis (Bắt buộc cho báo cáo)

```python
import shap

# Train final LightGBM trên toàn bộ train set
final_lgbm = lgb.LGBMRegressor(**lgbm_params)
final_lgbm.fit(X_train.fillna(X_train.median()), y_train)

# SHAP
explainer = shap.TreeExplainer(final_lgbm)
# Dùng sample để tránh OOM
sample_idx = np.random.choice(len(X_train), size=min(2000, len(X_train)), replace=False)
X_sample = X_train.fillna(X_train.median()).iloc[sample_idx]
shap_values = explainer.shap_values(X_sample)

# Plot 1: Global importance
plt.figure(figsize=(12, 8))
shap.summary_plot(shap_values, X_sample, max_display=25,
                  title="SHAP Feature Importance — Revenue Forecasting Model")

# Plot 2: Beeswarm (feature impact direction)
shap.summary_plot(shap_values, X_sample, plot_type='dot', max_display=20)

# Plot 3: Dependence plots cho top features
for feat in ['rev_lag_365', 'days_from_tet', 'web_sessions_lag1', 'month']:
    shap.dependence_plot(feat, shap_values, X_sample, alpha=0.3)

# Save feature importance DataFrame cho báo cáo
importance_df = pd.DataFrame({
    'feature': X_train.columns,
    'mean_abs_shap': np.abs(shap_values).mean(axis=0)
}).sort_values('mean_abs_shap', ascending=False)
importance_df.to_csv('shap_feature_importance.csv', index=False)
print(importance_df.head(20))
```

**Template translate SHAP sang business language:**

| SHAP Feature | Business Translation |
|---|---|
| `rev_lag_365` rank #1 | "Seasonal memory: doanh thu hôm nay phụ thuộc nhất vào cùng ngày năm ngoái → annual pattern cực ổn định, brand có seasonal predictability cao" |
| `days_from_tet` rank #2 | "Tết effect: khoảng cách tới Tết giải thích X% variance của model → nên start inventory buildup 45 ngày trước Tết" |
| `web_sessions_lag1` rank #3 | "Web traffic hôm nay là leading indicator của revenue ngày mai → monitor daily sessions như early warning system" |
| `pre_tet_14d` positive SHAP | "2 tuần trước Tết = peak demand window → tập trung stockout prevention trong window này" |

### Step 6: Final Submission

```python
# Load test date range từ sample submission
sample_sub = pd.read_csv('sample_submission.csv', parse_dates=['Date'])
test_dates = pd.DatetimeIndex(sample_sub['Date'])

# Build test features (sử dụng toàn bộ training data làm lag reference)
all_dates_with_test = pd.date_range(sales.index.min(), test_dates.max())
full_sales_index = pd.DataFrame(index=all_dates_with_test)

X_test = build_feature_matrix(
    sales_df=sales,           # Training revenue cho lag features
    web_df=web_traffic,
    inventory_df=inventory,
    promo_df=promotions,
    target_dates=test_dates   # Chỉ predict test dates
)

# LightGBM predictions
lgbm_test_pred = final_lgbm.predict(X_test.fillna(X_test.median()))

# Prophet predictions
prophet_full = train_prophet(
    pd.DataFrame({'ds': sales.index, 'y': sales['Revenue'].values})
)
future_df = pd.DataFrame({'ds': test_dates})
prophet_test_pred = np.clip(
    prophet_full.predict(future_df)['yhat'].values, 0, None
)

# N-BEATS predictions
# (train trên full data, predict với h=548)

# Stack
test_meta = np.column_stack([lgbm_test_pred, prophet_test_pred])
test_meta_scaled = scaler.transform(test_meta)
final_revenue_pred = meta_learner.predict(test_meta_scaled)
final_revenue_pred = np.clip(final_revenue_pred, 0, None)

# COGS: predict riêng hoặc dùng training margin ratio
# Option A: Predict COGS riêng với cùng pipeline (tốt hơn)
# Option B: final_cogs = final_revenue * (sales['COGS']/sales['Revenue']).median()
cogs_margin = (sales['COGS'] / sales['Revenue']).rolling(90).mean().iloc[-1]
final_cogs_pred = np.clip(final_revenue_pred * cogs_margin, 0, None)

# Tạo submission
submission = pd.DataFrame({
    'Date': test_dates,
    'Revenue': final_revenue_pred,
    'COGS': final_cogs_pred
})

# Validation checks
assert len(submission) == len(sample_sub), f"Row mismatch: {len(submission)} vs {len(sample_sub)}"
assert (submission['Revenue'] >= 0).all(), "Negative revenue found!"
assert (submission['COGS'] >= 0).all(), "Negative COGS found!"
assert list(submission.columns) == ['Date', 'Revenue', 'COGS'], "Column order wrong!"

# Verify row order matches sample
assert (submission['Date'].values == sample_sub['Date'].values).all(), "Date order mismatch!"

submission.to_csv('submission.csv', index=False)
print(f"✅ submission.csv saved: {len(submission)} rows")
print(submission.describe())
```

---

## 📝 Cấu trúc Báo cáo NeurIPS (≤ 4 trang)

```
§1. Introduction (0.25 trang)
    • Business context: fashion e-commerce VN 2012–2022
    • Contributions: novel EDA insights + ensemble forecasting approach
    • Brief overview of findings

§2. EDA & Business Intelligence (1.75 trang — ĐẦU TƯ NHIỀU NHẤT)
    2.1 Revenue Temporal Analysis (Tet effect, seasonality, COVID impact)
    2.2 Customer Segmentation & Lifetime Value (RFM, cohort, channel ROI)
    2.3 Promotion Effectiveness (lift analysis, return rate trade-off)
    2.4 Operations Intelligence (stockout revenue loss, inventory matrix)
    
    ┌─────────────────────────────────────────────────────────────────┐
    │ PRESCRIPTIVE RECOMMENDATIONS BOX (nổi bật, có số liệu cụ thể) │
    │ 1. Tăng inventory buffer X% trước 45 ngày Tết                  │
    │ 2. Rebalance marketing: giảm COD campaigns, tăng email_campaign │
    │ 3. Markdown Y danh mục đang trong quadrant dead stock          │
    │ 4. Estimated Z tỷ VND revenue recoverable từ stockout reduction│
    └─────────────────────────────────────────────────────────────────┘

§3. Forecasting Methodology (1.5 trang)
    3.1 Feature Engineering Rationale (tại sao mỗi block feature quan trọng)
    3.2 Three-Model Architecture & Stacking Protocol
    3.3 Time-Aware Cross-Validation Design (diagram visual)
    3.4 Results: CV performance table + Kaggle leaderboard score
    3.5 SHAP Analysis: Top 10 features với business interpretation
    3.6 Data Leakage Prevention Measures

§4. Conclusion (0.25 trang)
    • Key business insights summary
    • Model performance + limitations
    • Future work: real-time retraining, external macro features

References (không tính trang)

Appendix (không tính trang):
    • Full feature list (80+ features)
    • Additional charts
    • GitHub: [repo link] — contains all notebooks, README với reproduce guide
```

---

## ⏱️ Timeline Chi tiết (> 5 ngày — Full effort)

| Ngày | Task | Hours | Owner |
|------|------|-------|-------|
| **Day 1** | Data Audit + MCQ verification | 4h | All |
| **Day 1** | Basic EDA: shapes, distributions, date coverage | 4h | All |
| **Day 2** | Chương 1: Revenue seasonality + Tet decompose | 6h | DS1 |
| **Day 2** | Chương 2: Customer CLV, RFM, cohort | 6h | DS2 |
| **Day 3** | Chương 3: Promotion lift analysis | 4h | DS1 |
| **Day 3** | Chương 4: Inventory stockout + web traffic lag | 4h | DS2 |
| **Day 3** | Feature engineering framework | 4h | DS1+DS2 |
| **Day 4** | LightGBM + Prophet training + TimeSeriesSplit CV | 6h | DS1 |
| **Day 4** | N-BEATS training | 4h | DS2 |
| **Day 5** | Stacking ensemble + hyperparameter tuning | 4h | DS1 |
| **Day 5** | SHAP analysis + business translation | 3h | DS2 |
| **Day 5** | First Kaggle submission + iterate | 3h | All |
| **Day 6** | Chart polish + report writing draft | 6h | All |
| **Day 6** | GitHub README + code cleanup | 2h | DS1 |
| **Day 7** | Report finalize + final submission check | 4h | All |
| **Day 7** | Buffer: iterate on Kaggle if leaderboard below top 3 | 4h | All |

**Phân bổ effort cuối:**
```
EDA + Visualization (Phần 2):  50% ████████████████████░░░░░░░░░░░░░░░░░░░░
Modeling + Kaggle (Phần 3):    35% ██████████████░░░░░░░░░░░░░░░░░░░░░░░░░░
MCQ + Report (Phần 1):         15% ██████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
```

---

## ⚠️ Risk Register — Những gì có thể sai

| Rủi ro | Khả năng | Impact | Mitigation |
|--------|----------|--------|-----------|
| Data leakage trong lag features | Cao | Bị loại toàn bộ Phần 3 | `assert train.index.max() < val.index.min()` ở mỗi fold |
| N-BEATS training timeout | Trung bình | Mất 1 model trong stack | Reduce `max_steps`, fallback sang XGBoost |
| Sales có missing dates | Trung bình | Feature lag bị lệch | Audit ngay Day 0, impute nếu cần |
| Kaggle submission sai format | Thấp | 0đ Phần 3 | Validate vs sample_submission trước khi nộp |
| Report > 4 trang | Trung bình | Bị trừ điểm | Track trang số khi viết, Appendix cho overflow |
| Prescriptive chung chung | Cao | Mất 8–10đ EDA | Mọi recommendation PHẢI có con số VND cụ thể |

---

## ✅ Checklist Nộp bài Cuối cùng

### Phần 1 — MCQ
- [ ] Đã chạy verify script và lưu output
- [ ] Đã điền form với đáp án đã verify

### Phần 2 — EDA
- [ ] 4 chương, mỗi chương có đủ 4 tầng phân tích
- [ ] Mỗi chart: tiêu đề, nhãn trục, đơn vị, chú thích màu
- [ ] Ít nhất 3 insight kết hợp 3+ bảng dữ liệu
- [ ] Mỗi Prescriptive recommendation có con số cụ thể (VND, %, ngày)
- [ ] Stockout revenue loss được quantify bằng số

### Phần 3 — Forecasting
- [ ] `assert train.index.max() < val.index.min()` pass mọi fold
- [ ] Revenue predictions ≥ 0 (clip thực hiện)
- [ ] `len(submission) == len(sample_submission)` ✓
- [ ] Row order giữ nguyên như sample ✓
- [ ] random_state=42 set ở mọi stochastic operation
- [ ] SHAP plots rendered + saved
- [ ] Code chạy end-to-end từ raw data → submission.csv

### GitHub & Report
- [ ] `README.md` có: cấu trúc folder, environment setup, reproduce command
- [ ] Repo public hoặc đã share với ban tổ chức
- [ ] PDF ≤ 4 trang (kiểm tra bằng `wc -l` hoặc PDF viewer)
- [ ] GitHub link embedded trong PDF
- [ ] Ảnh thẻ sinh viên tất cả thành viên
- [ ] Tick xác nhận có người đến Hà Nội 23/05/2026

---

## 🔍 Điểm để Flagship Model Review

Khi đưa prompt này cho model khác, yêu cầu đánh giá theo **7 trục** sau:

1. **MCQ reasoning:** Câu nào thiếu chặt chẽ? Đặc biệt Q5, Q6, Q7 — có thể predict không hay cần data hoàn toàn?
2. **EDA coverage:** Chương nào có gap lớn? Có insight quan trọng của fashion e-commerce VN bị bỏ sót?
3. **Leakage audit:** Trong feature engineering code, có lỗ hổng leakage nào không tường minh?
4. **Model suitability:** Với horizon 548 ngày và 10 năm training data, N-BEATS có phải best choice? TimeGPT, TiDE, hay Chronos có merit không?
5. **Report allocation:** Với 4 trang NeurIPS, phân bổ trang có optimal không? Phần nào nên compress/expand?
6. **Stacking design:** Ridge meta-learner có đủ không? Có nên thêm diversity bằng cách dùng multiple time horizons?
7. **Competitive edge:** Điều gì sẽ phân biệt bài này với các team khác cũng làm LightGBM + Prophet?

---

*Prompt v2.0 — Calibrated cho: Team 2–3 người, DS/ML background, Python+SQL, ensemble experience, mục tiêu Top 3*  
*DATATHON 2026 — The Gridbreaker, VinTelligence / VinUniversity*  
*Assumptions: > 5 ngày còn lại, đã có data chưa explore*
