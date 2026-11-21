import csv
import gzip
import io
from pathlib import Path

import duckdb
import httpx


def harvest_housing():
    print("Harvesting official Observatoire de l'Habitat retrospective datasets...")
    client = httpx.Client(timeout=30.0, follow_redirects=True)
    con = duckdb.connect()
    con.execute("LOAD spatial;")

    files = [
        (
            "APARTMENT",
            "https://download.data.public.lu/resources/prix-annonces-des-logements-par-commune/20260326-095804/vente-appartement-2010-2025.xlsx",
        ),
        (
            "HOUSE",
            "https://download.data.public.lu/resources/prix-annonces-des-logements-par-commune/20260326-095818/vente-maison-2010-2025.xlsx",
        ),
    ]

    records = []

    for ptype, url in files:
        tmp_name = f"tmp_{ptype}.xlsx"
        print(f"Downloading {ptype} from {url}...")
        r = client.get(url)
        Path(tmp_name).write_bytes(r.content)

        sheets = con.execute(f"SELECT * FROM st_read_meta('{tmp_name}')").fetchall()
        sheet_info = sheets[0][3] if sheets and len(sheets[0]) > 3 else []
        for s in sheet_info:
            year = s.get("name")
            if not year or not year.isdigit():
                continue
            try:
                q_sql = (
                    f"SELECT Field3, Field4, Field5, Field6 FROM "
                    f"st_read('{tmp_name}', layer='{year}') WHERE Field3 IS NOT NULL"
                )
                rows = con.execute(q_sql).fetchall()
                for r_commune, r_offers, _r_price, r_m2 in rows:
                    commune = str(r_commune).strip()
                    if (
                        not commune
                        or commune.startswith("Précaution")
                        or commune.startswith("-")
                        or commune == "Commune"
                        or commune == "Total"
                    ):
                        continue

                    # Parse offers
                    offers_count = 1
                    try:
                        if r_offers and str(r_offers).isdigit():
                            offers_count = int(r_offers)
                    except Exception:
                        pass

                    # Parse price per m2
                    price_m2 = None
                    try:
                        if r_m2 and r_m2 != "*":
                            price_m2 = round(float(str(r_m2).replace(",", ".")), 2)
                    except Exception:
                        pass

                    if price_m2 and 1000 <= price_m2 <= 30000:
                        records.append(
                            {
                                "commune_name": commune,
                                "property_type": ptype,
                                "reference_period": year,
                                "price_eur_m2": price_m2,
                                "transactions_count": max(1, offers_count),
                            }
                        )
            except Exception as e:
                print(f"  Error on sheet {year}: {e}")

        if Path(tmp_name).exists():
            Path(tmp_name).unlink()

    print(
        f"===> Extracted {len(records)} commune-year official "
        "observations from Observatoire de l'Habitat! <==="
    )

    # Write to data/bronze/housing_observatoire/latest.csv.gz
    csv_buf = io.StringIO()
    writer = csv.DictWriter(
        csv_buf,
        fieldnames=[
            "commune_name",
            "property_type",
            "reference_period",
            "price_eur_m2",
            "transactions_count",
        ],
    )
    writer.writeheader()
    writer.writerows(records)

    raw_csv = csv_buf.getvalue().encode("utf-8")
    out_dir = Path("data/bronze/housing_observatoire")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "latest.csv.gz").write_bytes(gzip.compress(raw_csv))
    print(f"Wrote {len(records)} rows to data/bronze/housing_observatoire/latest.csv.gz")


if __name__ == "__main__":
    harvest_housing()
