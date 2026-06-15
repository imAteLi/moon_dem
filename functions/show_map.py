import numpy as np
from matplotlib.figure import Figure
from functions.geo_utils import build_projected_grid


def create_map_plot(data, meta_data, cmap, color_label, title, vmin=None, max_display_dim=1200):
    height, width = data.shape
    step = max(1, int(np.ceil(max(height, width) / max_display_dim)))

    data_ds = data[::step, ::step]
    plot_x, plot_y = build_projected_grid(meta_data, step=step, as_edges=True)

    fig = Figure(figsize=(6, 5), dpi=100)
    ax = fig.add_subplot(111)
    mesh = ax.pcolormesh(plot_x, plot_y, data_ds, cmap=cmap, shading='flat', vmin=vmin)

    ax.set_xlabel("Projected X (m)")
    ax.set_ylabel("Projected Y (m)")
    ax.set_title(title)
    ax.grid(True, linestyle='--', alpha=0.4)
    ax.set_aspect('equal')
    fig.colorbar(mesh, ax=ax, label=color_label)
    return fig


def create_dem_plot(dem_data, meta_data):
    return create_map_plot(dem_data, meta_data,
                           cmap='terrain', color_label="Elevation (m)",
                           title="DEM Map")


def create_slope_plot(slope_data, meta_data):
    return create_map_plot(slope_data, meta_data,
                           cmap='magma', color_label="Slope (Degrees)",
                           title="Slope Map", vmin=0)