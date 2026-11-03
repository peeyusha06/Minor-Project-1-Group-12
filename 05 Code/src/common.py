"""Shared paths, config, provenance and geometry helpers for the data pipeline."""
from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import geopandas as gpd
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
MANUAL = ROOT / "data" / "manual"
INTERIM = ROOT / "data" / "interim"
VARIANTS = INTERIM / "variants"
REPORTS = ROOT / "reports"
CONFIG_PATH = ROOT / "config" / "project_decisions.yaml"

STATE_CODE = "27"
GEOGRAPHIES = ("A", "B")
ENSO_INDICES = ("RONI", "ONI_v6")
THANE = 517
PALGHAR_LGD = 681
MUMBAI_CODES = (518, 519)
# Census 2011 sub-district codes of the 8 Thane talukas that formed Palghar district (2014).
PALGHAR_SUBDISTRICTS = ("04157", "04158", "04159", "04160", "04161", "04162", "04163", "04164")

SRC = {
    "census_pca": RAW / "census" / "2011-IndiaStateDistSbDistTwnWrd-0000.xlsx",
    "village_directory": RAW / "census" / "DH_2011_DCHB_Village_Release_2700.xlsx",
    "agcensus_report": RAW / "agriculture" / "agcensus" / "Agriculture_Census_2010-11_Maharashtra_State_Report_Argi.pdf",
    "imd_dir": RAW / "rainfall" / "imd_gridded_0p25_netcdf",
    "oni": RAW / "enso" / "oni.ascii.txt",
    "roni": RAW / "enso" / "RONI.ascii.txt",
    "oni_page": RAW / "enso" / "cpc_oni_v6_episode_table_page.html",
    "roni_page": RAW / "enso" / "cpc_roni_page.html",
    "soi_zip": RAW / "boundaries" / "survey_of_india" / "SOI_OVSF_1M_8_Maharashtra_upto_taluk.zip",
    "datameet_shp": RAW / "boundaries" / "datameet_census2011_districts" / "2011_Dist.shp",
    "icrisat_districts": RAW / "agriculture" / "icrisat_dld" / "icrisat_dld_unapportioned_districts.json",
    "icrisat_landuse": RAW / "agriculture" / "icrisat_dld" / "icrisat_dld_unapportioned_landuse.json",
    "gr_2023_circles": RAW / "validation" / "GR_202311101718225419_drought_1021_revenue_circles_addl_2023.pdf",
    "manifest": RAW / "source_manifest.csv",
    "district_reference": MANUAL / "district_reference.csv",
    "gr_talukas": MANUAL / "gr_declared_talukas_transcribed.csv",
    "gr2018_circles": MANUAL / "gr2018_revenue_circles_transcribed.csv",
    "gr2023_circle_map": MANUAL / "gr2023_circle_district_string_map.csv",
}


def load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def active(cfg: dict, key: str):
    return cfg["decisions"][key]["active"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def rel(path: Path) -> str:
    return str(Path(path).resolve().relative_to(ROOT))


def geo_dir(geo: str) -> Path:
    d = VARIANTS / f"geo_{geo}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def variant_dir(geo: str, index: str) -> Path:
    d = VARIANTS / f"geo_{geo}__{index}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def write_csv(df: pd.DataFrame, path: Path, float_decimals: int = 6) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, float_format=f"%.{float_decimals}f", encoding="utf-8")


def pdftotext(pdf: Path, first: int | None = None, last: int | None = None) -> str:
    cmd = ["pdftotext", "-layout"]
    if first:
        cmd += ["-f", str(first)]
    if last:
        cmd += ["-l", str(last)]
    cmd += [str(pdf), "-"]
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout


def district_ids(geo: str) -> list[int]:
    """Census 2011 district codes 497-531 (35); geography B adds Palghar (681)."""
    ids = list(range(497, 532))
    if geo == "B":
        ids.append(PALGHAR_LGD)
    return ids


def soi_layer(name: str) -> gpd.GeoDataFrame:
    return gpd.read_file(f"zip://{SRC['soi_zip']}!27/MAHARASHTRA_{name}.shp")


def district_polygons(geo: str, source: str) -> gpd.GeoDataFrame:
    """District polygons (EPSG:4326) keyed by district_id for the requested geography.

    survey_of_india: DIST_LGD codes equal Census 2011 codes; geography A dissolves
    Thane (517) and Palghar (681) back into Census-2011 Thane.
    datameet_2011: native Census 2011 polygons; geography B splits Thane using the
    Survey of India Palghar polygon (Palghar = DM Thane intersect SOI Palghar).
    """
    if source == "survey_of_india":
        g = soi_layer("DISTRICT_BDY")[["DIST_LGD", "geometry"]].copy()
        g["district_id"] = g["DIST_LGD"].astype(int)
        g = g.to_crs(4326)
        if geo == "A":
            g.loc[g.district_id == PALGHAR_LGD, "district_id"] = THANE
            g = g.dissolve(by="district_id", as_index=False)[["district_id", "geometry"]]
        return g[["district_id", "geometry"]].sort_values("district_id").reset_index(drop=True)
    if source == "datameet_2011":
        dm = gpd.read_file(SRC["datameet_shp"])
        dm = dm[dm["ST_NM"] == "Maharashtra"].copy()
        dm["district_id"] = dm["censuscode"].astype(int)
        dm = dm[["district_id", "geometry"]].to_crs(4326)
        if geo == "B":
            pal = soi_layer("DISTRICT_BDY").to_crs(4326)
            pal_geom = pal.loc[pal["DIST_LGD"].astype(int) == PALGHAR_LGD, "geometry"].union_all()
            th = dm.loc[dm.district_id == THANE, "geometry"].union_all()
            dm = dm[dm.district_id != THANE]
            extra = gpd.GeoDataFrame({"district_id": [THANE, PALGHAR_LGD],
                                      "geometry": [th.difference(pal_geom), th.intersection(pal_geom)]}, crs=4326)
            dm = pd.concat([dm, extra], ignore_index=True)
        return gpd.GeoDataFrame(dm, crs=4326).sort_values("district_id").reset_index(drop=True)
    raise ValueError(f"unknown boundary source {source}")
