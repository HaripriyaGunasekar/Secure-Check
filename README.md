# Secure-Check
 A Streamlit dashboard that analyses police traffic stop data to uncover patterns in violations, vehicle types, locations, and demographics.
SecureCheck – End-to-End Project Documentation

SecureCheck is an nteractive dashboard developed for analysing police traffic stop logs. 
The project focuses on the 2020 dataset, aiming to provide insights, summaries, and incident-level reporting. 
Below is a complete theoretical walkthrough of the project from start to finish.

1. Data Cleaning and Preparation (Visual Studios)
- The raw dataset was obtained in Excel format, containing traffic stop data such as stop time, stop date, driver demographics, violation type, and outcomes.
- Cleaning tasks performed:
  - Replaced missing or null values in key columns like driver_gender, vehicle_number, stop_outcome. Fill missing values
  - Standardised gender values (e.g. converting "Male" and "M" into a consistent format).
  - Format date & time, Combined date and time fields for better temporal analysis.
  - Converted stop duration into integers for consistent numeric operations.
  - Ensured all categorical fields were consistently formatted. Clean age values and Convert Booleans
- After cleaning, the data was uploaded into a PostgreSQL database using Python libraries (pandas and psycopg2).

2. Database Setup (PostgreSQL)
- A relational database schema was created with a table called police_logs.
- This table holds all structured traffic stop data for querying.
- pgAdmin was used to visually inspect the database and test queries.

3. Python Backend Logic
- The backend was built using a Python script with defined functions for:
  - Database connectivity.
  - Executing parameterised SQL queries.
  - Defining reusable queries like arrest ratios, demographic breakdowns, drug-related incidents, and country-based analysis.
- Plotly was used for building visual charts such as gauges, choropleth maps, and bar graphs.

4. Streamlit Frontend Dashboard
- Streamlit was used to build the dashboard interface.
- Key sections of the dashboard include:
  - Gauge Indicators: Visual KPIs such as arrest ratio, female drivers ratio, drug stops, juvenile drivers, verbal warnings, and short stops.
  - Country Analysis: Displays country-wise driver data both as a choropleth map and as a sortable table.
  - Incident Reports: Allows users to select a vehicle number and displays a summary of the latest traffic stop involving that vehicle.
  - Advanced Analysis: Users can select from a list of analysis cards, which trigger dynamic queries and display their results.
  - Blog Section: A newspaper-style awareness article on drug-related offences in India was created and presented within the app.
  - Helpline Section: National safety helpline numbers were included in a collapsible section.

5. Advanced Visuals and Awareness Article
- A realistic awareness article was written and formatted like a newspaper column.
- This article was also exported as a PDF.
- File downloads for PDF, PNG, and CSV were made available inside the dashboard, allowing users to download insights, reports, and images.

6. Download Functionality
- Streamlit's file handling was used to allow users to download PDF (awareness article), CSV (dataset), and PNG (article preview) files.
- These were displayed with icons, arranged in a single row for easy access.

7. Testing and Error Handling
- The dashboard was tested for blank inputs, failed queries, and missing data.
- Helpful error messages and information blocks were used to guide the user.

8. Applications and Tools Used
- Visual Studios
- PostgreSQL for data storage
- Python (pandas, psycopg2) for backend logic
- Streamlit for frontend dashboard
- Plotly for interactive charts
- HTML/CSS for UI styling within markdown blocks

9. Final Outcome
- The SecureCheck dashboard helps users explore and understand 2020 traffic stop data.
- It allows interactive exploration of violations, driver demographics, outcomes, and country-wise distribution.
- It also acts as an educational platform with awareness content and helpline numbers.

This project demonstrates the end-to-end process of data cleaning, storage, visualisation, and public reporting using modern data science tools and techniques.
