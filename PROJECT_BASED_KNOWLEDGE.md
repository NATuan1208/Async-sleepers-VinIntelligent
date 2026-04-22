# PROJECT BASED KNOWLEDGE - DATATHON 2026 (GRIDBREAKER)

## 1) Muc tieu tai lieu
Tai lieu nay la bo nho du an de dam bao moi session moi deu lam viec dung huong, dung ky thuat, va tranh cac loi gay mat diem.

Nguyen tac su dung:
- Luon doc file nay truoc khi viet code hoac chay notebook.
- Neu co thay doi logic/chien luoc, cap nhat file nay ngay lap tuc.
- Moi quyet dinh quan trong phai co data evidence (SQL, metric, output).

## 2) Boi canh va pham vi du an
Bai thi gom 3 phase:
- Phase 1: Data Engine + Data Audit + MCQ solver (DuckDB, SQL, Python)
- Phase 2: EDA + Business storytelling (uu tien tac dong VND, khong chi phan tram)
- Phase 3: Forecasting 548 ngay (LightGBM + Prophet + N-BEATS, stacking bang Ridge)

Muc tieu tong the:
- Minh bach, tai lap duoc, co kiem chung.
- Bao cao ro logic kinh doanh va logic ky thuat.

## 3) Quy tac bat buoc phai tuan thu

### 3.1 Data architecture va hieu nang
- Khong load tat ca CSV vao Pandas cung luc.
- Su dung DuckDB + read_csv_auto de ingest va truy van SQL tren local warehouse.
- Moi bang CSV phai duoc map 1-1 vao bang DuckDB theo ten file.

### 3.2 Data quality va audit
- Bat buoc kiem tra:
  - Missing dates (sales)
  - Referential integrity (orphan records)
  - Business constraints (cogs < price)
  - Null/blank o cot trong yeu
  - Duplicate keys
- Kiem tra phai co output file ro rang (json/csv) de trinh bay voi giam khao.

### 3.3 Quy tac MCQ (khong duoc sai dinh nghia)
- Q5: Promotion ratio phai dung dieu kien:
  - promo_id IS NOT NULL OR promo_id_2 IS NOT NULL
- Q7: Revenue by region phai loai bo don that bai:
  - Toi thieu loai cancelled, returned
  - Neu can, mo rong them failed-like statuses (theo quy uoc team)
- Q8: Bat buoc cross-check payment_method giua orders va payments truoc khi tim mode.
- Q9: Return rate theo RECORD COUNTS (so dong), KHONG theo quantity sum.

### 3.4 Forecasting anti-leakage
- Tuyet doi khong dung short-term lag (lag_1, lag_7, ... ) cho horizon 548 ngay.
- Chi dung seasonal lag dai (vi du lag_365) + calendar/holiday/covariate.
- Bat buoc assert chong leakage trong time split:
  - train max date < val min date

### 3.5 Reproducibility va coding standards
- Luon set seed/random_state = 42 cho moi thao tac ngau nhien.
- Notebook phai tach ro:
  - Markdown cell: business context + logic
  - Python/SQL cell: code thuc thi
- Moi ket qua quan trong phai co truy van hoac code tai lap duoc.

## 4) Cac dieu can tranh (anti-patterns)
- Doan dap an MCQ theo cam tinh, khong co SQL backup.
- Blend model forecasting bang mean don gian.
- Bo qua cross-check giua cac bang co thong tin trung lap (vi du payment_method).
- Dung metric khong dung dinh nghia de bai (vi du Q9 dung quantity thay vi record count).
- Viet code khong co defensive checks (assert, null handling, divide-by-zero handling).

## 5) Definition of Done theo phase

### Phase 1 Done khi:
- Warehouse ingest thanh cong tat ca bang nguon.
- Audit summary co ket qua day du va co file output.
- MCQ Q1-Q10 co ket qua SQL + mapping A/B/C/D ro rang.
- Co artifact trinh bay cho giam khao:
  - Notebook MCQ
  - SQL script MCQ
  - Report tom tat

### Phase 2 Done khi:
- Moi chart tra loi duoc: What happened, Why, So what, Now what.
- Moi recommendation co impact dinh luong (VND, %, ngay).
- Co phan tich payment_method vs return_rate/cancellation cost theo business logic VN.

### Phase 3 Done khi:
- Co CV time-aware, khong leakage.
- Co OOF predictions cho meta learner Ridge.
- Submission format dung va pass sanity checks (khong am, dung so dong, dung thu tu ngay).

## 6) Session bootstrap cho lan lam viec moi
Khi bat dau session moi, thuc hien theo thu tu:
1. Doc file PROJECT_BASED_KNOWLEDGE.md.
2. Xac nhan dang o phase nao (1/2/3).
3. Xac nhan constraints phase do.
4. Neu viet code: uu tien patch nho, de test, de truy vet.
5. Chay validate output sau moi thay doi quan trong.

## 7) Cac artifact da co trong repo (tham chieu nhanh)
- Pipeline round 1: run_round1_pipeline.py
- MCQ mapping script: map_mcq_choices.py
- Round 1 report script: generate_round1_report.py
- SQL MCQ script: sql/solve_mcq.sql
- Notebook MCQ: 01_mcq_solver.ipynb
- Output thu muc: outputs_round1/

## 8) Quy tac giao tiep ky thuat trong team
- Ngan gon, co evidence, uu tien so lieu.
- Neu co gia dinh, phai ghi ro assumption.
- Neu co rui ro, phai ghi ro impact + huong giam thieu.
- Moi thay doi logic can update file nay de tranh mat tri nho qua session.
