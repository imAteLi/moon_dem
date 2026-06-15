import tkinter as tk
from gui.dem_window import DEMApp


def main():
    root = tk.Tk()
    app = DEMApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()