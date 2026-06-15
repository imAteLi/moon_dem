import rasterio

def load_dem_data(file_path):
    try:
        with rasterio.open(file_path) as file:
            data = file.read(1, masked=True)

            # Unit detection
            if file.crs is None:
                unit_label = "unknown"
            elif file.crs.is_geographic:
                unit_label = "degrees"
            elif file.crs.is_projected:
                unit_label = "meters"
            else:
                unit_label = "unknown"

            # Radius extraction
            default_radius = 1737400.0
            radius = default_radius
            try:
                if file.crs is not None and getattr(file.crs, 'semi_major_axis', None):
                    radius = file.crs.semi_major_axis
            except Exception:
                print("Unable to extract radius, using default radius")

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