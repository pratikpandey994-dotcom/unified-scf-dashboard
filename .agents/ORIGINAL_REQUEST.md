# Original User Request

## Initial Request — 2026-06-13T10:52:29Z

# Teamwork Project Prompt — Draft

Analyze all tabs in the Unified SCF Dashboard, critique their current data visualization, and refactor the components to use a cleaner, more minimal design language.

Working directory: c:\Users\PratikPandey\unified-scf-dashboard
Integrity mode: development

## Requirements

### R1. Structural Refactor
The agent team has full autonomy to restructure, consolidate, or redesign the existing 10 tabs to achieve maximum minimalism and cleanliness without losing critical functionality.

### R2. Data-Dense Aesthetic
Revamp the data visualizations and dataframes. Keep the dataframes visible by default (data-dense), but aggressively strip out borders, alternate row styling, and unnecessary visual noise to make them sleek and clean.

### R3. Local Testing Only (No Git Pushes)
Do not automatically commit or push any changes to the git repository. All UI and structural changes must be run and reviewed on localhost first to prevent breaking the live dashboard or losing existing efforts.

## Acceptance Criteria

### Visualization Quality
- [ ] The dashboard's tab structure has been cohesively reorganized into a minimalist layout.
- [ ] All dataframes and tables are styled seamlessly (no heavy borders, no alternating row colors).
- [ ] An agent-as-judge script or independent evaluation confirms that visual noise has been minimized.
- [ ] No `git push` commands were executed during the process.

## Follow-up — 2026-06-13T11:33:09Z

# Teamwork Project Prompt — Draft

Deeply analyze the underlying Excel data and all metrics across the Unified SCF Dashboard. Act as a Data Scientist to transform plain numbers into meaningful, clean visual insights, while completely eliminating vertical scroll fatigue through smart sub-tabbing.

Working directory: c:\Users\PratikPandey\unified-scf-dashboard
Integrity mode: development

## Requirements

### R1. Deep Excel Data Analysis
Spawn a dedicated agent to thoroughly study the raw Excel files (typically Masterdata and Invoice data in Downloads or `data/` directories) inside and out to deeply understand the schema, data distributions, and relationships.

### R2. Data Scientist Visualizations
Understand the specific metrics that both Nikhil and Pankit are visualizing. Do not simply remove or hide metrics to achieve "cleanliness." Instead, think like a Data Scientist: replace plain numbers with the most effective, clean visual representations (e.g., sparklines, micro-charts, trendlines) that provide instant insight.

### R3. Pattern Recognition & Sub-Tabbing
Identify the common patterns and domain-specific metrics both leaders look at. To eliminate the current issue of excessive vertical scrolling, you must organize these visualizations into multiple focused sub-tabs within the main views. The leaders are completely fine with clicking through sub-tabs if it keeps the domain data clean and scroll-free.

### R4. Local Testing Only (No Git Pushes)
Do not automatically commit or push any changes to the git repository. All UI and structural changes must be run and reviewed on localhost first to prevent breaking the live dashboard or losing existing efforts.

## Acceptance Criteria

### Visualization Quality
- [ ] The raw Excel data structure has been explicitly analyzed and documented by an agent.
- [ ] Plain number metrics have been intelligently upgraded to rich, clean data visualizations (charts/sparklines) without removing underlying data.
- [ ] Vertical scrolling is largely eliminated by breaking long pages into logical, clickable sub-tabs based on leader patterns.
- [ ] An agent-as-judge script confirms that data density is maintained while scroll-depth is reduced.
- [ ] No `git push` commands were executed during the process.
