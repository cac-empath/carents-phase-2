import json
import pandas as pd
from pathlib import Path
from collections import OrderedDict, defaultdict
from datetime import datetime
import string

# ============================================================
# PATH CONFIG
# ============================================================
RESPONSE_DIR = Path("data_response")
TENANT_TAIS_FILE = Path("data_reports/tais_code_tenant.json")
CODELIST_FILE = "codelist202511.xlsx"
OUTPUT_DIR = Path("data_reports")

OUTPUT_DIR.mkdir(exist_ok=True)

# ============================================================
# LOAD TENANT TAIS FROM JSON
# Build mapping: TAIS -> set(Tenant Name)
# ============================================================
with TENANT_TAIS_FILE.open(encoding="utf-8") as f:
    tenant_data = json.load(f)

tais_to_tenants = defaultdict(set)

tais_by_file = tenant_data.get("tais_by_file", {})

alphabet = list(string.ascii_uppercase)
tenant_labels = {}
tenant_index = 0

for filename in sorted(tais_by_file.keys()):
    tenant_labels[filename] = f"Tenant {alphabet[tenant_index]}"
    tenant_index += 1

    for tais_cd in tais_by_file.get(filename, []):
        if tais_cd:
            tais_to_tenants[str(tais_cd).strip()].add(tenant_labels[filename])

# ============================================================
# LOAD TAIS MASTER FROM EXCEL
# Kolom A = TaisCd
# Kolom E = 貸与
# ============================================================
df_master = pd.read_excel(CODELIST_FILE, header=0)

tais_master = {}
for _, row in df_master.iterrows():
    tais_cd = str(row.iloc[0]).strip()
    if not tais_cd or tais_cd.lower() == "nan":
        continue

    rent_flag = ""
    if len(row) > 4 and not pd.isna(row.iloc[4]):
        rent_flag = str(row.iloc[4]).strip()

    tais_master[tais_cd] = rent_flag

# ============================================================
# READ RESPONSE JSON (ORDER BY FILE)
# ============================================================
ordered_results = OrderedDict()
seen = set()

json_files = sorted(RESPONSE_DIR.glob("*.json"), key=lambda x: x.name)

for file in json_files:
    with file.open(encoding="utf-8") as f:
        raw = json.load(f)

    data = raw[0] if isinstance(raw, list) and raw else raw

    for item in data.get("ChoiseRentalList", []):
        tais_cd = item.get("TaisCd")
        if not tais_cd:
            continue

        tais_cd = str(tais_cd).strip()

        if tais_cd not in seen:
            seen.add(tais_cd)
            ordered_results[tais_cd] = file.name

# ============================================================
# BUILD RESULT TABLE
# ============================================================
rows = []

for tais_cd, source_file in ordered_results.items():
    exists_and_rent = (
        "Yes"
        if tais_cd in tais_master and tais_master.get(tais_cd) == "○"
        else "-"
    )

    tenants = sorted(tais_to_tenants.get(tais_cd, []))
    tenant_display = ", ".join(tenants) if tenants else "Global TAIS"

    rows.append([
        tais_cd,
        exists_and_rent,
        "",  # Client From? (empty by design)
        tenant_display,
        source_file
    ])

headers = [
    "TaisCd",
    "Exists & Rent",
    "Client From?",
    "Exists in Tenant",
    "Source JSON"
]

# ============================================================
# PRINT TABLE TO TERMINAL
# ============================================================
col_widths = [
    max(len(str(row[i])) for row in ([headers] + rows))
    for i in range(len(headers))
]

def print_row(row):
    return " | ".join(
        str(row[i]).ljust(col_widths[i]) for i in range(len(row))
    )

total_width = sum(col_widths) + (3 * (len(headers) - 1))

print("=" * total_width)
print(print_row(headers))
print("=" * total_width)

for row in rows:
    print(print_row(row))

print("=" * total_width)
print(f"Total unique TaisCd checked: {len(rows)}")

# ============================================================
# EXPORT TO EXCEL
# ============================================================
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = OUTPUT_DIR / f"compare_result_{timestamp}.xlsx"

df_export = pd.DataFrame(rows, columns=headers)
df_export.to_excel(output_file, index=False)

print("\n✅ Excel report generated:")
print(output_file)
