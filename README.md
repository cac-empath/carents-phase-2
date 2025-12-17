# TAIS Code Scripts (Simple)

## Summary

Project ini punya **2 script**:

- **`data_prep.py`**
  Menyiapkan data TAIS Code dari JSON per tenant, lalu membuat:

  - JSON mapping TAIS → tenant
  - Excel matrix TAIS vs tenant

- **`compare.py`**
  Mengecek TAIS Code bulanan dari response JSON dan membandingkannya dengan:

  - data tenant
  - master TAIS (rental / non-rental)

---

## Struktur Folder

```
project/
├─ data_raw/
│  ├─ tenant_a/
│  │  ├─ response_1.json
│  │  └─ response_2.json
│  ├─ tenant_b/
│  │  └─ response_1.json
│  └─ tenant_c/
│     └─ response_1.json
│
├─ data_response/
│  ├─ api_response_20251101.json
│  ├─ api_response_20251115.json
│  └─ api_response_20251130.json
│
├─ data_reports/              # output (git ignored)
│  ├─ tais_code_tenant.json   # hasil mapping TAIS → tenant
│  ├─ tais_matrix_result_*.xlsx
│  └─ compare_result_*.xlsx
│
├─ codelist202511.xlsx        # master TAIS (Kolom A = TaisCd, Kolom E = Rent)
├─ data_prep.py               # preparation TAIS per tenant
├─ compare.py                 # testing TAIS bulanan
└─ README.md
```

---

## Cara Menjalankan

### Yang perlu disiapkan

- Python **3.11+**
- File:

  - `codelist202511.xlsx`
  - JSON tenant di `data_raw/*/*.json`
  - JSON response bulanan di `data_response/*.json`

- Library:

```bash
pip install pandas openpyxl
```

---

### 1️⃣ Preparation TAIS

```bash
python data_prep.py
```

Output:

- `data_reports/tais_code_tenant.json`
- `data_reports/tais_matrix_result_<timestamp>.xlsx`

---

### 2️⃣ Testing TAIS Bulanan

```bash
python compare.py
```

Output:

- Tabel hasil di terminal
- `data_reports/compare_result_<timestamp>.xlsx`
