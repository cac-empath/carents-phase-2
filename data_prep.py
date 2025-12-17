import json
import os
import pandas as pd
from datetime import datetime

# =====================
# CONFIG
# =====================
DATA_FOLDER = "data_raw"
MASTER_EXCEL = "codelist202512.xlsx"
REPORT_FOLDER = "data_reports"
TAIS_JSON_OUTPUT = os.path.join(REPORT_FOLDER, "tais_code_tenant.json")

CUSTOM_HEADERS = [
    "TAISコード",
    "法人名",
    "商品名",
    "型番",
    "貸与",
    "販売"
]

os.makedirs(REPORT_FOLDER, exist_ok=True)

# =====================
# TIMESTAMP (EXCEL ONLY)
# =====================
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
REPORT_EXCEL = f"tais_matrix_result_{timestamp}.xlsx"

# =====================
# READ RAW JSON (PER TENANT)
# =====================
tais_by_tenant = {}
all_tais_codes = set()
tenant_list = []

for tenant_folder in sorted(os.listdir(DATA_FOLDER)):
    tenant_path = os.path.join(DATA_FOLDER, tenant_folder)

    if not os.path.isdir(tenant_path):
        continue

    tenant_list.append(tenant_folder)
    tenant_tais_set = set()

    for filename in sorted(os.listdir(tenant_path)):
        if not filename.endswith(".json"):
            continue

        with open(os.path.join(tenant_path, filename), "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            continue

        for item in data:
            plans = item.get("TU_ServicePlanChoiseRental")
            if not isinstance(plans, list):
                continue

            for plan in plans:
                code = plan.get("TaisCd")
                if code:
                    tenant_tais_set.add(code)
                    all_tais_codes.add(code)

    tais_by_tenant[tenant_folder] = tenant_tais_set

# =====================
# EXPORT TAIS JSON
# =====================
with open(TAIS_JSON_OUTPUT, "w", encoding="utf-8") as f:
    json.dump(
        {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tais_by_tenant": {
                t: sorted(list(codes))
                for t, codes in tais_by_tenant.items()
            }
        },
        f,
        ensure_ascii=False,
        indent=2
    )

print("🧾 TAIS JSON berhasil di-update:", TAIS_JSON_OUTPUT)

# =====================
# READ MASTER EXCEL
# =====================
df_master = pd.read_excel(MASTER_EXCEL, dtype=str)
df_master.fillna("", inplace=True)

master_rows = df_master.values.tolist()

# index 0 = TAISコード
master_map = {
    row[0]: row
    for row in master_rows
    if row[0]  # pastikan tidak kosong
}

# =====================
# BUILD MATRIX (ALL TAIS)
# =====================
export_rows = []

for tais_code in sorted(all_tais_codes):
    if tais_code in master_map:
        base_row = master_map[tais_code][:len(CUSTOM_HEADERS)]
    else:
        # TAIS tidak ada di master → bikin row kosong
        base_row = [tais_code] + [""] * (len(CUSTOM_HEADERS) - 1)

    for tenant in tenant_list:
        base_row.append("○" if tais_code in tais_by_tenant[tenant] else "")

    export_rows.append(base_row)

# =====================
# EXPORT EXCEL
# =====================
final_headers = CUSTOM_HEADERS + tenant_list
df_export = pd.DataFrame(export_rows, columns=final_headers)

excel_path = os.path.join(REPORT_FOLDER, REPORT_EXCEL)
df_export.to_excel(excel_path, index=False)

print("✅ Excel report berhasil dibuat:", excel_path)
