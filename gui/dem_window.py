import tkinter as tk
from tkinter import filedialog, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from functions.load_dem import load_dem_data
from functions.crop_region import crop_to_circle
from functions.analyze_crater import analyze_crater
from functions.line_of_sight import line_of_sight, traverse_edges
from functions.show_map import create_dem_plot, create_slope_plot, create_crater_plot, create_profile_plot
from functions.calc_slope import calculate_slope_map


class DEMApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DEM Analysis Program")
        self.root.geometry("1000x800")

        # Data state
        self.full_meta_data = None
        self.current_dem_data = None
        self.current_meta_data = None
        self.crater_meta = None

        # UI initialization
        self.setup_ui()

    def setup_ui(self):
        # Left panel
        self.left_panel = tk.Frame(self.root, width=260, bg="#f0f0f0", padx=10, pady=10)
        self.left_panel.pack(side=tk.LEFT, fill=tk.Y)
        self.left_panel.pack_propagate(False)
        tk.Label(self.left_panel, text="Control Panel", font=("Arial", 14, "bold"), bg="#f0f0f0").pack(pady=(0, 10))

        # Right panel
        self.right_panel = tk.Frame(self.root, bg="white")
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        ## Left panel contents
        # Load / full-map buttons
        tk.Button(self.left_panel, text="Load File", command=self.open_file_dialog,
                  height=1, width=22).pack(pady=3)
        tk.Button(self.left_panel, text="Show DEM", command=self.show_dem_image,
                  height=1, width=22).pack(pady=3)
        tk.Button(self.left_panel, text="Show Slope", command=self.show_slope_image,
                  height=1, width=22).pack(pady=3)

        tk.Frame(self.left_panel, height=2, bd=1, relief=tk.SUNKEN).pack(fill=tk.X, pady=8)

        # Crater parameters
        self.e_lon0 = self._add_entry("Center lon", "-58.7061")
        self.e_lat0 = self._add_entry("Center lat", "7.2689")
        self.e_radius = self._add_entry("Radius (m)", "300")
        self.e_lonA = self._add_entry("Point A lon", "-58.6971")
        self.e_latA = self._add_entry("Point A lat", "7.2705")
        self.e_step = self._add_entry("Step (deg)", "10")

        # Crater buttons
        tk.Button(self.left_panel, text="Crop & Show Crater", command=self.show_crater,
                  height=1, width=22).pack(pady=3)
        tk.Button(self.left_panel, text="Analyze Depth/Slope", command=self.analyze_crater_btn,
                  height=1, width=22).pack(pady=3)
        tk.Button(self.left_panel, text="Sight A -> Center", command=self.sight_line_btn,
                  height=1, width=22).pack(pady=3)
        tk.Button(self.left_panel, text="Traverse Edges", command=self.traverse_btn,
                  height=1, width=22).pack(pady=3)

        tk.Frame(self.left_panel, height=2, bd=1, relief=tk.SUNKEN).pack(fill=tk.X, pady=8)

        # Information
        tk.Label(self.left_panel, text="Information:", anchor="w", bg="#f0f0f0").pack(fill=tk.X)
        self.txt_info = tk.Text(self.left_panel, height=12, width=32, font=("Consolas", 9))
        self.txt_info.pack(pady=5, fill=tk.BOTH, expand=True)
        self.txt_info.insert(tk.END, "Need to load first")
        self.txt_info.config(state=tk.DISABLED)

    def _add_entry(self, label, default):
        tk.Label(self.left_panel, text=label, anchor="w", bg="#f0f0f0").pack(fill=tk.X)
        e = tk.Entry(self.left_panel)
        e.insert(0, default)
        e.pack(fill=tk.X, pady=1)
        return e

    def _set_info(self, text):
        self.txt_info.config(state=tk.NORMAL)
        self.txt_info.delete(1.0, tk.END)
        self.txt_info.insert(tk.END, text)
        self.txt_info.config(state=tk.DISABLED)

    def _draw_figure(self, fig):
        for widget in self.right_panel.winfo_children():
            widget.destroy()
        canvas = FigureCanvasTkAgg(fig, master=self.right_panel)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _params(self):
        lon0 = float(self.e_lon0.get())
        lat0 = float(self.e_lat0.get())
        radius = float(self.e_radius.get())
        lonA = float(self.e_lonA.get())
        latA = float(self.e_latA.get())
        step = float(self.e_step.get())
        return lon0, lat0, radius, lonA, latA, step

    def _ensure_crater(self):
        if self.full_meta_data is None:
            raise RuntimeError("Need to load a file first")
        lon0, lat0, radius, _, _, _ = self._params()
        sub, sub_meta = crop_to_circle(self.full_meta_data, lon0, lat0, radius)
        self.crater_meta = sub_meta
        return sub_meta

    def open_file_dialog(self):
        file_path = filedialog.askopenfilename(filetypes=[("GeoTIFF", "*.tif")])
        if file_path:
            self.process_load(file_path)

    def process_load(self, file_path):
        try:
            result = load_dem_data(file_path)
            self.full_meta_data = result
            self.current_dem_data = result["data"]
            self.current_meta_data = result
            self.crater_meta = None
            self.update_info_display(file_path)
            messagebox.showinfo("Success", "Data loaded")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def update_info_display(self, file_path):
        data_min = self.current_dem_data.min()
        data_max = self.current_dem_data.max()
        rows, cols = self.current_dem_data.shape
        crs_info = self.current_meta_data['crs'].to_string() if self.current_meta_data['crs'] else "Unknown"
        nodata = self.current_meta_data['nodata']
        radius = self.current_meta_data['radius']

        self._set_info(
            f"File: {file_path}\n"
            f"----------------------------------------\n"
            f"Size: {rows} x {cols}\n"
            f"CRS: {crs_info}\n"
            f"Elevation: {data_min:.2f} ~ {data_max:.2f} m\n"
            f"NoData: {nodata}\n"
            f"Radius: {radius}\n"
        )

    def show_dem_image(self):
        if self.current_dem_data is None:
            messagebox.showwarning("Warning", "Need to load first")
            return
        try:
            self._draw_figure(create_dem_plot(self.current_dem_data, self.current_meta_data))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def show_slope_image(self):
        if self.current_dem_data is None:
            messagebox.showwarning("Warning", "Need to load first")
            return
        try:
            slope = calculate_slope_map(self.current_dem_data, self.current_meta_data)
            self._draw_figure(create_slope_plot(slope, self.current_meta_data))
        except Exception as e:
            messagebox.showerror("Calculation Error", str(e))

    def show_crater(self):
        try:
            lon0, lat0, radius, lonA, latA, _ = self._params()
            meta = self._ensure_crater()
            fig = create_crater_plot(
                meta['data'], meta, title="Crater",
                points=[(lon0, lat0, "Center"), (lonA, latA, "A")],
                lines=[((lonA, latA), (lon0, lat0))],
            )
            self._draw_figure(fig)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def analyze_crater_btn(self):
        try:
            lon0, lat0, radius, _, _, _ = self._params()
            meta = self._ensure_crater()
            r = analyze_crater(meta['data'], meta, lon0, lat0, radius)
            self._set_info(
                f"Crater analysis\n"
                f"----------------------------------------\n"
                f"Floor elev : {r['z_floor']:.2f} m\n"
                f"Rim elev   : {r['z_rim']:.2f} m\n"
                f"Max depth  : {r['max_depth']:.2f} m\n"
                f"Max slope  : {r['max_slope']:.2f} deg\n"
                f"Pixels used: {r['n_pixels']}\n"
            )
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def sight_line_btn(self):
        try:
            lon0, lat0, radius, lonA, latA, _ = self._params()
            meta = self._ensure_crater()
            los = line_of_sight(meta['data'], meta, (lonA, latA), (lon0, lat0))
            self._draw_figure(create_profile_plot(los))
            if los['blocked']:
                self._set_info(
                    f"A -> Center: BLOCKED\n"
                    f"Obstacle distance to floor: {los['obstacle_dist_to_bottom']:.1f} m\n"
                )
            else:
                self._set_info("A -> Center: VISIBLE (floor in direct sight)\n")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def traverse_btn(self):
        try:
            lon0, lat0, radius, lonA, latA, step = self._params()
            meta = self._ensure_crater()
            rows = traverse_edges(meta['data'], meta, (lon0, lat0), (lonA, latA), radius, step_deg=step)

            lines = []
            for r in rows:
                color = 'red' if r['blocked'] else 'lime'
                lines.append((r['edge_lonlat'], (lon0, lat0), color))
            fig = create_crater_plot(meta['data'], meta, title="Edge Traverse",
                                     lines=lines, points=[(lon0, lat0, "Center")])
            self._draw_figure(fig)

            n_blocked = sum(1 for r in rows if r['blocked'])
            text = [f"Traverse: {len(rows)} rays, {n_blocked} blocked\n",
                    "----------------------------------------"]
            for r in rows:
                if r['blocked']:
                    text.append(f"{r['bearing']:6.1f} deg | BLOCKED @ {r['obstacle_dist_to_bottom']:.0f} m")
                else:
                    text.append(f"{r['bearing']:6.1f} deg | VISIBLE")
            self._set_info("\n".join(text))
        except Exception as e:
            messagebox.showerror("Error", str(e))