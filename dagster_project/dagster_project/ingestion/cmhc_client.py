from pathlib import Path

import requests


TABLE_ID = "34100133"
WDS_URL = (
    "https://www150.statcan.gc.ca/t1/wds/rest/"
    f"getFullTableDownloadCSV/{TABLE_ID}/en"
)


def download_cmhc_rents(output_dir: Path) -> Path:
    """Download the CMHC-published rental table and save the raw ZIP."""
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{TABLE_ID}-eng.zip"
    temporary_path = output_dir / f"{TABLE_ID}-eng.zip.tmp"

    metadata_response = requests.get(WDS_URL, timeout=(10, 60))
    metadata_response.raise_for_status()
    metadata = metadata_response.json()

    if metadata.get("status") != "SUCCESS":
        raise RuntimeError(f"CMHC table lookup failed: {metadata}")

    download_url = metadata.get("object")
    if not isinstance(download_url, str):
        raise ValueError("CMHC response did not contain a download URL")

    data_response = requests.get(download_url, timeout=(10, 120))
    data_response.raise_for_status()

    if not data_response.content:
        raise ValueError("CMHC returned an empty download")

    temporary_path.write_bytes(data_response.content)
    temporary_path.replace(output_path)

    return output_path


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[3]
    output_dir = repo_root / "data" / "raw" / "cmhc" / "rental_market"

    saved_path = download_cmhc_rents(output_dir)
    print(f"Saved CMHC rental data to: {saved_path}")