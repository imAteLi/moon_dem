import numpy as np
from scipy.ndimage import map_coordinates

from functions.geo_utils import geo_to_pixel, pixel_to_geo, surface_distance, bearing_between, geo_offset


def _sample_elevation(z, rows, cols):
    return map_coordinates(z, [rows, cols], order=1, mode='nearest')


def line_of_sight(dem_data, meta_data, observer, target, n_samples=None, clearance=0.0):
    if np.ma.is_masked(dem_data):
        z = dem_data.filled(np.nan)
    else:
        z = np.asarray(dem_data, dtype=float)

    lon_o, lat_o = observer
    lon_t, lat_t = target

    r_o, c_o = geo_to_pixel(meta_data, lon_o, lat_o, as_int=False)
    r_t, c_t = geo_to_pixel(meta_data, lon_t, lat_t, as_int=False)

    if n_samples is None:
        pix_len = np.hypot(r_t - r_o, c_t - c_o)
        n_samples = max(int(np.ceil(pix_len)) * 2, 50)

    rows = np.linspace(r_o, r_t, n_samples)
    cols = np.linspace(c_o, c_t, n_samples)

    elev = _sample_elevation(z, rows, cols)
    lons, lats = pixel_to_geo(meta_data, rows, cols)
    lons = np.asarray(lons)
    lats = np.asarray(lats)

    dist_from_obs = surface_distance(meta_data, lon_o, lat_o, lons, lats)
    dist_to_target = surface_distance(meta_data, lons, lats, lon_t, lat_t)

    total = dist_from_obs[-1]
    if total <= 0:
        raise ValueError("Negative distance")

    t = dist_from_obs / total
    z_los = elev[0] + t * (elev[-1] - elev[0])

    poke = elev - z_los

    interior = np.arange(1, n_samples - 1)
    has_nodata = bool(np.isnan(elev[interior]).any())

    blocked = False
    obstacle_idx = None
    obstacle_dist_to_bottom = None
    obstacle_lonlat = None

    if interior.size > 0:
        poke_in = poke[interior]
        k = interior[np.nanargmax(poke_in)]
        if np.isfinite(poke[k]) and poke[k] > clearance:
            blocked = True
            obstacle_idx = int(k)
            obstacle_dist_to_bottom = float(dist_to_target[k])
            obstacle_lonlat = (float(lons[k]), float(lats[k]))

    return {
        'blocked': blocked,
        'obstacle_idx': obstacle_idx,
        'obstacle_dist_to_bottom': obstacle_dist_to_bottom,
        'obstacle_lonlat': obstacle_lonlat,
        'has_nodata': has_nodata,
        'profile': {
            'dist_from_obs': dist_from_obs,
            'dist_to_target': dist_to_target,
            'elev': elev,
            'z_los': z_los,
            'lons': lons,
            'lats': lats,
        },
    }


def traverse_edges(dem_data, meta_data, center, point_a, radius, step_deg=10.0, clearance=0.0):
    lon0, lat0 = center
    lon_a, lat_a = point_a
    start_bearing = float(bearing_between(meta_data, lon0, lat0, lon_a, lat_a))

    n = int(round(360.0 / step_deg))
    results = []
    for i in range(n):
        bearing = (start_bearing + i * step_deg) % 360.0
        lon_e, lat_e = geo_offset(meta_data, lon0, lat0, radius, bearing)
        los = line_of_sight(dem_data, meta_data, (lon_e, lat_e), (lon0, lat0), clearance=clearance)
        results.append({
            'bearing': bearing,
            'edge_lonlat': (lon_e, lat_e),
            'blocked': los['blocked'],
            'obstacle_dist_to_bottom': los['obstacle_dist_to_bottom'],
        })

    return results