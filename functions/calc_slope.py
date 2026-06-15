import numpy as np

def calculate_slope_map(dem_data, meta_data):
    if np.ma.is_masked(dem_data):
        z = dem_data.filled(np.nan)
    else:
        z = dem_data

    transform = meta_data['transform']
    unit_type = meta_data['units']
    radius = meta_data['radius']

    # Pixel resolution (degrees per pixel / meters per pixel)
    res_x = abs(transform.a)
    res_y = abs(transform.e)

    rows, cols = z.shape

    # Raw gradients
    raw_grad_y, raw_grad_x = np.gradient(z)

    meters_per_pixel_y = np.zeros_like(z)
    meters_per_pixel_x = np.zeros_like(z)

    if unit_type == 'meters':
        meters_per_pixel_y[:, :] = res_y
        meters_per_pixel_x[:, :] = res_x

    elif unit_type == 'degrees':
        # Y direction
        meters_per_degree = (np.pi * radius) / 180.0
        meters_per_pixel_y[:, :] = res_y * meters_per_degree

        # Latitude scale factor
        row_indices = np.arange(rows)
        latitudes = transform.f + (transform.e * row_indices)
        lat_radians = np.deg2rad(latitudes)
        scale_factors = np.cos(lat_radians)

        # X direction
        meters_per_lat = res_x * meters_per_degree * scale_factors
        meters_per_pixel_x = meters_per_lat[:, np.newaxis]
        meters_per_pixel_x[meters_per_pixel_x == 0] = 1e-6

    else:
        raise ValueError("Unknown unit")

    # Slope calculation
    slope_y = raw_grad_y / meters_per_pixel_y
    slope_x = raw_grad_x / meters_per_pixel_x

    tan_slope = np.sqrt(slope_x ** 2 + slope_y ** 2)
    slope_degrees = np.degrees(np.arctan(tan_slope))

    return slope_degrees