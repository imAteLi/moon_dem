import rasterio
import numpy as np

def load_dem_data(file_path):
    try:
        with rasterio.open(file_path) as file:
            data = file.read(1, masked=True)

            # Unit detection
            if file.crs.is_geographic:
                unit_label = "degrees"
            elif file.crs.is_projected:
                unit_label = "meters"
            else:
                unit_label = "unknown"

            # Radius extraction
            default_radius = 1737400.0
            try:
                if file.crs and hasattr(file.crs, 'semi_major_axis'):
                    radius = file.crs.semi_major_axis
                else:
                    radius = default_radius
            except Exception as load_error:
                print(f"Unable to extract radius.")

            meta_data = {
                "data": data,
                "transform": file.transform,
                "crs": file.crs,
                "width": file.width,
                "height": file.height,
                "bounds": file.bounds,
                "nodata": file.nodata,
                "units": unit_label,
                "radius": radius
            }

            return meta_data

    except Exception as e:
        raise RuntimeError(f"Failed to load data: {str(e)}")