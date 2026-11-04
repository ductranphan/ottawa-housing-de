from pathlib import Path
import requests

BOC_CPI_URL = (
    "https://www.bankofcanada.ca/valet/observations/V41690973/json"
)

def download_cpi(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok= True)

    output_path = output_dir / "bank_of_canada_cpi.json"
    temporary_path = output_dir / "bank_of_canada_cpi.json.tmp"

    response = requests.get(
        BOC_CPI_URL,
        params={
            "start_date": "2000-01-01",         
        },
        timeout=(10,60),
    )

    print(response.url)
    print(response.text[:500])

    response.raise_for_status()

    if not response.content:
        raise ValueError("Bank of Canada returned empty response")

    temporary_path.write_bytes(response.content)
    temporary_path.replace(output_path)

    return output_path

if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[3]
    output_dir = repo_root / "data" / "raw" / "bank_of_canada" / "cpi"

    saved_path = download_cpi(output_dir)
    print(f"Saved CPI data to: {saved_path}")