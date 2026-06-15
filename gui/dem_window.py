import tkinter as tk
import numpy as np
from tkinter import filedialog, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from functions.load_dem import load_dem_data
from functions.show_dem import create_dem_plot

from functions.calc_slope import calculate_slope_map
from functions.show_slope import create_slope_plot

class DEMApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DEM Analysis Program")
        self.root.geometry("1000x600")

        # Data state
        self.current_dem_data = None
        self.current_meta_data = None

        # UI initialization
        self.setup_ui()

    def setup_ui(self):
        # Left panel
        self.left_panel = tk.Frame(self.root, width=250, bg="#f0f0f0", padx=10, pady=10)
        self.left_panel.pack(side=tk.LEFT, fill=tk.Y)
        self.left_panel.pack_propagate(False)
        tk.Label(self.left_panel, text="Control Panel", font=("Arial", 14, "bold"), bg="#f0f0f0").pack(pady=(0, 20))

        # Right panel
        self.right_panel = tk.Frame(self.root, bg="white")
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        ## Left panel contents
        # Load button
        self.btn_load = tk.Button(self.left_panel, text="Load File", command=self.open_file_dialog, height=2, width=20)
        self.btn_load.pack(pady=5)

        # Show DEM button
        self.btn_show_DEM = tk.Button(self.left_panel, text="Show DEM", command=self.show_dem_image, height=2, width=20)
        self.btn_show_DEM.pack(pady=5)

        # Slope button
        self.btn_slope = tk.Button(self.left_panel, text="Calc Slope", command=self.show_slope_image, height=2, width=20)
        self.btn_slope.pack(pady=5)

        ## Split line
        tk.Frame(self.left_panel, height=2, bd=1, relief=tk.SUNKEN).pack(fill=tk.X, pady=20)

        # Information
        tk.Label(self.left_panel, text="File information:", anchor="w", bg="#f0f0f0").pack(fill=tk.X)
        self.txt_info = tk.Text(self.left_panel, height=15, width=30, font=("Consolas", 9))
        self.txt_info.pack(pady=5, fill=tk.Y)
        self.txt_info.insert(tk.END, "Need to load first")
        self.txt_info.config(state=tk.DISABLED)

    def open_file_dialog(self):
        file_path = filedialog.askopenfilename(filetypes=[("GeoTIFF", "*.tif")])
        if file_path:
            self.process_load(file_path)

    def process_load(self, file_path):
        try:
            result = load_dem_data(file_path)

            # Store data to state
            self.current_dem_data = result["data"]
            self.current_meta_data = result

            # Update message
            self.update_info_display(file_path)
            messagebox.showinfo("Success", "Data loaded")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def update_info_display(self, file_path):
        # Update meta information
        data_min = np.nanmin(self.current_dem_data)
        data_max = np.nanmax(self.current_dem_data)
        rows, cols = self.current_dem_data.shape

        crs_info = self.current_meta_data['crs'].to_string() if self.current_meta_data['crs'] else "Unknown"
        data_type = self.current_dem_data.dtype
        nodata = self.current_meta_data['nodata']
        radius = self.current_meta_data['radius']

        info_text = (
            f"File path: {file_path}\n"
            f"----------------------------------------\n"
            f"Size: {rows} rows x {cols} cols\n"
            f"CRS: {crs_info}\n"
            f"Elevation: {data_min:.2f} m ~ {data_max:.2f} m\n"
            f"Data type: {data_type}\n"
            f"NoData: {nodata}\n"
            f"Radius: {radius}\n"
        )

        self.txt_info.config(state=tk.NORMAL)
        self.txt_info.delete(1.0, tk.END)
        self.txt_info.insert(tk.END, info_text)
        self.txt_info.config(state=tk.DISABLED)

    def show_dem_image(self):
        if self.current_dem_data is None:
            messagebox.showwarning("Warning", "Need to load first")
            return

        # Clear image
        for widget in self.right_panel.winfo_children():
            widget.destroy()

        try:
            fig = create_dem_plot(self.current_dem_data, self.current_meta_data)
            canvas = FigureCanvasTkAgg(fig, master=self.right_panel)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def show_slope_image(self):
        if self.current_dem_data is None:
            messagebox.showwarning("Warning", "Need to load first")
            return

        # Clear image
        for widget in self.right_panel.winfo_children():
            widget.destroy()

        try:
            slope_data = calculate_slope_map(self.current_dem_data, self.current_meta_data)

            fig = create_slope_plot(slope_data, self.current_meta_data)

            canvas = FigureCanvasTkAgg(fig, master=self.right_panel)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        except Exception as e:
            messagebox.showerror("Calculation Error", str(e))