# Data directory

Place the following CSV files in this directory **or** in the workspace root folder
(the default `DATA_DIR` is the workspace root: two levels above `backend/`).

| File | Publisher | Period |
|------|-----------|--------|
| `GTTC_Shortterm_Courses.csv` | GTTC, Govt. of Karnataka (catalogue page unverified) | FY 2018–19 to 2021–22 |
| `GTTC_Number_of_Students_Passed_2019-2021_0.csv` | GTTC, Govt. of Karnataka (catalogue page unverified) | Calendar 2019–2021 |
| `census_2011_ddw_b06_2900_2011.csv` | Registrar General & Census Commissioner, India — [censusindia.gov.in](https://censusindia.gov.in) | Census 2011 |
| `TotalEnrollmentbyLevel_2020-21.csv` | School-education MIS (publisher unverified) | AY 2020–21 |
| `ManagementWiseClasswiseEnrolment2018_2019_1.csv` | Publisher unverified | AY 2018–19 |
| `State_Level_Single_Window_Committee_Industrydetails_2021.csv` | Publisher unverified | FY 2020–21 |

Raw files must **not** be modified. The application reads them exactly as provided.

If a file is missing, the corresponding analytical module will display a
"Dataset not loaded" notice without crashing unrelated modules.
