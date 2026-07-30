"""
fcrm.data.geospatial_loader
---------------------------
Geospatial processing layer for mapping asset Latitude/Longitude
to high-resolution hazard severities (Flash Flood, Cyclone, Landslide).
"""

import json
from pathlib import Path
from typing import Tuple

import numpy as np
import zarr

_HAZARD_ARRAY_PATH = Path(__file__).parent.parent.parent.parent / "climate_risk_modelling" / "testing" / "datasets" / "hazard_array.zarr"
_HAZARD_META_PATH = Path(__file__).parent.parent.parent.parent / "climate_risk_modelling" / "testing" / "datasets" / "hazard_meta.json"

# Global cache for zarr array and metadata
_zarr_array = None
_meta = None

def _load_meta():
    global _meta
    if _meta is None:
        if not _HAZARD_META_PATH.exists():
            return None
        with open(_HAZARD_META_PATH, "r") as f:
            _meta = json.load(f)
    return _meta

def _load_zarr():
    global _zarr_array
    if _zarr_array is None:
        if not _HAZARD_ARRAY_PATH.exists():
            return None
        _zarr_array = zarr.open(str(_HAZARD_ARRAY_PATH), mode="r")
    return _zarr_array

def get_geospatial_risk(lat: float, lon: float) -> Tuple[float, float]:
    """
    Look up local physical hazard risk for a specific geographic coordinate.
    
    If the coordinate is outside the Zarr bounding box (e.g., outside India), 
    or if the datasets are missing, it returns a safe baseline (0.0, 0.0).

    The array contains 3 hazard layers (Flash Flood, Cyclone, Landslide).
    The last dimension holds [severity_score, damage_probability].
    
    We average across the 3 hazard layers to compute the localized anomaly.

    Parameters
    ----------
    lat : float
        Latitude.
    lon : float
        Longitude.

    Returns
    -------
    Tuple[float, float]
        (mean_severity_score, mean_damage_probability)
    """
    meta = _load_meta()
    z_arr = _load_zarr()

    # Fallback if datasets don't exist
    if meta is None or z_arr is None:
        return 0.0, 0.0

    # Boundary checks
    if not (meta["lat_min"] <= lat <= meta["lat_max"]):
        return 0.0, 0.0
    if not (meta["lon_min"] <= lon <= meta["lon_max"]):
        return 0.0, 0.0

    # Calculate index
    lat_idx = int((lat - meta["lat_min"]) / meta["resolution"])
    lon_idx = int((lon - meta["lon_min"]) / meta["resolution"])

    # Ensure indices do not exceed bounds (edge case handling)
    lat_idx = min(lat_idx, z_arr.shape[0] - 1)
    lon_idx = min(lon_idx, z_arr.shape[1] - 1)

    # Extract multi-hazard vector at [lat, lon, :, :]
    # Shape of vector: (3, 2) -> 3 hazards, 2 properties [severity, probability]
    hazard_data = z_arr[lat_idx, lon_idx, :, :]
    
    # Compute mean across hazards
    mean_severity = float(np.mean(hazard_data[:, 0]))
    mean_probability = float(np.mean(hazard_data[:, 1]))

    return mean_severity, mean_probability
