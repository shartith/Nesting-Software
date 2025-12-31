
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import cv2  # For image processing in PDF mode
from PIL import Image, ImageTk
from pdf_loader import load_pdf_image, extract_dimensions, extract_table_info
from nesting_engine import calculate_nesting_layout, create_preview_image
from gcode_generator import generate_gcode

class GCodeGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Nesting G-Code Generator")
        self.root.geometry("1400x950")
        
        # Style
        self.style = ttk.Style()
        self.style.configure("TButton", padding=6)
        self.style.configure("TLabel", padding=5)
        
        # --- Variables ---
        # Common
        self.unit_var = tk.StringVar(value="inch")
        self.output_path = tk.StringVar(value="output.nc")
        
        # PDF Mode Variables
        self.pdf_path = tk.StringVar()
        self.pdf_width = tk.StringVar()
        self.pdf_height = tk.StringVar()
        
        # Manual Mode Variables
        self.plate_w = tk.StringVar(value="96")
        self.plate_h = tk.StringVar(value="48")
        self.part_w = tk.StringVar(value="10")
        self.part_h = tk.StringVar(value="10")
        self.quantity = tk.StringVar(value="1")
        
        self.create_widgets()
        
    def create_widgets(self):
        # Top Config Frame
        config_frame = ttk.Frame(self.root, padding=10)
        config_frame.pack(fill="x")
        
        ttk.Label(config_frame, text="Unit:").pack(side="left")
        ttk.Radiobutton(config_frame, text="Inch (G20)", variable=self.unit_var, value="inch").pack(side="left", padx=5)
        ttk.Radiobutton(config_frame, text="MM (G21)", variable=self.unit_var, value="mm").pack(side="left", padx=5)
        
        ttk.Label(config_frame, text="Output File:").pack(side="left", padx=10)
        ttk.Entry(config_frame, textvariable=self.output_path, width=20).pack(side="left")
        
        # Tab Control
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Tab 1: Manual Nesting
        self.manual_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.manual_tab, text="Manual Nesting")
        self.setup_manual_tab()
        
        # Tab 2: PDF Extraction
        self.pdf_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.pdf_tab, text="PDF Extraction")
        self.setup_pdf_tab()
        
        # Log Area (Shared)
        log_frame = ttk.LabelFrame(self.root, text="Log", padding=10)
        log_frame.pack(fill="x", padx=10, pady=5, side="bottom")
        
        self.log_text = tk.Text(log_frame, height=5, state="disabled")
        self.log_text.pack(fill="x")
        
    def setup_pdf_tab(self):
        frame = ttk.Frame(self.pdf_tab, padding=20)
        frame.pack(fill="both", expand=True)
        
        # File Selection
        ttk.Label(frame, text="PDF/Image File:").grid(row=0, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.pdf_path, width=40).grid(row=0, column=1, padx=5)
        ttk.Button(frame, text="Browse", command=self.browse_pdf).grid(row=0, column=2)
        
        # Dimensions
        ttk.Label(frame, text="Plate Width (W) [Vertical]:").grid(row=1, column=0, sticky="w", pady=10)
        ttk.Entry(frame, textvariable=self.pdf_height).grid(row=1, column=1)
        
        ttk.Label(frame, text="Plate Length (L) [Horizontal]:").grid(row=2, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.pdf_width).grid(row=2, column=1)
        
        # Run Button
        ttk.Button(frame, text="Generate G-Code (PDF)", command=self.run_pdf_process).grid(row=3, column=1, pady=20)

    def setup_manual_tab(self):
        # Left Panel: Inputs
        left_panel = ttk.Frame(self.manual_tab, padding=20)
        left_panel.pack(side="left", fill="y")
        
        ttk.Button(left_panel, text="Import Plate Size from PDF", command=self.import_manual_pdf).pack(fill="x", pady=(0, 15))
        
        ttk.Label(left_panel, text="Plate Dimensions").pack(anchor="w", pady=(0, 5))
        ttk.Label(left_panel, text="Width (W) [Vertical]:").pack(anchor="w")
        ttk.Entry(left_panel, textvariable=self.plate_h).pack(fill="x")
        ttk.Label(left_panel, text="Length (L) [Horizontal]:").pack(anchor="w")
        ttk.Entry(left_panel, textvariable=self.plate_w).pack(fill="x")
        
        ttk.Separator(left_panel, orient="horizontal").pack(fill="x", pady=15)
        
        ttk.Label(left_panel, text="Part Dimensions").pack(anchor="w", pady=(0, 5))
        
        # Part Input Frame
        part_input_frame = ttk.Frame(left_panel)
        part_input_frame.pack(fill="x")
        
        ttk.Label(part_input_frame, text="W (Vert):").grid(row=0, column=0, sticky="w")
        ttk.Entry(part_input_frame, textvariable=self.part_h, width=8).grid(row=0, column=1, padx=2)
        
        ttk.Label(part_input_frame, text="L (Horz):").grid(row=0, column=2, sticky="w")
        ttk.Entry(part_input_frame, textvariable=self.part_w, width=8).grid(row=0, column=3, padx=2)
        
        ttk.Label(part_input_frame, text="Qty:").grid(row=0, column=4, sticky="w")
        ttk.Entry(part_input_frame, textvariable=self.quantity, width=5).grid(row=0, column=5, padx=2)
        
        ttk.Button(left_panel, text="Add Part", command=self.add_manual_part).pack(fill="x", pady=5)
        
        # Treeview for Part List
        cols = ('W', 'L', 'Qty')
        self.part_list_tree = ttk.Treeview(left_panel, columns=cols, show='headings', height=6)
        
        self.part_list_tree.heading('W', text='W (Vert)')
        self.part_list_tree.heading('L', text='L (Horz)')
        self.part_list_tree.heading('Qty', text='Qty')
        
        self.part_list_tree.column('W', width=60, anchor='center')
        self.part_list_tree.column('L', width=60, anchor='center')
        self.part_list_tree.column('Qty', width=40, anchor='center')
        
        self.part_list_tree.pack(fill="both", expand=True, pady=5)
        
        ttk.Button(left_panel, text="Remove Selected", command=self.remove_selected_part).pack(fill="x", pady=2)
        
        self.enable_rem_cut = tk.BooleanVar(value=True)
        ttk.Checkbutton(left_panel, text="Cut Remnant (잔량 절단)", variable=self.enable_rem_cut).pack(fill="x", pady=(10, 0))
        
        ttk.Button(left_panel, text="Update Preview", command=self.update_preview).pack(fill="x", pady=20)
        ttk.Button(left_panel, text="Generate G-Code", command=self.run_manual_process).pack(fill="x")
        
        # Right Panel: Visualization (Preview + GCode)
        right_panel = ttk.Frame(self.manual_tab, padding=10)
        right_panel.pack(side="right", fill="both", expand=True)

        # Use PanedWindow for adjustable split
        paned = ttk.PanedWindow(right_panel, orient="vertical")
        paned.pack(fill="both", expand=True)

        # Frame 1: Image Preview
        preview_frame = ttk.LabelFrame(paned, text="Layout Preview", padding=5)
        paned.add(preview_frame, weight=2)
        
        self.preview_label = ttk.Label(preview_frame)
        self.preview_label.pack(fill="both", expand=True)
        
        # Frame 2: G-Code Text
        gcode_frame = ttk.LabelFrame(paned, text="G-Code Output", padding=5)
        paned.add(gcode_frame, weight=1)
        
        self.gcode_text = tk.Text(gcode_frame, height=10, state="disabled")
        scroll = ttk.Scrollbar(gcode_frame, command=self.gcode_text.yview)
        self.gcode_text.configure(yscrollcommand=scroll.set)
        
        self.gcode_text.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        
    def browse_pdf(self):
        filename = filedialog.askopenfilename(filetypes=[("PDF & Images", "*.pdf *.png *.jpg"), ("All Files", "*.*")])
        if filename:
            self.pdf_path.set(filename)
            
    
    def add_manual_part(self):
        try:
            w = float(self.part_h.get())
            l = float(self.part_w.get())
            q = int(self.quantity.get())
            
            if q > 0:
                self.part_list_tree.insert('', 'end', values=(w, l, q))
                # Clear entries after add
                self.part_h.set("")
                self.part_w.set("")
                self.quantity.set("")
                # self.update_preview() # Disabled per user request
        except ValueError:
            messagebox.showwarning("Input Error", "Please enter valid numeric values for Part Dimensions and Quantity.")

    def remove_selected_part(self):
        selected_items = self.part_list_tree.selection()
        for item in selected_items:
            self.part_list_tree.delete(item)
        # self.update_preview() # Disabled per user request

    def log(self, msg):
        self.log_text.config(state="normal")
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def import_manual_pdf(self):
        filename = filedialog.askopenfilename(filetypes=[("PDF & Images", "*.pdf *.png *.jpg"), ("All Files", "*.*")])
        if filename and filename.lower().endswith('.pdf'):
            try:
                # 1. Extract Plate Dimensions (Header)
                w, l = extract_dimensions(filename)
                if w is not None and l is not None:
                     self.plate_h.set(str(w))
                     self.plate_w.set(str(l))
                     self.log(f"Imported Plate Dims: W={w}, L={l}")
                else:
                    self.log("Plate dimensions not found in PDF header.")

                # 2. Extract Part Info (Table)
                parts_data = extract_table_info(filename)
                
                # Clear existing table
                for item in self.part_list_tree.get_children():
                    self.part_list_tree.delete(item)
                
                if parts_data:
                     count = 0
                     for p in parts_data:
                         # Extraction returns {'length': l, 'width': w, 'quantity': q}
                         # UI expects (W (Vert), L (Horz), Qty)
                         # We mapped L=Horizontal, W=Vertical in extraction too.
                         
                         p_w = p['width']  # Vertical
                         p_l = p['length'] # Horizontal
                         p_qty = p['quantity']
                         
                         self.part_list_tree.insert('', 'end', values=(p_w, p_l, p_qty))
                         count += 1
                         
                     self.log(f"Imported {count} unique part types.")
                     # self.update_preview() # Disabled per user request
                else:
                    self.log("Part info table not found or format unrecognized.")
                    
            except Exception as e:
                self.log(f"Import Error: {e}")
                messagebox.showerror("Error", str(e))

    def update_preview(self):
        try:
            pw = float(self.plate_w.get())
            ph = float(self.plate_h.get())
            
            # Construct Parts List from Treeview
            parts_list = []
            for item_id in self.part_list_tree.get_children():
                vals = self.part_list_tree.item(item_id)['values']
                # vals = (w, l, qty) as strings or numbers
                try:
                    p_w = float(vals[0]) # Vertical
                    p_l = float(vals[1]) # Horizontal
                    p_q = int(vals[2])
                    parts_list.append({'length': p_l, 'width': p_w, 'quantity': p_q})
                except: continue
                
            if not parts_list:
                # If list is empty, maybe user typed in entry but didn't click Add?
                # Optional: Check entry fields and add temp?
                # No, strict UI: Must add to list.
                pass
            
            v_lines, h_lines, rects = calculate_nesting_layout(pw, ph, parts_list)
            
            # Extend Horizontal Lines if Enabled (Cut Remnant)
            if self.enable_rem_cut.get() and h_lines:
                # Find the right-most X2 coordinate across all horizontal lines
                # h_lines format: [x1, y1, x2, y2]
                # Right X is x2 (index 2)
                max_x = 0
                if h_lines:
                    max_x = max(line[2] for line in h_lines)
                
                # Extend lines that reach close to max_x to the plate width
                epsilon = 1.0 # Tolerance
                for line in h_lines:
                    # line is [x1, y1, x2, y2]
                    # We extend the RIGHT side (x2)
                    if abs(line[2] - max_x) < epsilon:
                        line[2] = pw
            
            # Draw preview
            # Note: create_preview_image now accepts rects directly
            
            # Dynamic Sizing based on current Label size
            w = self.preview_label.winfo_width()
            h = self.preview_label.winfo_height()
            if w < 100: w = 800 # Default larger width
            if h < 100: h = 600 # Default larger height
            
            preview_img = create_preview_image(pw, ph, v_lines, h_lines, rects, img_size=(w, h))
            
            # Not returning None to allow UI update with empty image if needed?
            # Actually create_preview_image returns an image even if empty.
            if preview_img:
                # Convert to Tkinter
                # Only if using opencv/numpy internally in create_preview_image, which returns PIL Image directly now?
                # Check nesting_engine.py again. 
                # Yes, it returns PIL Image.
                # So no need for cv2.cvtColor unless it returned numpy array.
                # My previous `nesting_engine.py` view used cv2 internally but returned `Image.fromarray`.
                # Wait, `Image.fromarray` usually expects RGB. OpenCv is BGR.
                # In my rewrite of `nesting_engine.py`, I did: `cv2.rectangle(...)` on `img`.
                # `img` is numpy array.
                # Then `Image.fromarray(img)`.
                # OpenCV uses BGR by default? No, `np.ones` creates array.
                # If I used BGR colors in cv2 calls (e.g. (255,0,0) is Blue in BGR, Red in RGB).
                # To be safe, let's keep it simple.
                # I'll Assume `create_preview_image` returns PIL Image.
                
                im_tk = ImageTk.PhotoImage(preview_img)
                self.preview_label.config(image=im_tk)
                self.preview_label.image = im_tk # Keep ref
            
            self.log(f"Preview updated: {len(rects)} parts placed.")
            return v_lines, h_lines
            
        except Exception as e:
            self.log(f"Preview Error: {e}")
            messagebox.showerror("Error", str(e))
            return None, None

    def run_manual_process(self):
        v_lines, h_lines = self.update_preview()
        if v_lines is None:
            return
            
        out_file = self.output_path.get()
        unit = self.unit_var.get()
        
        try:
            gcode = generate_gcode(v_lines, h_lines, unit=unit)
            with open(out_file, "w") as f:
                f.write(gcode)
            
            # Show in Text Area
            self.gcode_text.config(state="normal")
            self.gcode_text.delete("1.0", "end")
            self.gcode_text.insert("end", gcode)
            self.gcode_text.config(state="disabled")
            
            self.log(f"G-code generated: {out_file} ({unit})")
            # messagebox.showinfo("Success", f"G-code saved to {out_file}")
            
        except Exception as e:
            self.log(f"Error: {e}")
            messagebox.showerror("Error", str(e))

    def run_pdf_process(self):
        # ... logic similar to previous gui_main ...
        # Need to patch process_file to support unit if I want to match features, 
        # but user specifically asked for "parameters input" flow for the new requirement.
        # I will keep PDF flow as is (mm based usually) or update coordinates?
        # The prompt implies the NEW features are for the manual input.
        # But let's try to verify if PDF mode should also support Inch?
        # "Change basic unit to inch". Okay so PDF mode should also use inch?
        # If so, the user needs to input Plate Width in Inch.
        
        path = self.pdf_path.get()
        try:
            w = float(self.pdf_width.get())
            h = float(self.pdf_height.get())
        except:
             messagebox.showerror("Error", "Invalid dimensions")
             return
             
        out = self.output_path.get()
        unit = self.unit_var.get()
        
        # Thread
        threading.Thread(target=self._pdf_thread, args=(path, w, h, out, unit)).start()
        
    def _pdf_thread(self, path, w, h, out, unit):
        # NOTE: process_file in main.py currently hardcodes gcode generation with default args (mm).
        # We need to update main.py/process_file to accept unit or handle it here.
        # Since process_file encapsulates everything, I should update main.py first.
        # Or I can just import logic components.
        
        # Let's import logic components to have full control
        try:
            from gcode_generator import generate_gcode
            from image_processor import detect_lines, map_coordinates
            from pdf_loader import load_pdf_image
            
            if not os.path.exists(path):
                raise Exception("File not found")
                
            if path.lower().endswith('.pdf'):
                img = load_pdf_image(path)
            else:
                img = cv2.imread(path)
                
            v, h_lines = detect_lines(img)
            ih, iw = img.shape[:2]
            
            mv = map_coordinates(v, iw, ih, w, h)
            mh = map_coordinates(h_lines, iw, ih, w, h)
            
            gcode = generate_gcode(mv, mh, unit=unit)
            
            with open(out, "w") as f:
                f.write(gcode)
                
            self.root.after(0, lambda: self.log(f"PDF G-code saved to {out}"))
            self.root.after(0, lambda: messagebox.showinfo("Success", "Done"))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))

if __name__ == "__main__":
    root = tk.Tk()
    app = GCodeGeneratorApp(root)
    root.mainloop()
