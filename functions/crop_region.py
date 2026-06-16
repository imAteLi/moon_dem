import numpy as np
from affine import Affine
from functions.geo_utils import meters_per_degree, geo_to_pixel


def crop_to_circle(meta_data, lon0, lat0, radius, margin=1.3):
    mpd = meters_per_degree(meta_data['radius'])
    r_m = radius * margin
    d_lat = r_m / mpd
    d_lon = r_m / (mpd * np.cos(np.deg2rad(lat0)))

    r1, c1 = geo_to_pixel(meta_data, lon0 - d_lon, lat0 + d_lat)
    r2, c2 = geo_to_pixel(meta_data, lon0 + d_lon, lat0 - d_lat)

    row_min, row_max = sorted((r1, r2))
    col_min, col_max = sorted((c1, c2))

    row_min = max(0, row_min)
    col_min = max(0, col_min)
    row_max = min(meta_data['height'], row_max + 1)
    col_max = min(meta_data['width'], col_max + 1)

    if row_max <= row_min or col_max <= col_min:
        raise ValueError("Crater range wrong")

    sub_data = meta_data['data'][row_min:row_max, col_min:col_max]

    new_transform = meta_data['transform'] * Affine.translation(col_min, row_min)

    sub_meta = dict(meta_data)
    sub_meta.update({
        'data': sub_data,
        'transform': new_transform,
        'height': sub_data.shape[0],
        'width': sub_data.shape[1],
    })

    return sub_data, sub_meta