import json
import requests
import pandas as pd
from pathlib import Path
from collections import OrderedDict, defaultdict
from datetime import datetime
import string
from config import API_URL, AUTH_URL, CLIENT_ID, CLIENT_SECRET

# ============================================================
# PATH CONFIG
# ============================================================

DATA_DIR = Path("data_test")
RESPONSE_DIR = Path("data_response")
REPORT_DIR = Path("data_reports")

RESPONSE_DIR.mkdir(exist_ok=True)
REPORT_DIR.mkdir(exist_ok=True)

# ============================================================
# HELPER
# ============================================================

def normalize_tais(value: str) -> str:
    return str(value).strip().replace("－", "-")

# ============================================================
# AUTH - GET ACCESS TOKEN
# ============================================================

auth_response = requests.post(
    AUTH_URL,
    data={
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    },
    timeout=30
)

auth_response.raise_for_status()
ACCESS_TOKEN = auth_response.json()["access_token"]

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

# ============================================================
# PHASE 1 - API REQUEST & SAVE RESPONSE
# ============================================================

json_files = sorted(DATA_DIR.glob("*.json"))

if not json_files:
    print("❌ No JSON payload found in data_test/")
    exit(1)

print(f"🚀 Start processing {len(json_files)} request(s)...\n")

for index, payload_file in enumerate(json_files, start=1):
    print(f"▶️  Processing [{index}/{len(json_files)}] : {payload_file.name}")

    payload = json.loads(payload_file.read_text(encoding="utf-8"))

    response = requests.post(
        API_URL,
        headers=headers,
        json=payload,
        timeout=30
    )

    try:
        response_body = response.json()
    except ValueError:
        response_body = {}

    with (RESPONSE_DIR / f"response-{index}.json").open("w", encoding="utf-8") as f:
        json.dump(
            {
                "file": payload_file.name,
                "status_code": response.status_code,
                "response": response_body
            },
            f,
            indent=2,
            ensure_ascii=False
        )

print("\n🎉 All requests processed.\n")

# ============================================================
# PHASE 2 - LOAD TENANT TAIS (FIXED)
# ============================================================

TENANT_TAIS_FILE = REPORT_DIR / "tais_code_tenant.json"

with TENANT_TAIS_FILE.open(encoding="utf-8") as f:
    tenant_data = json.load(f)

if "tais_by_tenant" not in tenant_data:
    raise ValueError("❌ Invalid tenant file format: 'tais_by_tenant' not found")

tais_by_tenant = tenant_data["tais_by_tenant"]

tais_to_tenants = defaultdict(set)
alphabet = list(string.ascii_uppercase)

for idx, (tenant_id, tais_list) in enumerate(tais_by_tenant.items()):
    tenant_label = f"Tenant {alphabet[idx]}"

    for tais_cd in tais_list:
        if not tais_cd:
            continue

        norm = normalize_tais(tais_cd)
        tais_to_tenants[norm].add(tenant_label)

# ============================================================
# LOAD TAIS MASTER (EXCEL)
# ============================================================

CODELIST_FILE = "codelist202512.xlsx"
df_master = pd.read_excel(CODELIST_FILE, header=0)

tais_master = {}

for _, row in df_master.iterrows():
    tais_cd = str(row.iloc[0]).strip()
    if not tais_cd or tais_cd.lower() == "nan":
        continue

    rent_flag = ""
    if len(row) > 4 and not pd.isna(row.iloc[4]):
        rent_flag = str(row.iloc[4]).strip()

    tais_master[normalize_tais(tais_cd)] = rent_flag

# ============================================================
# READ RESPONSE FILES
# ============================================================

ordered_results = OrderedDict()
seen = set()

for file in sorted(RESPONSE_DIR.glob("response-*.json")):
    with file.open(encoding="utf-8") as f:
        raw = json.load(f)

    response_body = raw.get("response", {})
    if not isinstance(response_body, dict):
        continue

    for item in response_body.get("ChoiseRentalList", []):
        tais_cd = item.get("TaisCd")
        if not tais_cd:
            continue

        norm = normalize_tais(tais_cd)

        if norm not in seen:
            seen.add(norm)
            ordered_results[norm] = file.name

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

# ============================================================
# EXPORT EXCEL
# ============================================================

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = REPORT_DIR / f"compare_result_{timestamp}.xlsx"

pd.DataFrame(rows, columns=headers).to_excel(output_file, index=False)

print("✅ Excel report generated:")
print(output_file)
