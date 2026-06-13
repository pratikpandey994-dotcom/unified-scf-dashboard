import os
import pandas as pd
import numpy as np
from pathlib import Path

# Paths
downloads_dir = Path(r"c:\Users\PratikPandey\Downloads")
master_filename = "us_scf___master_data___client_level_2026-06-11T15_38_42.895386762Z.xlsx"
invoice_filename = "us_scf___invoice_level_data_2026-06-11T13_48_36.170164549Z.xlsx"

master_path = downloads_dir / master_filename
invoice_path = downloads_dir / invoice_filename

report_path = Path(r"c:\Users\PratikPandey\unified-scf-dashboard\.agents\teamwork_preview_explorer_excel_analysis\excel_analysis_report.md")

print(f"Reading master: {master_path}")
master_df = pd.read_excel(master_path)
print(f"Reading invoices: {invoice_path}")
invoice_df = pd.read_excel(invoice_path)

# Let's clean the IDs helper
def norm_id(val):
    if pd.isna(val):
        return ""
    text = str(val).replace(",", "").strip()
    return text[:-2] if text.endswith(".0") else text

# Master statistics and column mapping
master_df['clean_id'] = master_df['USER_ID'].apply(norm_id)
invoice_df['clean_id'] = invoice_df['IMPORTER_USER_ID'].apply(norm_id)

master_user_ids = set(master_df['clean_id'].unique()) - {""}
invoice_importer_ids = set(invoice_df['clean_id'].unique()) - {""}

matching_ids = master_user_ids.intersection(invoice_importer_ids)
orphaned_invoice_ids = invoice_importer_ids - master_user_ids
unmatched_master_ids = master_user_ids - invoice_importer_ids

# Statistics functions
def get_column_stats(df):
    stats = []
    for col in df.columns:
        null_count = df[col].isnull().sum()
        null_pct = (null_count / len(df)) * 100
        dtype = str(df[col].dtype)
        unique_count = df[col].nunique()
        sample = df[col].dropna().head(3).tolist()
        stats.append(f"| {col} | {dtype} | {null_count} ({null_pct:.2f}%) | {unique_count} | `{sample}` |")
    return "\n".join(stats)

master_col_stats_md = get_column_stats(master_df)
invoice_col_stats_md = get_column_stats(invoice_df)

# Value count functions formatted as MD tables
def get_vc_table(series, col_name):
    vc = series.value_counts(dropna=False)
    rows = []
    for val, count in vc.items():
        pct = (count / len(series)) * 100
        rows.append(f"| {val} | {count} | {pct:.2f}% |")
    return "\n".join(rows)

# Numerical summaries
facility_size_desc = master_df['FACILITY_SIZE'].describe()
overdraft_limit_desc = master_df['OVERDRAFT_LIMIT'].describe()
total_limit_desc = master_df['TOTAL_LIMIT'].describe()
master_ob_desc = master_df['OB'].describe()

invoice_outstanding_desc = invoice_df['OUTSTANDING_ADVANCE_BALANCE_USD'].describe()
invoice_origination_desc = invoice_df['ORIGINATION'].describe()

# Outstanding and count by Stage
stage_grp = invoice_df.groupby('STAGE').agg(
    count=('INVOICE_ID', 'count'),
    total_outstanding=('OUTSTANDING_ADVANCE_BALANCE_USD', 'sum'),
    total_origination=('ORIGINATION', 'sum')
).reset_index().sort_values(by='total_outstanding', ascending=False)

stage_grp_rows = []
for idx, r in stage_grp.iterrows():
    stage_grp_rows.append(f"| {r['STAGE']} | {r['count']} | ${r['total_outstanding']:,.2f} | ${r['total_origination']:,.2f} |")
stage_grp_md = "\n".join(stage_grp_rows)

# Outstanding and count by AM in Master
am_grp = master_df.groupby('AM').agg(
    count=('clean_id', 'count'),
    total_ob=('OB', 'sum'),
    total_facility=('TOTAL_LIMIT', 'sum')
).reset_index().sort_values(by='total_ob', ascending=False)

am_grp_rows = []
for idx, r in am_grp.iterrows():
    am_grp_rows.append(f"| {r['AM']} | {r['count']} | ${r['total_ob']:,.2f} | ${r['total_facility']:,.2f} |")
am_grp_md = "\n".join(am_grp_rows)

# Build the markdown content
md_content = f"""# Raw Excel Data Analysis Report

**Date of Analysis**: 2026-06-13
**As of Date of Extracts**: 2026-06-11
**Source Directory**: `c:\\Users\\PratikPandey\\Downloads`

---

## 1. File Inventory and Basic Shapes

| File Name | Row Count | Column Count | Description / Role |
| :--- | :---: | :---: | :--- |
| `{master_filename}` | {master_df.shape[0]} | {master_df.shape[1]} | Client-level master data containing limit, OB, IRR, AM, and status definitions. |
| `{invoice_filename}` | {invoice_df.shape[0]} | {invoice_df.shape[1]} | Invoice-level transaction data containing stage, origination, outstanding, dates, etc. |

---

## 2. Key Identifiers & Relationship Mapping

### USER_ID / IMPORTER_USER_ID Join Analysis
We normalized and joined `USER_ID` from the client-level master file and `IMPORTER_USER_ID` from the invoice level file.

- **Unique User IDs in Client Master**: {len(master_user_ids)}
- **Unique Importer User IDs in Invoice Data**: {len(invoice_importer_ids)}
- **Successfully Matched IDs (Intersection)**: {len(matching_ids)}
- **Orphaned Invoice IDs (present in invoices, but not in master)**: {len(orphaned_invoice_ids)}
- **Unmatched Master IDs (present in master, but no invoices)**: {len(unmatched_master_ids)}

#### Orphaned Invoice IDs (if any):
`{list(orphaned_invoice_ids)[:10]}` (showing up to 10)

#### Unmatched Master IDs (if any):
`{list(unmatched_master_ids)[:10]}` (showing up to 10)

### CP_ID and CP_COMPANY Mapping
- **Unique CP_IDs in Master**: {master_df['CP_ID'].nunique(dropna=True)}
- **Unique CP_COMPANYs (Partners) in Master**: {master_df['CP_COMPANY'].nunique(dropna=True)} (`{list(master_df['CP_COMPANY'].dropna().unique())[:5]}`...)
- **Unique CP_COMPANYs in Invoice**: {invoice_df['CP_COMPANY'].nunique(dropna=True)} (`{list(invoice_df['CP_COMPANY'].dropna().unique())[:5]}`...)

---

## 3. Account Status & Status Distributions

### Client-Level Master: ACCOUNT_STATUS
| ACCOUNT_STATUS | Account Count | Percentage |
| :--- | :---: | :---: |
{get_vc_table(master_df['ACCOUNT_STATUS'], 'ACCOUNT_STATUS')}

### Client-Level Master: BROAD_ACCOUNT_STATUS
| BROAD_ACCOUNT_STATUS | Account Count | Percentage |
| :--- | :---: | :---: |
{get_vc_table(master_df['BROAD_ACCOUNT_STATUS'], 'BROAD_ACCOUNT_STATUS')}

### Client-Level Master: USER_UTILIZATION_STATUS
| USER_UTILIZATION_STATUS | Account Count | Percentage |
| :--- | :---: | :---: |
{get_vc_table(master_df['USER_UTILIZATION_STATUS'], 'USER_UTILIZATION_STATUS')}

### Invoice-Level: STAGE
| STAGE | Invoice Count | Percentage |
| :--- | :---: | :---: |
{get_vc_table(invoice_df['STAGE'], 'STAGE')}

---

## 4. Limit and Balance Distributions

### Facility Size Statistics (Client-Level)
- **FACILITY_SIZE**:
  - Min: ${facility_size_desc['min']:,.2f}
  - Max: ${facility_size_desc['max']:,.2f}
  - Mean: ${facility_size_desc['mean']:,.2f}
  - Median: ${facility_size_desc['50%']:,.2f}
  - Std Dev: ${facility_size_desc['std']:,.2f}
- **OVERDRAFT_LIMIT**:
  - Min: ${overdraft_limit_desc['min']:,.2f}
  - Max: ${overdraft_limit_desc['max']:,.2f}
  - Mean: ${overdraft_limit_desc['mean']:,.2f}
  - Median: ${overdraft_limit_desc['50%']:,.2f}
  - Std Dev: ${overdraft_limit_desc['std']:,.2f}
- **TOTAL_LIMIT**:
  - Min: ${total_limit_desc['min']:,.2f}
  - Max: ${total_limit_desc['max']:,.2f}
  - Mean: ${total_limit_desc['mean']:,.2f}
  - Median: ${total_limit_desc['50%']:,.2f}
  - Std Dev: ${total_limit_desc['std']:,.2f}

### Outstanding Balances
- **Client-Level Master Outstanding Balance (OB)**:
  - Total Sum: ${master_df['OB'].sum():,.2f}
  - Min: ${master_ob_desc['min']:,.2f}
  - Max: ${master_ob_desc['max']:,.2f}
  - Mean: ${master_ob_desc['mean']:,.2f}
  - Median: ${master_ob_desc['50%']:,.2f}
- **Invoice-Level Outstanding Balance (OUTSTANDING_ADVANCE_BALANCE_USD)**:
  - Total Sum: ${invoice_df['OUTSTANDING_ADVANCE_BALANCE_USD'].sum():,.2f}
  - Min: ${invoice_outstanding_desc['min']:,.2f}
  - Max: ${invoice_outstanding_desc['max']:,.2f}
  - Mean: ${invoice_outstanding_desc['mean']:,.2f}
  - Median: ${invoice_outstanding_desc['50%']:,.2f}
  - Number of positive-outstanding invoices: {len(invoice_df[invoice_df['OUTSTANDING_ADVANCE_BALANCE_USD'] > 0])}

*Note: The master OB total (${master_df['OB'].sum():,.2f}) differs from the sum of outstanding advances in invoices (${invoice_df['OUTSTANDING_ADVANCE_BALANCE_USD'].sum():,.2f}). This is expected because master OB uses a different net measure than raw invoice outstanding balances.*

---

## 5. Segmentations & Aggregations

### Invoice Outstanding & Origination by STAGE
| STAGE | Count | Total Outstanding | Total Origination |
| :--- | :---: | :---: | :--- |
{stage_grp_md}

### Client-Level Accounts by AM (Top 15 by Outstanding Balance)
| AM | Count | Total Outstanding Balance (OB) | Total Facility size (TOTAL_LIMIT) |
| :--- | :---: | :---: | :--- |
{am_grp_md}

---

## 6. Columns & Schema Verification

### Client-Level Master Schema details
| Column Name | Data Type | Null Count (%) | Unique Values | Sample Values |
| :--- | :--- | :--- | :---: | :--- |
{master_col_stats_md}

### Invoice-Level Schema details
| Column Name | Data Type | Null Count (%) | Unique Values | Sample Values |
| :--- | :--- | :--- | :---: | :--- |
{invoice_col_stats_md}
"""

with open(report_path, "w", encoding="utf-8") as f:
    f.write(md_content)

print(f"Report successfully written to {report_path}")
print("Done!")
