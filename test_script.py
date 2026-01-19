import json
import requests
import pandas as pd
from pathlib import Path
from collections import defaultdict
from datetime import datetime

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

def normalize_tais(value):
    if value is None:
        return ""
    return str(value).strip().replace("－", "-")

def find_codelist_file():
    fixed = Path("codelist.xlsx")
    if fixed.exists():
        return fixed

    candidates = sorted(
        Path(".").glob("codelist*.xlsx"),
        key=lambda f: f.stat().st_mtime,
        reverse=True
    )

    if not candidates:
        raise FileNotFoundError("❌ No codelist excel file found")

    return candidates[0]

def generate_curl_txt(api_url, headers, payload):
    payload_pretty = json.dumps(payload, indent=2, ensure_ascii=False)

    return (
        f'curl -X POST "{api_url}" \\\n'
        f'  -header "Authorization: {headers["Authorization"]}" \\\n'
        f'  -header "Content-Type: application/json" \\\n'
        f"  -data '{payload_pretty}'"
    )

# ============================================================
# AUTH
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
auth_json = auth_response.json()

ACCESS_TOKEN = auth_json.get("access_token")
if not ACCESS_TOKEN:
    raise RuntimeError("❌ access_token not found")

auth_info = {
    "access_token": ACCESS_TOKEN,
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "expires_in": auth_json.get("expires_in")
}

http_headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

# ============================================================
# PHASE 1 - API REQUEST
# ============================================================

json_files = sorted(DATA_DIR.glob("*.json"))
if not json_files:
    raise RuntimeError("❌ No JSON payload found")

print(f"🚀 Processing {len(json_files)} request(s)\n")

for idx, payload_file in enumerate(json_files, start=1):
    print(f"▶️ [{idx}] {payload_file.name}")

    payload = json.loads(payload_file.read_text(encoding="utf-8"))

    response = requests.post(
        API_URL,
        headers=http_headers,
        json=payload,
        timeout=60
    )

    try:
        response_body = response.json()
    except ValueError:
        response_body = {}

    # save response json (WITH AUTH INFO)
    with (RESPONSE_DIR / f"response-{idx}.json").open("w", encoding="utf-8") as f:
        json.dump(
            {
                "file": payload_file.name,
                "auth": auth_info,
                "status_code": response.status_code,
                "response": response_body
            },
            f,
            indent=2,
            ensure_ascii=False
        )

    # save curl txt (MULTILINE & PRETTY)
    curl_txt = generate_curl_txt(API_URL, http_headers, payload)
    (RESPONSE_DIR / f"response-{idx}.curl.txt").write_text(curl_txt, encoding="utf-8")

print("\n🎉 API phase done\n")

# ============================================================
# LOAD TENANT TAIS
# ============================================================

tenant_file = REPORT_DIR / "tais_code_tenant.json"
tenant_data = json.loads(tenant_file.read_text(encoding="utf-8"))

tais_to_tenants = defaultdict(set)

for i, (_, tais_list) in enumerate(tenant_data["tais_by_tenant"].items(), start=1):
    tenant_label = f"Tenant {i}"
    for tais_cd in tais_list:
        norm = normalize_tais(tais_cd)
        if norm:
            tais_to_tenants[norm].add(tenant_label)

# ============================================================
# LOAD TAIS MASTER
# ============================================================

codelist_file = find_codelist_file()
print(f"📘 Using codelist: {codelist_file.name}")

df_master = pd.read_excel(codelist_file)
tais_master = {}

for _, row in df_master.iterrows():
    tais_cd = normalize_tais(row.iloc[0])
    if not tais_cd:
        continue

    rent_flag = ""
    if len(row) > 4 and not pd.isna(row.iloc[4]):
        rent_flag = str(row.iloc[4]).strip()

    tais_master[tais_cd] = rent_flag

# ============================================================
# BUILD REPORT
# ============================================================

rows = []

for file in sorted(RESPONSE_DIR.glob("response-*.json")):
    raw = json.loads(file.read_text(encoding="utf-8"))
    response_body = raw.get("response", {})

    for item in response_body.get("ChoiseRentalList", []):
        tais_cd = normalize_tais(item.get("TaisCd"))

        rows.append([
            tais_cd,
            "Yes" if tais_master.get(tais_cd) == "○" else "-",
            "",
            ", ".join(sorted(tais_to_tenants.get(tais_cd, []))) or "Global TAIS",
            file.name
        ])

excel_headers = [
    "TaisCd",
    "Exists & Rent",
    "Client From?",
    "Exists in Tenant",
    "Source JSON"
]

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = REPORT_DIR / f"compare_result_{timestamp}.xlsx"

pd.DataFrame(rows, columns=excel_headers).to_excel(output_file, index=False)

print("✅ Excel generated:")
print(output_file)
