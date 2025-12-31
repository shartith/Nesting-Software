import fitz  # PyMuPDF
import numpy as np
import cv2
import re

def extract_dimensions(pdf_path):
    """
    Extracts W (Width/Vertical) and L (Length/Horizontal) values from the PDF text.
    Returns: (width, length) or (None, None)
    """
    try:
        doc = fitz.open(pdf_path)
        page = doc.load_page(0)
        text = page.get_text()
        doc.close()
        
        # Regex patterns to find "W : <number>" and "L : <number>"
        # Pattern handles: W: 123.45, W : 123.45, W:123.45
        w_pattern = r"W\s*[:]\s*([0-9.]+)"
        l_pattern = r"L\s*[:]\s*([0-9.]+)"
        
        w_match = re.search(w_pattern, text, re.IGNORECASE)
        l_match = re.search(l_pattern, text, re.IGNORECASE)
        
        w_val = float(w_match.group(1)) if w_match else None
        l_val = float(l_match.group(1)) if l_match else None
        
        return w_val, l_val
        
    except Exception as e:
        print(f"Error extracting dimensions: {e}")
        return None, None

def extract_table_info(pdf_path):
    """
    Extracts Part info (Length, Width, Quantity) from the PDF table.
    Returns: List of dictionaries [{'length': float, 'width': float, 'quantity': int}, ...]
    """
    try:
        doc = fitz.open(pdf_path)
        page = doc.load_page(0)
        text = page.get_text("text") 
        doc.close()
        
        # Regex to match the table row structure shown in screenshot:
        # 절단 ... W ... L
        pattern = r"절단\s+\S+\s+\S+\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)"
        matches = re.findall(pattern, text)
        
        parts_map = {}
        
        if matches:
            for m in matches:
                try:
                    val1 = float(m[0])
                    val2 = float(m[1])
                    
                    # Map to L (Horizontal) and W (Vertical)
                    # L is larger, W is smaller
                    l = max(val1, val2)
                    w = min(val1, val2)
                    
                    key = (l, w)
                    if key in parts_map:
                        parts_map[key] += 1
                    else:
                        parts_map[key] = 1
                except:
                    continue
                    
        # Convert map to list
        parts_list = []
        for (l, w), q in parts_map.items():
            parts_list.append({'length': l, 'width': w, 'quantity': q})
            
        # Return list (empty if no matches)
        return parts_list

    except Exception as e:
        print(f"Error extracting table info: {e}")
        return []

    except Exception as e:
        print(f"Error extracting table info: {e}")
        return None, None, None


def load_pdf_image(pdf_path, dpi=300):
    """
    Loads the first page of a PDF and returns it as an OpenCV image (numpy array).
    """
    try:
        doc = fitz.open(pdf_path)
        page = doc.load_page(0)  # Load the first page
        
        # Increase resolution for better detection
        zoom = dpi / 72  # 72 is the default PDF DPI
        mat = fitz.Matrix(zoom, zoom)
        
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to numpy array
        # pix.samples is a bytes object, we need to convert it
        img_array = np.frombuffer(pix.samples, dtype=np.uint8)
        
        if pix.n == 3:  # RGB
            img = img_array.reshape((pix.h, pix.w, 3))
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR) # Convert to BGR for OpenCV
        elif pix.n == 4:  # RGBA
            img = img_array.reshape((pix.h, pix.w, 4))
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
        elif pix.n == 1: # Gray
            img = img_array.reshape((pix.h, pix.w))
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        else:
            raise ValueError(f"Unsupported number of channels: {pix.n}")
            
        doc.close()
        return img
        
    except Exception as e:
        print(f"Error loading PDF: {e}")
        return None
