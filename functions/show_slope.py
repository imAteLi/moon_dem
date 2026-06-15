import numpy as np
from matplotlib.figure import Figure
from pyproj import CRS, Transformer

def create_slope_plot(slope_data, meta_data):

    height, width = slope_data.shape
    transform = meta_data['transform']
    unit_type = meta_data['units']
    radius = meta_data['radius']

    # Mesh grid transformation
    rows_grid, cols_grid = np.meshgrid(np.arange(height), np.arange(width), indexing='ij')

    a, b, c = transform.a, transform.b, transform.c
    d, e, f = transform.d, transform.e, transform.f

    # x = c + a*col + b*row
    # y = f + d*col + e*row
    x_transformed = c + (a * cols_grid) + (b * rows_grid)
    y_transformed = f + (d * cols_grid) + (e * rows_grid)

    # Projection
    if unit_type == 'degrees':
        center_lon = c + (width / 2 * a)
        center_lat = f + (height / 2 * e)

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

        plot_x, plot_y = transformer.transform(x_transformed, y_transformed)

    else:
        plot_x, plot_y = x_transformed, y_transformed

    # Rendering
    fig = Figure(figsize=(6, 5), dpi=100)
    ax = fig.add_subplot(111)

    plot = ax.pcolormesh(plot_x, plot_y, slope_data, cmap='magma', shading='auto', vmin=0)

    ax.set_xlabel("Projected X (Meters)")
    ax.set_ylabel("Projected Y (Meters)")
    ax.set_title(f"Slope Map")
    ax.grid(True, linestyle='--', alpha=0.3)

    fig.colorbar(plot, ax=ax, label="Slope (Degrees)")

    ax.set_aspect('equal')

    return fig