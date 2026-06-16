import numpy as np
from matplotlib.figure import Figure
from functions.geo_utils import build_projected_grid, project_points


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


def _overlay(ax, meta_data, lines=None, points=None):
    if lines:
        for item in lines:
            p1, p2 = item[0], item[1]
            color = item[2] if len(item) > 2 else 'cyan'   # optional 3rd entry
            x1, y1 = project_points(meta_data, p1[0], p1[1])
            x2, y2 = project_points(meta_data, p2[0], p2[1])
            ax.plot([x1, x2], [y1, y2], '-', color=color, linewidth=1.0)
    if points:
        for (lon, lat, label) in points:
            x, y = project_points(meta_data, lon, lat)
            ax.plot(x, y, 'o', markersize=6)
            ax.annotate(label, (x, y), textcoords="offset points", xytext=(5, 5), fontsize=8, color='white')


def create_crater_plot(data, meta_data, cmap='terrain', color_label="Elevation (m)", title="Crater", lines=None, points=None):
    plot_x, plot_y = build_projected_grid(meta_data, step=1, as_edges=True)

    fig = Figure(figsize=(6, 5), dpi=100)
    ax = fig.add_subplot(111)
    mesh = ax.pcolormesh(plot_x, plot_y, data, cmap=cmap, shading='flat')

    _overlay(ax, meta_data, lines=lines, points=points)

    ax.set_xlabel("Projected X (m)")
    ax.set_ylabel("Projected Y (m)")
    ax.set_title(title)
    ax.grid(True, linestyle='--', alpha=0.4)
    ax.set_aspect('equal')
    fig.colorbar(mesh, ax=ax, label=color_label)
    return fig


def create_profile_plot(los_result, title="Line of Sight Profile"):
    prof = los_result['profile']
    d = prof['dist_from_obs']
    elev = prof['elev']
    z_los = prof['z_los']

    fig = Figure(figsize=(6, 5), dpi=100)
    ax = fig.add_subplot(111)
    ax.plot(d, elev, '-', color='saddlebrown', label="Terrain")
    ax.plot(d, z_los, '--', color='gray', label="Sight line")

    if los_result['blocked'] and los_result['obstacle_idx'] is not None:
        k = los_result['obstacle_idx']
        ax.plot(d[k], elev[k], 'rx', markersize=9, label="Obstacle")

    ax.set_xlabel("Distance from observer (m)")
    ax.set_ylabel("Elevation (m)")
    ax.set_title(title + (" - BLOCKED" if los_result['blocked'] else " - VISIBLE"))
    ax.grid(True, linestyle='--', alpha=0.4)
    ax.legend()
    return fig