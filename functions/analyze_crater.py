import numpy as np
from functions.geo_utils import circle_mask
from functions.calc_slope import calculate_slope_map


def analyze_crater(dem_data, meta_data, lon0, lat0, radius):
    if np.ma.is_masked(dem_data):
        z = dem_data.filled(np.nan)
    else:
        z = np.asarray(dem_data, dtype=float)

    mask = circle_mask(meta_data, lon0, lat0, radius)
    valid = mask & np.isfinite(z)
    if not np.any(valid):
        raise ValueError("No pixel inside the crater")

    inside = z[valid]
    z_floor = float(inside.min())
    z_rim = float(inside.max())
    max_depth = z_rim - z_floor

    slope = calculate_slope_map(dem_data, meta_data)
    max_slope = float(np.nanmax(slope[valid]))

    return {
        'z_floor': z_floor,
        'z_rim': z_rim,
        'max_depth': max_depth,
        'max_slope': max_slope,
        'n_pixels': int(valid.sum()),
    }