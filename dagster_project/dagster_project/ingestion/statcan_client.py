from pathlib import Path
import requests

BOC_CPI_URL = (
    "https://www.bankofcanada.ca/valet/observations/v41690973/json"
)

def download_cpi(output_dir: Path) -> Path:
    output_dir.mkdir(parent=True, exist_ok= True)

    output_path = output_dir / "bank_of_canada_cpi.json"
    temporary_path = output_dir / "bank_of_canada_cpi.json.tmp"

    response = requests.get(
        BOC_CPI_URL,
        params={
            "start-date": "2000-01-01",         
        },
        timeout=(10,60),
    )

    response.raise_for_status()

    if not response.content:
        raise ValueError("Bank of Canada returned empty response")

    temporary_path.write_bytes(response.content)
    temporary_path.replace(output_path)

    return output_path