import numpy as np
from rasterio.transform import rowcol, xy
from pyproj import CRS, Transformer


def meters_per_degree(radius):
    return (np.pi * radius) / 180.0


def compute_meters_per_pixel(meta_data):
    transform = meta_data['transform']
    unit_type = meta_data['units']
    radius = meta_data['radius']
    rows = meta_data['height']

    res_x = abs(transform.a)
    res_y = abs(transform.e)

    if unit_type == 'meters':
        return res_x, res_y

    if unit_type == 'degrees':
        mpd = meters_per_degree(radius)
        mpp_y = res_y * mpd

        row_indices = np.arange(rows)
        latitudes = transform.f + (transform.e * (row_indices + 0.5))
        scale = np.cos(np.deg2rad(latitudes))

        mpp_x = (res_x * mpd * scale)[:, np.newaxis]
        mpp_x = np.clip(mpp_x, 1e-6, None)

        return mpp_x, mpp_y

    raise ValueError(f"Unknown unit: {unit_type}")


def geo_to_pixel(meta_data, lon, lat, as_int=True):
    transform = meta_data['transform']
    op = round if as_int else float
    r, c = rowcol(transform, lon, lat, op=op)
    return r, c


def pixel_to_geo(meta_data, row, col):
    transform = meta_data['transform']
    lon, lat = xy(transform, row, col)
    return lon, lat


def surface_distance(meta_data, lon1, lat1, lon2, lat2):
    radius = meta_data['radius']
    mpd = meters_per_degree(radius)
    mean_lat = np.deg2rad((lat1 + lat2) / 2.0)
    dx = (lon2 - lon1) * mpd * np.cos(mean_lat)
    dy = (lat2 - lat1) * mpd
    return np.hypot(dx, dy)


def build_projected_grid(meta_data, step=1, as_edges=False):
    transform = meta_data['transform']
    unit_type = meta_data['units']
    radius = meta_data['radius']
    height = meta_data['height']
    width = meta_data['width']

    if as_edges:
        n_rows = len(np.arange(0, height, step))
        n_cols = len(np.arange(0, width, step))
        rows = (np.arange(n_rows + 1) - 0.5) * step
        cols = (np.arange(n_cols + 1) - 0.5) * step
    else:
        rows = np.arange(0, height, step)
        cols = np.arange(0, width, step)
    cols_grid, rows_grid = np.meshgrid(cols, rows)

    a, b, c = transform.a, transform.b, transform.c
    d, e, f = transform.d, transform.e, transform.f
    x = c + (a * cols_grid) + (b * rows_grid)
    y = f + (d * cols_grid) + (e * rows_grid)

    if unit_type == 'degrees':
        center_lon = c + (width / 2.0) * a
        center_lat = f + (height / 2.0) * e

        src_crs = CRS.from_dict({
            'proj': 'longlat',
            'a': radius,
            'b': radius,
            'no_defs': True
        })

        proj_crs = CRS.from_dict({
            'proj': 'ortho',
            'lat_0': center_lat,
            'lon_0': center_lon,
            'a': radius,
            'b': radius,
            'units': 'm',
            'no_defs': True
        })

        transformer = Transformer.from_crs(src_crs, proj_crs, always_xy=True)
        x, y = transformer.transform(x, y)

    return x, y


def circle_mask(meta_data, lon0, lat0, radius):
    height = meta_data['height']
    width = meta_data['width']
    transform = meta_data['transform']

    rows = np.arange(height)[:, np.newaxis]
    cols = np.arange(width)[np.newaxis, :]

    lon = transform.c + transform.a * (cols + 0.5) + transform.b * (rows + 0.5)
    lat = transform.f + transform.d * (cols + 0.5) + transform.e * (rows + 0.5)

    dist = surface_distance(meta_data, lon0, lat0, lon, lat)
    return dist <= radius


def to_local_xy(meta_data, lon0, lat0, lon, lat):
    mpd = meters_per_degree(meta_data['radius'])
    east = (lon - lon0) * mpd * np.cos(np.deg2rad(lat0))
    north = (lat - lat0) * mpd
    return east, north


def bearing_between(meta_data, lon0, lat0, lon1, lat1):
    east, north = to_local_xy(meta_data, lon0, lat0, lon1, lat1)
    return np.degrees(np.arctan2(east, north)) % 360.0


def geo_offset(meta_data, lon0, lat0, distance, bearing_deg):
    mpd = meters_per_degree(meta_data['radius'])
    b = np.deg2rad(bearing_deg)
    east = distance * np.sin(b)
    north = distance * np.cos(b)
    lon = lon0 + east / (mpd * np.cos(np.deg2rad(lat0)))
    lat = lat0 + north / mpd
    return lon, lat