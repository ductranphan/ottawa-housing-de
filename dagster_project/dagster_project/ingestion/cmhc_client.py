from pathlib import Path
from zipfile import BadZipFile, ZipFile, is_zipfile

import requests


TABLE_ID = "34100133"
DOWNLOAD_URL = f"https://www150.statcan.gc.ca/n1/tbl/csv/{TABLE_ID}-eng.zip"


def _valid_cached_zip(path: Path) -> bool:
    if not is_zipfile(path):
        return False
    try:
        with ZipFile(path) as archive:
            return archive.testzip() is None and f"{TABLE_ID}.csv" in archive.namelist()
    except (OSError, BadZipFile):
        return False


def download_cmhc_rents(output_dir: Path) -> Path:
    """Download the CMHC-published rental table and save the raw ZIP."""
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{TABLE_ID}-eng.zip"
    temporary_path = output_dir / f"{TABLE_ID}-eng.zip.tmp"

    headers = {
        "Accept": "application/zip",
        "User-Agent": "ottawa-housing-affordability-tracker/1.0",
    }
    try:
        data_response = requests.get(
            DOWNLOAD_URL,
            headers=headers,
            timeout=(10, 120),
        )
        data_response.raise_for_status()
    except requests.RequestException:
        if _valid_cached_zip(output_path):
            return output_path
        raise

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
