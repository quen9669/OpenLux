import gzip
import json
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path

import httpx

from openlux.core.parsers import cita_datex2


def harvest():
    client = httpx.Client(timeout=15.0, headers={"User-Agent": "OpenLuxHub/1.0"})
    now_iso = datetime.now(UTC).isoformat()

    # 1. TRAFFIC CITA
    print("Fetching live traffic situations from CITA DATEX II...")
    r_traf = client.get("https://www.cita.lu/info_trafic/datex/situationrecord")
    recs_traf = cita_datex2(r_traf.content)
    # Deduplicate traffic events
    traf_seen = set()
    dedup_traf = []
    for r in recs_traf:
        if r["event_id"] not in traf_seen:
            traf_seen.add(r["event_id"])
            dedup_traf.append(r)

    try:
        r_vdl_traf = client.get(
            "https://maps.vdl.lu/arcgis/rest/services/DYNDATA/TRAFIC_INFO/FeatureServer/0/query?where=1%3D1&outFields=*&f=json"
        )
        vdl_features = r_vdl_traf.json().get("features", [])
        for f in vdl_features:
            attrs = f.get("attributes", {})
            geom = f.get("geometry", {})
            eid = f"VDL_TRAF_{attrs.get('OBJECTID', '0')}"
            if eid not in traf_seen:
                traf_seen.add(eid)
                dedup_traf.append(
                    {
                        "event_id": eid,
                        "road_name": attrs.get("RUE") or attrs.get("LIEU") or "Voirie VDL",
                        "situation_type": "MunicipalTrafficEvent",
                        "start_time": now_iso,
                        "lat": geom.get("y") or 49.6117,
                        "lon": geom.get("x") or 6.1319,
                        "comment": attrs.get("DESCRIPTION")
                        or attrs.get("INFOTEXT")
                        or "Perturbation urbaine Ville de Luxembourg",
                    }
                )
    except Exception as e:
        print("VDL traffic error:", e)

    print(f"Total live traffic events: {len(dedup_traf)}")
    out_dir_traf = Path("data/bronze/traffic_cita_datex2")
    out_dir_traf.mkdir(parents=True, exist_ok=True)
    (out_dir_traf / "latest.json.gz").write_bytes(
        gzip.compress(json.dumps(dedup_traf, ensure_ascii=False).encode("utf-8"))
    )

    # 2. ROADWORKS CITA (Nationaux)
    print("\nFetching national roadworks from CITA...")
    r_chan_act = client.get("https://www.cita.lu/info_trafic/datex/chantierActuelDatex.xml")
    root_act = ET.fromstring(r_chan_act.content)
    chan_recs = []
    seen_rw = set()

    for elem in root_act.iter():
        if elem.tag.endswith("situationRecord"):
            rec_id = elem.attrib.get("id") or "UNKNOWN"
            if rec_id in seen_rw:
                continue
            seen_rw.add(rec_id)

            road_el = next((e for e in elem.iter() if e.tag.endswith("roadName")), None)
            lat_el = next((e for e in elem.iter() if e.tag.endswith("latitude")), None)
            lon_el = next((e for e in elem.iter() if e.tag.endswith("longitude")), None)
            time_el = next((e for e in elem.iter() if "CreationTime" in e.tag), None)
            val_el = next((e for e in elem.iter() if e.tag.endswith("value")), None)
            comm_el = next((e for e in elem.iter() if e.tag.endswith("town")), None)

            r_name = (
                road_el.text.strip() if road_el is not None and road_el.text else "Réseau National"
            )
            s_time = time_el.text.strip() if time_el is not None and time_el.text else now_iso
            r_lat = float(lat_el.text.strip()) if lat_el is not None and lat_el.text else 49.6117
            r_lon = float(lon_el.text.strip()) if lon_el is not None and lon_el.text else 6.1319
            r_comm = (
                val_el.text.strip()
                if val_el is not None and val_el.text
                else "Travaux de réfection de chaussée PCH"
            )
            commune = comm_el.text.strip() if comm_el is not None and comm_el.text else "Luxembourg"

            chan_recs.append(
                {
                    "work_id": f"CITA_RW_{rec_id}",
                    "road_name": r_name,
                    "start_date": s_time,
                    "end_date": "",
                    "impact_level": "MODERATE",
                    "title": r_comm[:140],
                    "observed_at": now_iso,
                    "lat": r_lat,
                    "lon": r_lon,
                    "commune_name": commune,
                }
            )

    print(f"Total national roadworks: {len(chan_recs)}")
    out_dir_rw_cita = Path("data/bronze/roadworks_cita")
    out_dir_rw_cita.mkdir(parents=True, exist_ok=True)
    (out_dir_rw_cita / "latest.json.gz").write_bytes(
        gzip.compress(json.dumps(chan_recs, ensure_ascii=False).encode("utf-8"))
    )

    # 3. ROADWORKS VDL (Ville de Luxembourg)
    print("\nFetching municipal roadworks from Ville de Luxembourg ArcGIS REST...")
    vdl_recs = []
    seen_vdl = set()
    try:
        r_vdl_1 = client.get(
            "https://maps.vdl.lu/arcgis/rest/services/DYNDATA/TRAFIC_INFO/FeatureServer/1/query?where=1%3D1&outFields=*&f=json"
        )
        for f in r_vdl_1.json().get("features", []):
            attrs = f.get("attributes", {})
            geom = f.get("geometry", {})
            wid = f"VDL_RW_{attrs.get('OBJECTID', '0')}"
            if wid in seen_vdl:
                continue
            seen_vdl.add(wid)
            vdl_recs.append(
                {
                    "work_id": wid,
                    "road_name": attrs.get("RUE") or attrs.get("LIEU") or "Voirie communale",
                    "start_date": attrs.get("DATE_DEBUT") or now_iso,
                    "end_date": attrs.get("DATE_FIN") or "",
                    "impact_level": "HIGH" if "fermeture" in str(attrs).lower() else "MODERATE",
                    "title": (
                        attrs.get("DESCRIPTION")
                        or attrs.get("REMARQUE")
                        or "Chantier communal de voirie VDL"
                    )[:140],
                    "observed_at": now_iso,
                    "lat": geom.get("y") or 49.6117,
                    "lon": geom.get("x") or 6.1319,
                    "commune_name": "Luxembourg",
                }
            )
    except Exception as e:
        print("VDL layer 1 error:", e)

    try:
        r_vdl_5 = client.get(
            "https://maps.vdl.lu/arcgis/rest/services/DYNDATA/TRAFIC_INFO/FeatureServer/5/query?where=1%3D1&outFields=*&f=json"
        )
        for f in r_vdl_5.json().get("features", []):
            attrs = f.get("attributes", {})
            geom = f.get("geometry", {})
            wid = f"VDL_FOUILLE_{attrs.get('OBJECTID', '0')}"
            if wid in seen_vdl:
                continue
            seen_vdl.add(wid)
            vdl_recs.append(
                {
                    "work_id": wid,
                    "road_name": attrs.get("RUE") or attrs.get("LIEU") or "Voirie communale",
                    "start_date": attrs.get("DATE_DEBUT") or now_iso,
                    "end_date": attrs.get("DATE_FIN") or "",
                    "impact_level": "LOW",
                    "title": (
                        attrs.get("DESCRIPTION")
                        or attrs.get("REMARQUE")
                        or "Fouilles et interventions réseaux souterrains"
                    )[:140],
                    "observed_at": now_iso,
                    "lat": geom.get("y") or 49.6117,
                    "lon": geom.get("x") or 6.1319,
                    "commune_name": "Luxembourg",
                }
            )
    except Exception as e:
        print("VDL layer 5 error:", e)

    print(f"Total municipal roadworks/fouilles (VDL): {len(vdl_recs)}")
    out_dir_rw_vdl = Path("data/bronze/roadworks_vdl")
    out_dir_rw_vdl.mkdir(parents=True, exist_ok=True)
    (out_dir_rw_vdl / "latest.json.gz").write_bytes(
        gzip.compress(json.dumps(vdl_recs, ensure_ascii=False).encode("utf-8"))
    )

    print("\nHarvest completed successfully with deduplication!")


if __name__ == "__main__":
    harvest()
