import json
import requests
import pandas as pd
from pathlib import Path
from collections import OrderedDict, defaultdict
from datetime import datetime
import string
from config import API_URL, AUTH_TOKEN

# ============================================================
# PHASE 1 - API REQUEST & SAVE RESPONSE
# ============================================================

DATA_DIR = Path("data_test")
RESPONSE_DIR = Path("data_response")
RESPONSE_DIR.mkdir(exist_ok=True)

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {AUTH_TOKEN}"
}

json_files = sorted(DATA_DIR.glob("*.json"))

if not json_files:
    print("❌ No JSON payload found in data_test/")
    exit(1)

print(f"🚀 Start processing {len(json_files)} request(s)...\n")

for index, payload_file in enumerate(json_files, start=1):
    response_file = RESPONSE_DIR / f"response-{index}.json"

    # ⬅️ TERMINAL CUMA PROCESSING
    print(f"▶️  Processing [{index}/{len(json_files)}] : {payload_file.name}")

    log_data = {
        "file": payload_file.name,
        "status_code": None,
        "response": None
    }

    try:
        payload = json.loads(payload_file.read_text(encoding="utf-8"))

        response = requests.post(
            API_URL,
            headers=headers,
            json=payload,
            timeout=30
        )

        log_data["status_code"] = response.status_code

        if response.text and response.text.strip():
            try:
                log_data["response"] = response.json()
            except ValueError:
                log_data["response"] = response.text
        else:
            log_data["response"] = {}

    except Exception:
        # API sudah handle error → cukup simpan kosong
        log_data["response"] = {}

    # ⬅️ FILE SELALU DITULIS (UPDATE / OVERWRITE)
    with response_file.open("w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)

print("\n🎉 All requests processed.\n")

# ============================================================
# PHASE 2 - TAIS ANALYSIS & REPORT
# (TIDAK DIUBAH)
# ============================================================

TENANT_TAIS_FILE = Path("data_reports/tais_code_tenant.json")
CODELIST_FILE = "codelist202512.xlsx"
OUTPUT_DIR = Path("data_reports")
OUTPUT_DIR.mkdir(exist_ok=True)

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

ordered_results = OrderedDict()
seen = set()

response_files = sorted(RESPONSE_DIR.glob("response-*.json"), key=lambda x: x.name)

for file in response_files:
    with file.open(encoding="utf-8") as f:
        raw = json.load(f)

    response_body = raw.get("response", {})

    if not isinstance(response_body, dict):
        continue

    for item in response_body.get("ChoiseRentalList", []):
        tais_cd = item.get("TaisCd")
        if not tais_cd:
            continue

        tais_cd = str(tais_cd).strip()

        if tais_cd not in seen:
            seen.add(tais_cd)
            ordered_results[tais_cd] = file.name

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
        "",
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

if rows:
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

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = OUTPUT_DIR / f"compare_result_{timestamp}.xlsx"

pd.DataFrame(rows, columns=headers).to_excel(output_file, index=False)

print("\n✅ Excel report generated:")
print(output_file)
