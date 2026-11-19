# Ottawa Student Housing Affordability Tracker

## Purpose

The Ottawa Student Housing Affordability Tracker is a reproducible data platform for analyzing the relationship between Ottawa-area rent, inflation, and income.

The project demonstrates the following data engineering practices:

- API and file-based ingestion
- Dagster orchestration
- Pandera DataFrame validation
- Parquet-based bronze storage
- dbt staging, intermediate, and mart models
- DuckDB analytics
- Python and SQL testing
- Dockerized execution
- GitHub Actions CI

## Architecture

```text
Bank of Canada CPI API ─────┐
CMHC rental data ───────────┼──> Dagster ──> raw files ──> Pandera ──> bronze Parquet
Statistics Canada income ──┘

bronze Parquet ──> dbt staging ──> dbt intermediate ──> dbt mart ──> DuckDB
```

This is a hybrid ETL/ELT design:

- Dagster extracts source data and performs source-specific cleaning and validation before creating bronze Parquet files.
- dbt performs warehouse transformations inside DuckDB.
- The final analytical model is created in the warehouse layer.

## Repository structure

```text
ottawa-housing-de/
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .github/
│   └── workflows/
│       └── ci.yml
├── ELT/
│   └── ELT_development.md
├── dagster_project/
│   ├── requirements.txt
│   └── dagster_project/
│       ├── assets/
│       ├── ingestion/
│       └── definitions.py
├── dbt_project/
│   ├── dbt_project.yml
│   ├── profiles.yml
│   ├── models/
│   │   ├── staging/
│   │   ├── intermediate/
│   │   └── marts/
│   └── tests/
├── data/
│   ├── raw/
│   ├── bronze/
│   └── warehouse/
└── tests/
```

## Source data

### Bank of Canada CPI

Client:

```text
dagster_project/dagster_project/ingestion/bankcan_client.py
```

Source:

```text
Bank of Canada Valet API
Series: V41690973
```

Raw output:

```text
data/raw/bank_of_canada/cpi/bank_of_canada_cpi.json
```

The source contains monthly Canadian CPI observations beginning in 2000.

### CMHC rental data

Client:

```text
dagster_project/dagster_project/ingestion/cmhc_client.py
```

Source:

```text
CMHC Rental Market data
StatCan table: 34100133
```

Raw output:

```text
data/raw/cmhc/rental_market/34100133-eng.zip
```

The transformation filters to:

- Ottawa-Gatineau, Ontario part
- Dollar measurements
- Rental structure types
- Rental unit types

### Statistics Canada income

Client:

```text
dagster_project/dagster_project/ingestion/income_client.py
```

Source:

```text
Statistics Canada table: 11100238
```

Raw output:

```text
data/raw/statcan/income/11100238-eng.zip
```

The transformation filters to:

- Ottawa-Gatineau, Ontario/Quebec
- After-tax income
- Median income
- 2024 constant dollars

The income measure is not student-specific.

## Dagster ingestion

Dagster asset definitions are located in:

```text
dagster_project/dagster_project/assets/
```

The registered assets are:

```text
bank_of_canada_cpi_bronze
cmhc_rental_market_bronze
statcan_income_bronze
```

They are registered in:

```text
dagster_project/dagster_project/definitions.py
```

Each asset:

1. Creates the required raw-data directory.
2. Calls its source client.
3. Reads the raw response.
4. Runs the source-specific bronze transformation.
5. Validates the resulting DataFrame with Pandera.
6. Writes a Parquet file.
7. Logs source metadata, row count, and output path.

The three source assets are independent and can run in parallel.

## Bronze transformations and validation

### CPI bronze

Transformation:

```text
dagster_project/dagster_project/ingestion/bronze_cpi.py
```

Output:

```text
data/bronze/bank_of_canada/cpi/cpi.parquet
```

Important columns:

```text
reference_date
cpi_value
series_id
source
```

Pandera validates that:

- Dates are non-null and unique.
- CPI values are greater than zero.
- The series ID is `V41690973`.
- The source is `bank_of_canada`.
- The DataFrame has the expected schema.

### CMHC bronze

Transformation:

```text
dagster_project/dagster_project/ingestion/bronze_cmhc.py
```

Output:

```text
data/bronze/cmhc/rental_market/rents.parquet
```

Important columns:

```text
reference_year
geography
structure_type
unit_type
rent_value
vector
source
```

Pandera validates that:

- Years are valid.
- Geography, structure type, and unit type are present.
- Rent values are greater than zero.
- The source is `cmhc`.
- The expected columns are present.

### Income bronze

Transformation:

```text
dagster_project/dagster_project/ingestion/bronze_income.py
```

Output:

```text
data/bronze/statcan/income/income.parquet
```

Important columns:

```text
reference_year
geography
income_concept
statistic
income_value
unit
vector
source
```

Pandera validates that:

- Years are valid.
- The required income dimensions are present.
- Income values are non-negative.
- The source is `statcan`.
- The DataFrame has the expected schema.

## dbt models

The dbt project is located at:

```text
dbt_project/
```

The DuckDB profile is configured in:

```text
dbt_project/profiles.yml
```

The warehouse database is:

```text
data/warehouse/ottawa_housing.duckdb
```

### Staging models

Files:

```text
dbt_project/models/staging/stg_cpi.sql
dbt_project/models/staging/stg_cmhc_rents.sql
dbt_project/models/staging/stg_income.sql
```

The staging models read bronze Parquet files using DuckDB `read_parquet()`. Their main responsibilities are:

- Selecting required columns
- Applying consistent SQL data types
- Creating stable dbt relations for downstream models

### Annual CPI model

File:

```text
dbt_project/models/intermediate/int_annual_cpi.sql
```

This model aggregates monthly CPI into annual average CPI:

```text
monthly CPI observations
        ↓
group by calendar year
        ↓
annual average CPI
```

Output columns:

```text
reference_year
annual_average_cpi
```

### Housing affordability mart

File:

```text
dbt_project/models/marts/mart_housing_affordability.sql
```

The mart joins annual rent, CPI, and income by year.

Output columns include:

```text
reference_year
geography
structure_type
unit_type
rent_value
annual_average_cpi
income_geography
annual_median_after_tax_income
annual_rent
rent_growth_percent
cpi_growth_percent
rent_in_2002_cpi_dollars
rent_burden_percent
```

Key calculations:

```text
annual_rent = monthly rent × 12
```

```text
rent_growth_percent =
    (current rent - previous rent) / previous rent × 100
```

```text
cpi_growth_percent =
    (current CPI - previous CPI) / previous CPI × 100
```

```text
rent_in_2002_cpi_dollars =
    rent / annual average CPI × 100
```

```text
rent_burden_percent =
    annual rent / annual median after-tax income × 100
```

The approximate mart grain is:

```text
reference_year
+ rent geography
+ structure type
+ unit type
```

## Data limitations

The CMHC rental geography is:

```text
Ottawa-Gatineau, Ontario part
```

The income geography is:

```text
Ottawa-Gatineau, Ontario/Quebec
```

These labels do not match exactly. The mart therefore joins the datasets by year and preserves both geography fields:

```text
geography
income_geography
```

This is an approximation and should be documented as a limitation of the pipeline.

The income measure is also not student-specific. The rent-burden metric represents affordability relative to median after-tax income for the selected geography, not affordability for a typical student.

## Testing

### Python tests

Python tests are located in:

```text
tests/
```

They test:

- Bronze transformation behavior
- Parquet output creation
- Data type and column expectations
- Rejection of invalid values

Run locally with:

```powershell
pytest
```

### Pandera validation

Pandera validates source DataFrames before Parquet output is written. This prevents invalid source data from entering the bronze layer.

### dbt schema tests

Schema tests are defined in:

```text
dbt_project/models/schema.yml
```

They cover:

- Not-null constraints
- Unique dates and years
- Accepted source values
- Required mart fields

### dbt singular tests

Files:

```text
dbt_project/tests/assert_positive_values.sql
dbt_project/tests/assert_mart_grain_unique.sql
```

The positive-values test rejects non-positive CPI, rent, and income values.

The grain test returns duplicate mart keys if the expected mart grain is violated. A dbt singular test passes when it returns zero rows.

## Docker execution

The Docker files are located at the repository root:

```text
Dockerfile
docker-compose.yml
.dockerignore
```

The Docker image uses Python 3.11 and installs dependencies from:

```text
dagster_project/requirements.txt
```

The repository root is mounted as `/app` inside the image. The local `data/` directory is mounted as:

```text
./data:/app/data
```

This keeps raw files, bronze Parquet files, and the DuckDB database outside the temporary containers.

Build the image:

```powershell
docker compose build
```

Run Dagster ingestion:

```powershell
docker compose run --rm dagster
```

Run Python tests:

```powershell
docker compose run --rm dbt pytest
```

Run dbt models and tests:

```powershell
docker compose run --rm dbt
```

The expected execution order is:

```text
Dagster ingestion
        ↓
data/bronze/*.parquet
        ↓
dbt build
        ↓
data/warehouse/ottawa_housing.duckdb
```

## GitHub Actions CI

The workflow is located at:

```text
.github/workflows/ci.yml
```

It runs on pushes and pull requests targeting `main`. It can also be started manually with `workflow_dispatch`.

The CI steps are:

1. Check out the repository.
2. Build the Docker image.
3. Run Dagster ingestion.
4. Run pytest.
5. Run dbt models and tests.

This verifies that the project can be executed in a clean Linux container rather than only in the local development environment.

The external source downloads may be affected by rate limits or access restrictions. Cached official raw ZIP files can be used when the source service returns an HTTP 403 response. A future improvement would be to separate live ingestion tests from fixture-based CI tests.

## Pipeline status

Completed:

- Source ingestion clients
- Dagster assets
- Pandera bronze validation
- Bronze Parquet outputs
- dbt staging models
- Annual CPI intermediate model
- Housing affordability mart
- Python tests
- dbt schema and singular tests
- Docker execution
- GitHub Actions CI

The data engineering pipeline is complete through the DuckDB mart and CI validation stages.
