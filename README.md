# TAIS Code Scripts (Simple)

## Summary

Project ini punya **3 script**:

- **`data_prep.py`**
  Menyiapkan data TAIS Code dari JSON per tenant, lalu membuat:

  - JSON mapping TAIS → tenant
  - Excel matrix TAIS vs tenant

- **`test_script.py`**
  Melakukan testing API dan analisis TAIS Code:

  - Kirim request API dari payload JSON
  - Simpan response API
  - Bandingkan TAIS Code dengan data tenant & master TAIS
  - Tampilkan hasil di terminal dan Excel

- **`compare.py`**
  Mengecek TAIS Code dari response JSON dan membandingkannya dengan:

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
│  └─ api_response_20251130.json
│
├─ data_test/
│  ├─ payload-1.json
│  └─ payload-2.json
│
├─ data_reports/                  # output (git ignored)
│  ├─ tais_code_tenant.json       # hasil mapping TAIS → tenant
│  ├─ tais_matrix_result_*.xlsx   # hasil matrix TAIS vs tenant
│  └─ compare_result_*.xlsx       # hasil perbandingan TAIS
│
├─ .env                           # API config (not committed)
├─ .gitignore
├─ codelist202511.xlsx            # master TAIS (Kolom A = TaisCd, Kolom E = Rent)
├─ data_prep.py                   # preparation TAIS per tenant
├─ test_script.py                 # API testing & TAIS analysis
├─ compare.py
└─ README.md
```

---

## Cara Menjalankan

### Yang perlu disiapkan

- Python **3.11**
- File:

  - `taiscode.xlsx`
  - JSON tenant di `data_raw/*/*.json`
  - JSON response di `data_response/*.json`
  - JSON data test di `data_test/*.json`

- Library:

```bash
pip install -r requirements.txt
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
python test_script.py
```

Output:

- `Tabel hasil di terminal`
- `data_reports/compare_result_<timestamp>.xlsx`
