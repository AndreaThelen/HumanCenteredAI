# session_logs

Curated OpenMATB session logs for analysis. **Only the `.csv` files placed here
are analysed** by the notebook and the `matb_analysis` package.

Copy the relevant runs from `../../OpenMATB/sessions/<date>/` into this folder
(flat or keeping the date subfolders — both are found, the search is recursive).
Non-study, pilot, or aborted runs you don't want included should simply be left
out.

The analysis auto-discovers everything here via
`matb_analysis.discovery.find_study_sessions()`, keeps only sessions whose
scenario is under `scenarios/study/`, and segments each into its F1/F2/F3 ×
A/B/C blocks.
