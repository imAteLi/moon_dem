import numpy as np
from functions.geo_utils import compute_meters_per_pixel


def calculate_slope_map(dem_data, meta_data):
    if np.ma.is_masked(dem_data):
        z = dem_data.filled(np.nan)
    else:
        z = dem_data

    raw_grad_y, raw_grad_x = np.gradient(z)
    mpp_x, mpp_y = compute_meters_per_pixel(meta_data)

    slope_x = raw_grad_x / mpp_x
    slope_y = raw_grad_y / mpp_y

    tan_slope = np.sqrt(slope_x ** 2 + slope_y ** 2)
    slope_degrees = np.degrees(np.arctan(tan_slope))

    return slope_degrees