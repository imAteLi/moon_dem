# 函数速查备忘录

本文件逐一说明项目中每个函数的**作用、参数含义、返回值与调用关系**，便于回顾与维护。

---

## 一、贯穿全程的数据结构

### `meta_data`（元数据字典）

由 `load_dem_data` 生成，几乎所有函数的第一个或第二个参数。裁剪后由 `crop_to_circle` 产生一个更新过的副本（`sub_meta`）。键如下：

| 键 | 含义 |
|---|---|
| `data` | 高程矩阵（masked array，单位米） |
| `transform` | 仿射变换（affine.Affine），像素↔地理坐标 |
| `crs` | 坐标参考系（rasterio CRS） |
| `width` / `height` | 列数 / 行数 |
| `bounds` | 地理范围 |
| `nodata` | 无效值标记 |
| `units` | `'degrees'`(地理) / `'meters'`(投影) / `'unknown'` |
| `radius` | 参考球半径（米），默认 1737400 |

> 重要：裁剪后必须更新 `transform`、`width`、`height`，否则坐标换算会错位。

### `line_of_sight` 的返回字典

| 键 | 含义 |
|---|---|
| `blocked` | 是否被遮挡（bool） |
| `obstacle_idx` | 主遮挡点的采样下标（被挡时） |
| `obstacle_dist_to_bottom` | 主遮挡点到坑底的**水平**距离（米） |
| `obstacle_lonlat` | 主遮挡点经纬度 |
| `has_nodata` | 采样线上是否有无效值 |
| `profile` | 绘剖面用的数组字典：`dist_from_obs`、`dist_to_target`、`elev`、`z_los`、`lons`、`lats` |

---

## 二、调用流程总览

```
加载：       Load File → load_dem_data → meta_data
裁剪：       _ensure_crater → crop_to_circle → sub_meta（缓存）
深度/坡度：  analyze_crater → circle_mask + calculate_slope_map
视线：       sight_line_btn → line_of_sight → create_profile_plot
遍历：       traverse_btn → traverse_edges →（内部多次 line_of_sight）→ create_crater_plot
绘图：       create_*_plot → build_projected_grid / project_points
```

底层依赖方向：`geo_utils`（被所有人依赖）← 功能模块 ← `show_map` ← `dem_window`。

---

## 三、逐模块函数说明

### functions/load_dem.py

**`load_dem_data(file_path)`**
- 作用：用 rasterio 打开 GeoTIFF，读取第 1 波段（masked），判定单位、提取参考半径，打包成 `meta_data`。
- 参数：`file_path` — .tif 文件路径。
- 返回：`meta_data` 字典。
- 连接：被 `DEMApp.process_load` 调用；是所有后续处理的数据源。

---

### functions/geo_utils.py（坐标 / 距离 / 方位 / 投影中枢）

**`meters_per_degree(radius)`**
- 作用：1° 大圆弧长 = πR/180（米/度），南北方向常数。
- 参数：`radius` — 参考球半径（米）。
- 返回：float。
- 连接：被 `compute_meters_per_pixel`、`surface_distance`、`crop_to_circle`、`to_local_xy`、`geo_offset` 等调用。

**`compute_meters_per_pixel(meta_data)`**
- 作用：算每像素的真实米数；度数数据下 X 方向逐行乘 cosφ。
- 参数：`meta_data`。
- 返回：`(mpp_x, mpp_y)`，其中 `mpp_x` 为按行变化的列向量。
- 连接：被 `calculate_slope_map` 调用。

**`geo_to_pixel(meta_data, lon, lat, as_int=True)`**
- 作用：经纬度 → 像素 (行, 列)。`as_int=False` 返回浮点位置。
- 参数：`lon, lat` 坐标；`as_int` 是否取整。
- 返回：`(row, col)`。
- 连接：被 `crop_to_circle`、`line_of_sight` 调用。

**`pixel_to_geo(meta_data, row, col)`**
- 作用：像素 (行, 列) → 经纬度（`geo_to_pixel` 的逆，工具函数）。
- 参数：`row, col`。
- 返回：`(lon, lat)`。
- 连接：通用工具；当前主流程已改用端点线性插值，未直接调用（保留备用）。

**`surface_distance(meta_data, lon1, lat1, lon2, lat2)`**
- 作用：两点地表平距（米），按经纬度差分解为东(×cosφ)、北方向再勾股。标量与数组通用。
- 参数：两点经纬度（可为数组）。
- 返回：距离（标量或数组）。
- 连接：被 `circle_mask`、`line_of_sight` 调用。

**`build_geo_transformer(meta_data)`**
- 作用：建立「地理经纬度 → 正射米制」的 pyproj 变换器，以研究区中心为切点；非度数数据返回 None。
- 参数：`meta_data`。
- 返回：`Transformer` 或 `None`。
- 连接：被 `project_points`、`build_projected_grid` 共用（投影的单一来源）。

**`project_points(meta_data, lon, lat)`**
- 作用：把点投到与栅格相同的正射坐标系，保证叠加对齐。
- 参数：`lon, lat`（可为数组）。
- 返回：`(x, y)` 投影米坐标。
- 连接：被 `show_map._overlay` 调用。

**`build_projected_grid(meta_data, step=1, as_edges=False)`**
- 作用：把像素网格转成投影坐标网格，供 pcolormesh 绘图。
- 参数：`step` 下采样步长；`as_edges` 是否输出像元边界（flat 着色需要）。
- 返回：`(x, y)` 两个二维网格。
- 连接：被 `create_map_plot`、`create_crater_plot` 调用。

**`circle_mask(meta_data, lon0, lat0, radius)`**
- 作用：生成布尔掩膜，标记距 (lon0,lat0) ≤ radius 的像素。
- 参数：圆心 `lon0, lat0`；`radius` 米。
- 返回：与高程同形状的布尔数组。
- 连接：被 `analyze_crater` 调用。

**`to_local_xy(meta_data, lon0, lat0, lon, lat)`**
- 作用：经纬度 → 以 (lon0,lat0) 为原点的本地「东, 北」米制。
- 参数：原点与目标点经纬度。
- 返回：`(east, north)`。
- 连接：被 `bearing_between` 调用。

**`bearing_between(meta_data, lon0, lat0, lon1, lat1)`**
- 作用：方位角反算，0°=北、90°=东，`atan2(东, 北)`。
- 参数：起点与目标点经纬度。
- 返回：方位角（度，0–360）。
- 连接：被 `traverse_edges` 调用（确定起始方位）。

**`geo_offset(meta_data, lon0, lat0, distance, bearing_deg)`**
- 作用：方位角正算，由起点 + 距离 + 方位求落点（东=d·sinβ，北=d·cosβ，再折回经纬度）。
- 参数：起点经纬度；`distance` 米；`bearing_deg` 方位角。
- 返回：`(lon, lat)`。
- 连接：被 `traverse_edges` 调用（生成各坑缘点）。

---

### functions/calc_slope.py

**`calculate_slope_map(dem_data, meta_data)`**
- 作用：坡度图。梯度除以真实米/像素得斜率，合成取反正切。
- 参数：`dem_data` 高程；`meta_data`。
- 返回：坡度角（度）数组。
- 连接：被 `analyze_crater`、`DEMApp.show_slope_image` 调用；内部调 `compute_meters_per_pixel`。

---

### functions/crop_region.py

**`crop_to_circle(meta_data, lon0, lat0, radius, margin=1.3)`**
- 作用：把整幅 DEM 裁成坑附近的方形小块，并更新 transform/尺寸。
- 参数：圆心 `lon0, lat0`；`radius` 米；`margin` 四周余量倍数。
- 返回：`(sub_data, sub_meta)`。
- 连接：被 `DEMApp._ensure_crater` 调用；内部调 `meters_per_degree`、`geo_to_pixel`。

---

### functions/analyze_crater.py

**`analyze_crater(dem_data, meta_data, lon0, lat0, radius)`**
- 作用：圆掩膜内求最大深度（缘最高−底最低）与最大坡度。
- 参数：`dem_data` 高程；`meta_data`；圆心 `lon0, lat0`；`radius` 米。
- 返回：字典 `z_floor, z_rim, max_depth, max_slope, n_pixels`。
- 连接：被 `DEMApp.analyze_crater_btn` 调用；内部调 `circle_mask`、`calculate_slope_map`。

---

### functions/line_of_sight.py

**`_sample_elevation(z, rows, cols)`**（内部）
- 作用：在浮点像素位置双线性插值取高程（`scipy` map_coordinates）。
- 参数：`z` 高程数组；`rows, cols` 浮点索引。
- 返回：各采样点高程数组。
- 连接：被 `line_of_sight` 调用。

**`line_of_sight(dem_data, meta_data, observer, target, n_samples=None, clearance=0.0)`**
- 作用：判断 observer→target 的直线视线是否被地形遮挡，并定位主遮挡点。
- 参数：
  - `observer` / `target` — (lon, lat) 元组；
  - `n_samples` — 采样点数（默认按像素长 2 倍自动取）；
  - `clearance` — 遮挡判定宽容度（米），容忍 DEM 垂直噪声。
- 返回：见上文「`line_of_sight` 的返回字典」。
- 连接：被 `DEMApp.sight_line_btn` 与 `traverse_edges` 调用；内部调 `geo_to_pixel`、`surface_distance`、`_sample_elevation`。
- 关键细节：采样索引减 0.5 对齐像素中心；采样点经纬度用端点线性插值，使起点严格等于观测者；只在内部采样点中找遮挡（端点本身不计）。

**`traverse_edges(dem_data, meta_data, center, point_a, radius, step_deg=10.0, clearance=0.0)`**
- 作用：从 A 的方位起每隔 `step_deg` 取一坑缘点，逐个做视线分析并汇总。
- 参数：`center` 坑底中心 (lon,lat)；`point_a` 点 A (lon,lat)；`radius` 米；`step_deg` 角度步长；`clearance` 同上。
- 返回：列表，每项含 `bearing, edge_lonlat, blocked, obstacle_dist_to_bottom`。
- 连接：被 `DEMApp.traverse_btn` 调用；内部调 `bearing_between`、`geo_offset`、`line_of_sight`。

---

### functions/show_map.py

**`create_map_plot(data, meta_data, cmap, color_label, title, vmin=None, max_display_dim=1200)`**
- 作用：通用绘图——下采样 + 正射投影 + pcolormesh。
- 参数：`data` 待绘数组；`cmap` 色图；`color_label` 色条标签；`title` 标题；`vmin` 色标下限；`max_display_dim` 下采样目标尺寸。
- 返回：matplotlib `Figure`。
- 连接：被 `create_dem_plot`、`create_slope_plot` 调用；内部调 `build_projected_grid`。

**`create_dem_plot(dem_data, meta_data)`** / **`create_slope_plot(slope_data, meta_data)`**
- 作用：分别按高程(terrain 色)/坡度(magma 色)封装 `create_map_plot`。
- 参数：对应数组与 `meta_data`。
- 返回：`Figure`。
- 连接：被 `DEMApp.show_dem_image` / `show_slope_image` 调用。

**`_overlay(ax, meta_data, lines=None, points=None)`**（内部）
- 作用：在坐标轴上叠加视线/射线与标注点，经 `project_points` 投影对齐。
- 参数：`ax` 轴；`lines` 线列表（每项 `(p1, p2)` 或 `(p1, p2, color)`）；`points` 点列表（每项 `(lon, lat, label)`）。
- 返回：无。
- 连接：被 `create_crater_plot` 调用。

**`create_crater_plot(data, meta_data, cmap='terrain', color_label='Elevation (m)', title='Crater', lines=None, points=None)`**
- 作用：绘制裁好的坑体小块（正射投影），可叠加连线与标注。
- 参数：见上；`lines`/`points` 同 `_overlay`。
- 返回：`Figure`。
- 连接：被 `DEMApp.show_crater`、`traverse_btn` 调用；内部调 `build_projected_grid`、`_overlay`。

**`create_profile_plot(los_result, title='Line of Sight Profile')`**
- 作用：绘制视线剖面——地形实线 vs 视线虚线，被挡时标出障碍点；标题含 VISIBLE/BLOCKED。
- 参数：`los_result` — `line_of_sight` 的返回；`title`。
- 返回：`Figure`。
- 连接：被 `DEMApp.sight_line_btn` 调用。

---

### gui/dem_window.py（`DEMApp` 类）

**`__init__(self, root)`**：初始化窗口、状态变量（`full_meta_data`、`crater_meta` 等）、调用 `setup_ui`。

**`setup_ui(self)`**：搭建左侧控制面板（按钮 + 输入框）与右侧绘图区。

**`_add_entry(self, label, default)`**：辅助生成「标签 + 输入框」，返回 Entry。

**`_set_info(self, text)`**：把文字写入左下信息栏。

**`_draw_figure(self, fig)`**：清空右侧并嵌入一个 matplotlib Figure。

**`_params(self)`**：读取中心/半径/点A/步长，返回 `(lon0, lat0, radius, lonA, latA, step)`。

**`_clearance(self)`**：读取 Clearance 输入框，返回浮点宽容度。

**`_ensure_crater(self)`**：用当前参数从整幅图裁出坑并缓存到 `self.crater_meta`，返回该 `sub_meta`；调 `crop_to_circle`。

**`open_file_dialog(self)` / `process_load(self, file_path)`**：选择并加载文件；调 `load_dem_data` 并刷新信息栏。

**`update_info_display(self, file_path)`**：在信息栏显示文件路径、尺寸、CRS、高程范围等。

**`show_dem_image(self)` / `show_slope_image(self)`**：显示整幅高程图 / 坡度图。

**`show_crater(self)`**：裁坑并绘制坑体图（标注 Center、A 与连线）。

**`analyze_crater_btn(self)`**：输出最大深度、最大坡度等；调 `analyze_crater`。

**`sight_line_btn(self)`**：单条视线分析，绘剖面并显示通/挡与距离；调 `line_of_sight`（传 `clearance`）。

**`traverse_btn(self)`**：绕坑一圈遍历，绘红/绿射线图并列出逐方位结果；调 `traverse_edges`（传 `clearance`）。

---

### main.py

**`main()`**：创建 Tk 根窗口、实例化 `DEMApp`、进入事件循环。程序入口。
