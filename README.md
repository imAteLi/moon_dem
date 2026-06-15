# README

## 项目简介

本项目基于 Pyhton 开发完成，能够实现月球 DEM 数据的加载、经过纬度矫正的坡度计算以及经过正射投影的图像显示。



## 环境依赖

本项目依赖于以下环境库：

- numpy
- matplotlib
- tkinter
- rasterio
- pyproj

其中通过 Anaconda 导出的环境配置已保存于 environment.yml 文件中，通过运行

```
conda env create -f environment.yml
```

完成配置环境，并通过运行主程序 main.py 进行启动。



## 项目过程

### 加载数据

首先，我了解到 .tif 格式的数据保存的包括高程的矩阵数据和元数据 meta data，故在加载数据的部分主要要进行的是对元数据的提取。由于数据同时可能是使用角度度数作为单位的也可能是使用米数作为单位的，首先需要进行区分。最终提取得到的元数据，包括变形矩阵、CRS 和单位等关键信息。

```
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
```



### 计算坡度

对于坡度的计算，此处直接使用 np.gradient 函数得到原始图像的梯度，再对使用米作为单位和使用度数作为单位分情况讨论。对于使用米作为单位，无需额外处理。但是对于使用度数作为单位，在 Y 方向也就是南北方向上只需要加入月球半径计算 米/度 的值并乘以分辨率得到 米/像素 值。

```
        # Y direction
        meters_per_degree = (np.pi * radius) / 180.0
        meters_per_pixel_y[:, :] = res_y * meters_per_degree
```

但是对于 X 方向来说，不同纬度的 米/度 都是不一样的，还需要根据各自所处的维度计算出缩放因子。因此此处多增加了一步纬度的计算。

```
        # Latitude scale factor
        row_indices = np.arange(rows)
        latitudes = transform.f + (transform.e * row_indices)
        lat_radians = np.deg2rad(latitudes)
        scale_factors = np.cos(lat_radians)

        # X direction
        meters_per_lat = res_x * meters_per_degree * scale_factors
        meters_per_pixel_x = meters_per_lat[:, np.newaxis]
        meters_per_pixel_x[meters_per_pixel_x == 0] = 1e-6
```

将原始的梯度除以各个方向上的 米/像素 值即可得到坡度数据。

```
    # Slope calculation
    slope_y = raw_grad_y / meters_per_pixel_y
    slope_x = raw_grad_x / meters_per_pixel_x

    tan_slope = np.sqrt(slope_x ** 2 + slope_y ** 2)
    slope_degrees = np.degrees(np.arctan(tan_slope))
```



### 显示图像

图像的坐标首先需要使用 meta data 中的 transform 矩阵对原始像素的 meshgrid 进行转换以完成坐标的还原。

```
   # Mesh grid transformation
    rows_grid, cols_grid = np.meshgrid(np.arange(height), np.arange(width), indexing='ij')

    a, b, c = transform.a, transform.b, transform.c
    d, e, f = transform.d, transform.e, transform.f

    # x = c + a*col + b*row
    # y = f + d*col + e*row
    x_transformed = c + (a * cols_grid) + (b * rows_grid)
    y_transformed = f + (d * cols_grid) + (e * rows_grid)
```

最开始我是用此种方法直接进行了绘图。但是随后通过与专业库 rasterio 中的对比我发现这样不经处理绘制出的图像会导致图象被强制拉伸成方形，完全变形。

![comparison_slope](pictures/comparison_slope.jpg)

随后我尝试根据不同方向的比例进行还原，但是简单地使用 matplotlib 进行比例缩放绘制出的图像还是只有比例进行了大致还原没有实际意义。

![ratio_changed_slope](pictures/ratio_changed_slope.jpg)

最后为了实现图像的正射投影，我使用了 pyproj 函数，使用其中的投影函数完成了图像投影。

```
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
```



### 操作界面

本项目使用的 GUI 界面为 python 自带的基础库 tkinter，其左侧的 Load File 实现点击后选择文件进行读取，Show DEM 在点击后显示出高程图。点击 Calc Slope 完成坡度的计算和显示。其最终结果如图：

![DEM_map](pictures/DEM_map.jpg)

![slope_map](pictures/slope_map.jpg)

目前该程序最大的问题是由于数据点极多，绘图时需要渲染的点过多，导致在点击按钮后需要等待相当漫长的时间才能完成图像的显示。