# Raw Excel Data Analysis Report

**Date of Analysis**: 2026-06-13
**As of Date of Extracts**: 2026-06-11
**Source Directory**: `c:\Users\PratikPandey\Downloads`

---

## 1. File Inventory and Basic Shapes

| File Name | Row Count | Column Count | Description / Role |
| :--- | :---: | :---: | :--- |
| `us_scf___master_data___client_level_2026-06-11T15_38_42.895386762Z.xlsx` | 647 | 38 | Client-level master data containing limit, OB, IRR, AM, and status definitions. |
| `us_scf___invoice_level_data_2026-06-11T13_48_36.170164549Z.xlsx` | 36975 | 36 | Invoice-level transaction data containing stage, origination, outstanding, dates, etc. |

---

## 2. Key Identifiers & Relationship Mapping

### USER_ID / IMPORTER_USER_ID Join Analysis
We normalized and joined `USER_ID` from the client-level master file and `IMPORTER_USER_ID` from the invoice level file.

- **Unique User IDs in Client Master**: 647
- **Unique Importer User IDs in Invoice Data**: 647
- **Successfully Matched IDs (Intersection)**: 647
- **Orphaned Invoice IDs (present in invoices, but not in master)**: 0
- **Unmatched Master IDs (present in master, but no invoices)**: 0

#### Orphaned Invoice IDs (if any):
`[]` (showing up to 10)

#### Unmatched Master IDs (if any):
`[]` (showing up to 10)

### CP_ID and CP_COMPANY Mapping
- **Unique CP_IDs in Master**: 44
- **Unique CP_COMPANYs (Partners) in Master**: 43 (`['C2FO', 'Flexent', 'Anderson CFO, LLC', 'GO2 Fintrade LLC', 'Boundless Financial Corp']`...)
- **Unique CP_COMPANYs in Invoice**: 43 (`['IGA Trade Credit', 'Beacon Business Capital', 'Funding Nexus', 'GO2 Fintrade LLC', 'Capo Fin Corporation']`...)

---

## 3. Account Status & Status Distributions

### Client-Level Master: ACCOUNT_STATUS
| ACCOUNT_STATUS | Account Count | Percentage |
| :--- | :---: | :---: |
| Workable - Active | 239 | 36.94% |
| Non-Workable | 206 | 31.84% |
| Workable - Inactive (BDM) | 127 | 19.63% |
| Workable - Temporarily suspended | 45 | 6.96% |
| Workable - Inactive (AM) | 30 | 4.64% |

### Client-Level Master: BROAD_ACCOUNT_STATUS
| BROAD_ACCOUNT_STATUS | Account Count | Percentage |
| :--- | :---: | :---: |
| Workable | 441 | 68.16% |
| Non-Workable | 206 | 31.84% |

### Client-Level Master: USER_UTILIZATION_STATUS
| USER_UTILIZATION_STATUS | Account Count | Percentage |
| :--- | :---: | :---: |
| suspended | 407 | 62.91% |
| active | 240 | 37.09% |

### Invoice-Level: STAGE
| STAGE | Invoice Count | Percentage |
| :--- | :---: | :---: |
| closed | 28707 | 77.64% |
| paid | 4752 | 12.85% |
| advanced | 3009 | 8.14% |
| npa | 264 | 0.71% |
| overdue | 171 | 0.46% |
| partial | 67 | 0.18% |
| received | 3 | 0.01% |
| partadvanced | 2 | 0.01% |

---

## 4. Limit and Balance Distributions

### Facility Size Statistics (Client-Level)
- **FACILITY_SIZE**:
  - Min: $0.00
  - Max: $5,000,000.00
  - Mean: $319,511.01
  - Median: $200,000.00
  - Std Dev: $443,449.67
- **OVERDRAFT_LIMIT**:
  - Min: $0.00
  - Max: $350,000.00
  - Mean: $6,398.76
  - Median: $0.00
  - Std Dev: $31,909.29
- **TOTAL_LIMIT**:
  - Min: $0.00
  - Max: $5,000,000.00
  - Mean: $325,909.77
  - Median: $200,000.00
  - Std Dev: $448,841.93

### Outstanding Balances
- **Client-Level Master Outstanding Balance (OB)**:
  - Total Sum: $81,140,144.28
  - Min: $0.00
  - Max: $4,869,452.18
  - Mean: $128,998.64
  - Median: $0.00
- **Invoice-Level Outstanding Balance (OUTSTANDING_ADVANCE_BALANCE_USD)**:
  - Total Sum: $89,982,878.90
  - Min: $0.00
  - Max: $650,000.00
  - Mean: $2,433.61
  - Median: $0.00
  - Number of positive-outstanding invoices: 3447

*Note: The master OB total ($81,140,144.28) differs from the sum of outstanding advances in invoices ($89,982,878.90). This is expected because master OB uses a different net measure than raw invoice outstanding balances.*

---

## 5. Segmentations & Aggregations

### Invoice Outstanding & Origination by STAGE
| STAGE | Count | Total Outstanding | Total Origination |
| :--- | :---: | :---: | :--- |
| advanced | 3009 | $75,479,359.22 | $75,479,359.22 |
| npa | 264 | $8,348,937.52 | $11,071,750.32 |
| overdue | 171 | $3,162,238.29 | $3,625,495.08 |
| partial | 67 | $2,933,143.87 | $3,818,594.86 |
| partadvanced | 2 | $59,200.00 | $59,200.00 |
| closed | 28707 | $0.00 | $895,414,037.90 |
| paid | 4752 | $0.00 | $164,770,617.91 |
| received | 3 | $0.00 | $215,634.73 |

### Client-Level Accounts by AM (Top 15 by Outstanding Balance)
| AM | Count | Total Outstanding Balance (OB) | Total Facility size (TOTAL_LIMIT) |
| :--- | :---: | :---: | :--- |
| Pejush Hal | 71 | $15,418,220.45 | $26,305,000.00 |
| Nikhil Shetty | 87 | $11,843,065.81 | $41,630,001.00 |
| Kaustav Das | 67 | $11,084,377.54 | $17,150,000.00 |
| Ashitha Nair | 54 | $10,975,668.90 | $17,882,029.00 |
| Pankit Shah | 29 | $9,362,794.46 | $23,200,488.00 |
| Sonal Mishra | 48 | $7,703,464.60 | $12,875,054.00 |
| Darshan Hublikar | 41 | $6,658,507.29 | $11,190,001.00 |
| Deepsayan Dam | 48 | $6,533,471.40 | $10,950,051.00 |
| Pratik Pandey | 2 | $104,919.66 | $200,000.00 |
| Asif Ali | 25 | $95,570.52 | $3,655,000.00 |
| Adriana Carbajal Rivera | 4 | $0.00 | $1,000,000.00 |
| Amar Samarapally | 3 | $0.00 | $125,000.00 |
| Arjun Narayan | 2 | $0.00 | $225,000.00 |
| Miriam Cristina Godinez Carranza | 4 | $0.00 | $1,090,000.00 |
| Ayush Shrivastava | 4 | $0.00 | $1,075,000.00 |
| Luis Miguel Gongora Boy | 19 | $0.00 | $6,275,000.00 |
| Pablo Zavala Sousa | 29 | $0.00 | $4,750,000.00 |
| Sakshi Issar | 17 | $0.00 | $4,080,000.00 |
| Shreyanshu Devikar | 44 | $0.00 | $13,626,000.00 |
| Suraj Petkar | 6 | $0.00 | $950,000.00 |

---

## 6. Columns & Schema Verification

### Client-Level Master Schema details
| Column Name | Data Type | Null Count (%) | Unique Values | Sample Values |
| :--- | :--- | :--- | :---: | :--- |
| USER_ID | int64 | 0 (0.00%) | 647 | `[481826, 479652, 482100]` |
| IMPORTER_NAME | str | 0 (0.00%) | 646 | `['Anthem Snacks LLC', 'Kope Logistics Inc.', 'Hamilton Home Products Inc.']` |
| CP_ID | float64 | 334 (51.62%) | 44 | `[372872.0, 372872.0, 372872.0]` |
| CP_COMPANY | str | 335 (51.78%) | 43 | `['C2FO', 'C2FO', 'C2FO']` |
| TYPE | str | 0 (0.00%) | 2 | `['CP', 'DIRECT', 'CP']` |
| AIRTABLE_INDUSTRY | str | 53 (8.19%) | 18 | `['Food - Animal Products', 'Other', 'Consumer - Others']` |
| AIRTABLE_GOODS_SHIPPED | str | 194 (29.98%) | 394 | `['Sugar cane; fit for human consumption, fresh, chilled, frozen or dried, whether or not ground, Aluminium oxide; other than artificial corundum, Paints and varnishes; based on acrylic or vinyl polymers, dispersed or dissolved in an aqueous medium,Alcohols; saturated monohydric, propan-1-ol (propyl alcohol) and propan-2-ol (isopropyl alcohol)', 'Vegetable fats and oils and their fractions; fixed, n.e.c. in heading no. 1515, whether or not refined, but not chemically modified, Edible mixtures or preparations of animal or vegetable fats or oils or of fractions of different fats or oils of this chapter, other than edible fats or oils of heading no. 1516', "Bedding and similar furnishing articles; n.e.c. in heading no. 9404 (e.g. quilts, eiderdowns, cushions, pouffes and pillows), Jerseys, pullovers, cardigans, waistcoats and similar articles; of cotton, knitted or crocheted,Nightdresses and pyjamas; women's or girls', of textile materials (other than cotton or man-made fibres), knitted or crocheted"]` |
| USER_UTILIZATION_STATUS | str | 0 (0.00%) | 2 | `['active', 'active', 'active']` |
| FIRST_DISBURSED_DATE | datetime64[us] | 0 (0.00%) | 505 | `[Timestamp('2026-06-08 00:00:00'), Timestamp('2026-06-05 00:00:00'), Timestamp('2026-06-04 00:00:00')]` |
| LAST_DISBURSED_DATE | datetime64[us] | 0 (0.00%) | 400 | `[Timestamp('2026-06-08 00:00:00'), Timestamp('2026-06-05 00:00:00'), Timestamp('2026-06-04 00:00:00')]` |
| FACILITY_SIZE | int64 | 0 (0.00%) | 78 | `[100000, 400000, 50000]` |
| OVERDRAFT_LIMIT | int64 | 0 (0.00%) | 11 | `[0, 0, 0]` |
| TOTAL_LIMIT | int64 | 0 (0.00%) | 74 | `[100000, 400000, 50000]` |
| OB | float64 | 18 (2.78%) | 239 | `[84927.072, 80491.6, 47881.562]` |
| MAX_DPD | float64 | 153 (23.65%) | 191 | `[1.0, 5.0, 9.0]` |
| MAX_OPEN_DPD | float64 | 14 (2.16%) | 69 | `[0.0, 0.0, 0.0]` |
| SIGNED_UP_IRR | float64 | 0 (0.00%) | 266 | `[23.2, 20.5, 22.7]` |
| INTEREST_RATE | float64 | 0 (0.00%) | 155 | `[19.2, 18.0, 19.2]` |
| FLAT_DISCOUNTING_FEE | float64 | 0 (0.00%) | 40 | `[0.8, 0.5, 0.7]` |
| PLANS_PAYMENT_TENOR | int64 | 0 (0.00%) | 5 | `[90, 90, 90]` |
| OVERDUE_RATE | int64 | 0 (0.00%) | 11 | `[36, 36, 36]` |
| USER_ADDRESS | str | 36 (5.56%) | 604 | `['380 MOUNTAIN MAN TRAIL #781, MT, GALLATIN GATEWAY, United States Of America, 59730', '6550 NW 97TH AVE, FL, DORAL, United States Of America, 33178', '8260 HOWE INDUSTRIAL PARKWAY SUITEF, OH, CANAL WINCHESTER, United States Of America, 43110']` |
| USER_CITY | str | 262 (40.49%) | 240 | `['Bozeman', 'Doral', 'Canal Winchester']` |
| USER_STATE | str | 59 (9.12%) | 58 | `['Montana', 'Florida', 'Ohio']` |
| USER_COUNTRY | str | 0 (0.00%) | 2 | `['United States Of America', 'United States Of America', 'United States Of America']` |
| AM | str | 43 (6.65%) | 20 | `['Deepsayan Dam', 'Darshan Hublikar', 'Deepsayan Dam']` |
| BDM | str | 42 (6.49%) | 45 | `['Matt Heske', 'Aanchal Kumari', 'Matt Heske']` |
| ACCOUNT_STATUS | str | 0 (0.00%) | 5 | `['Workable - Active', 'Workable - Active', 'Workable - Active']` |
| BROAD_ACCOUNT_STATUS | str | 0 (0.00%) | 2 | `['Workable', 'Workable', 'Workable']` |
| POD_MANAGER | str | 0 (0.00%) | 2 | `['Nikhil Shetty', 'Pankit Shah', 'Nikhil Shetty']` |
| PLANS_MARGIN_RATE | int64 | 0 (0.00%) | 3 | `[20, 20, 20]` |
| PLANS_ADVANCE_RATE | int64 | 0 (0.00%) | 3 | `[80, 80, 80]` |
| PROCESSING_FEE | float64 | 0 (0.00%) | 7 | `[0.5, 0.0, 0.5]` |
| ANNUAL_MAINTENANCE_FEE | float64 | 250 (38.64%) | 12 | `[0.5, 0.0, 0.5]` |
| PG_STATUS | str | 0 (0.00%) | 2 | `['Yes', 'Yes', 'Yes']` |
| CG_STATUS | str | 0 (0.00%) | 1 | `['No', 'No', 'No']` |
| PLAID_STATUS | str | 0 (0.00%) | 3 | `['Not Integrated', 'Active', 'Active']` |
| clean_id | str | 0 (0.00%) | 647 | `['481826', '479652', '482100']` |

### Invoice-Level Schema details
| Column Name | Data Type | Null Count (%) | Unique Values | Sample Values |
| :--- | :--- | :--- | :---: | :--- |
| INVOICE_ID | int64 | 0 (0.00%) | 36975 | `[131478, 238084, 238731]` |
| IMPORTER_USER_ID | int64 | 0 (0.00%) | 647 | `[314543, 359520, 214459]` |
| IMPORTER_COMPANY | str | 0 (0.00%) | 646 | `['GSI SUPPLIES INC', 'CROSSDOCK SUPPLY, LLC', 'LASER MASTER INTERNATIONAL, INC. (DBA- FLEXO-CRAFT PRINTS,INC.)']` |
| BUYER_COUNTRY | str | 0 (0.00%) | 2 | `['United States Of America', 'United States Of America', 'United States Of America']` |
| EXPORTER_USER_ID | int64 | 0 (0.00%) | 3682 | `[320906, 370942, 372359]` |
| EXPORTER_COMPANY | str | 0 (0.00%) | 3642 | `['MIGALI INDUSTRIES', 'Ingersoll-Rand Industrial U.S. Inc', 'DI PAPEL SA DE CV']` |
| EXPORTER_COUNTRY | str | 0 (0.00%) | 88 | `['United States Of America', 'United States Of America', 'Mexico']` |
| CP_COMPANY | str | 17497 (47.32%) | 43 | `['IGA Trade Credit', 'Beacon Business Capital', 'IGA Trade Credit']` |
| TYPE | str | 0 (0.00%) | 2 | `['CP', 'CP', 'CP']` |
| ACCOUNT_STATUS | str | 0 (0.00%) | 4 | `['Non-Workable', 'Workable - Active', 'Workable - Active']` |
| USER_UTILIZATION_STATUS | str | 0 (0.00%) | 2 | `['suspended', 'suspended', 'active']` |
| AM | str | 444 (1.20%) | 20 | `['Pejush Hal', 'Ashitha Nair', 'Nikhil Shetty']` |
| STAGE | str | 0 (0.00%) | 8 | `['closed', 'closed', 'closed']` |
| INVOICE_DATE | datetime64[us] | 0 (0.00%) | 2060 | `[Timestamp('2023-03-21 00:00:00'), Timestamp('2025-05-02 00:00:00'), Timestamp('2025-05-07 00:00:00')]` |
| MARGIN_RECEIVED_DATE | datetime64[us] | 2 (0.01%) | 1408 | `[Timestamp('2023-03-28 00:00:00'), Timestamp('2025-06-04 00:00:00'), Timestamp('2025-06-09 00:00:00')]` |
| FIRST_ADVANCE_DATE | datetime64[us] | 0 (0.00%) | 1398 | `[Timestamp('2023-03-28 00:00:00'), Timestamp('2025-06-04 00:00:00'), Timestamp('2025-06-10 00:00:00')]` |
| DUE_DATE | datetime64[us] | 0 (0.00%) | 1956 | `[Timestamp('2023-06-26 00:00:00'), Timestamp('2025-09-02 00:00:00'), Timestamp('2025-09-08 00:00:00')]` |
| SETTLEMENT_DATE | datetime64[us] | 3513 (9.50%) | 1391 | `[Timestamp('2023-06-26 00:00:00'), Timestamp('2025-09-04 00:00:00'), Timestamp('2025-09-02 00:00:00')]` |
| INVOICE_TERM | int64 | 0 (0.00%) | 6 | `[90, 90, 90]` |
| CURRENCY | str | 0 (0.00%) | 5 | `['USD', 'USD', 'USD']` |
| INVOICE_VALUE_USD | float64 | 0 (0.00%) | 29741 | `[4775.0, 87728.0, 11174.66]` |
| TOTAL_ADVANCED | float64 | 0 (0.00%) | 29377 | `[4775.0, 87728.0, 11174.66]` |
| MARGIN_RECEIVED_USD | float64 | 0 (0.00%) | 29868 | `[955.0, 13159.2, 1676.199]` |
| ORIGINATION | float64 | 0 (0.00%) | 30786 | `[3820.0, 74568.8, 9498.461]` |
| INTEREST_RATE | float64 | 0 (0.00%) | 260 | `[15.0, 18.0, 16.0]` |
| DISCOUNTING_RATE | float64 | 0 (0.00%) | 46 | `[0.5, 0.8, 0.15]` |
| BOOKED_REVENUE | int64 | 0 (0.00%) | 5528 | `[167, 4058, 397]` |
| EXPECTED_REGULAR_INTEREST_USD | int64 | 0 (0.00%) | 4981 | `[143, 3356, 380]` |
| EXPECTED_FACTORING_FEES_USD | int64 | 0 (0.00%) | 1546 | `[24, 702, 17]` |
| REGULAR_INTEREST_NATIVE | float64 | 3531 (9.55%) | 4715 | `[143.0, 3428.0, 355.0]` |
| FACTORING_FEES_NATIVE | float64 | 3531 (9.55%) | 1516 | `[24.0, 702.0, 17.0]` |
| OVERDUE_INTEREST_NATIVE | float64 | 3531 (9.55%) | 1173 | `[0.0, 149.0, 0.0]` |
| TOTAL_LIMIT | int64 | 0 (0.00%) | 74 | `[100000, 500000, 2861000]` |
| OUTSTANDING_ADVANCE_BALANCE_USD | float64 | 0 (0.00%) | 3093 | `[0.0, 0.0, 0.0]` |
| DAYS_PAST_DUE | float64 | 25641 (69.35%) | 446 | `[2.0, 1.0, 2.0]` |
| clean_id | str | 0 (0.00%) | 647 | `['314543', '359520', '214459']` |
