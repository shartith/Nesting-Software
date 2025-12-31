import cv2
import numpy as np
from PIL import Image

def calculate_nesting_layout(plate_w, plate_h, parts_list, align_top_left=True):
    """
    Calculates nesting layout for multiple parts using Column Packing strategy.
    
    Args:
        plate_w (float): Plate Length (Horizontal)
        plate_h (float): Plate Width (Vertical)
        parts_list (list): List of dicts [{'length': float, 'width': float, 'quantity': int}]
    
    Returns:
        v_lines (list): List of [x1, y1, x2, y2]
        h_lines (list): List of [x1, y1, x2, y2]
        placed_rects (list): List of (x, y, w, h) in Bottom-Left coordinates
    """
    
    # 1. Expand parts into individual items
    items = []
    for p in parts_list:
        try:
            q = int(p['quantity'])
            l = float(p['length']) # Horizontal
            w = float(p['width'])  # Vertical
            if q > 0 and l > 0 and w > 0:
                for _ in range(q):
                    items.append({'l': l, 'w': w})
        except: continue
        
    # 2. Sort by Length (Horizontal) Descending
    items.sort(key=lambda x: x['l'], reverse=True)
    
    v_lines = []
    h_lines = []
    placed_rects = []
    
    current_x = 0
    
    # Column State
    col_width = 0
    current_y_from_top = 0 # Track usage in current column from top
    
    # Process items
    i = 0
    # Use a loop that allows reprocessing items if we start new column
    while i < len(items):
        item = items[i]
        l = item['l']
        w = item['w']
        
        # Start new column if needed (first item or column full/mismatch)
        if col_width == 0:
            if current_x + l > plate_w:
                print(f"Part {l}x{w} doesn't fit in remaining width.")
                i += 1
                continue
            col_width = l
            current_y_from_top = 0
            
        # Check Vertical Fit
        if current_y_from_top + w <= plate_h:
            # Place it
            x_pos = current_x
            y_pos = plate_h - (current_y_from_top + w)
            
            placed_rects.append((x_pos, y_pos, l, w))
            
            # Horizontal Cut (Green)
            if y_pos > 0: # Don't cut bottom edge
                h_lines.append([x_pos, y_pos, x_pos + col_width, y_pos])
                
            current_y_from_top += w
            i += 1 # Item placed
        else:
            # Column Full
            # Finish this column
            
            # Vertical Cut (Blue) at right of column
            cut_x = current_x + col_width
            if cut_x < plate_w:
                v_lines.append([cut_x, 0, cut_x, plate_h])
            
            current_x += col_width
            
            # Reset
            col_width = 0
            # Do NOT increment i, try to place this item in next column
            
    # Close last column
    if col_width > 0:
        cut_x = current_x + col_width
        if cut_x < plate_w:
            v_lines.append([cut_x, 0, cut_x, plate_h])
            
    return v_lines, h_lines, placed_rects


def create_preview_image(plate_w, plate_h, v_lines, h_lines, parts_rects, img_size=(600, 400)):
    """
    Creates a visual preview.
    Note: Can handle parts_rects as (x,y,w,h) in Bottom-Left coords.
    """
    # Create blank white image
    img = np.ones((img_size[1], img_size[0], 3), dtype=np.uint8) * 255
    
    if plate_w <= 0 or plate_h <= 0:
        return Image.fromarray(img)
    
    pad = 20
    avail_w = img_size[0] - 2*pad
    avail_h = img_size[1] - 2*pad
    
    scale = min(avail_w / plate_w, avail_h / plate_h)
    
    # Origin at Bottom-Left of visual area
    origin_x = pad + (avail_w - plate_w * scale) / 2
    origin_y = img_size[1] - pad - (avail_h - plate_h * scale) / 2
    
    def to_pix(x, y):
        # Input x,y are Bottom-Left based.
        # Image Y is Top-Down.
        # So y=0 -> px_y = origin_y
        # y=H -> px_y = origin_y - H*scale
        px = int(origin_x + x * scale)
        py = int(origin_y - y * scale)
        return px, py

    # Draw Plate Border
    p0 = to_pix(0, 0)
    p1 = to_pix(plate_w, plate_h)
    cv2.rectangle(img, (p0[0], p1[1]), (p1[0], p0[1]), (0, 0, 0), 2)

    # Draw Parts
    for (px, py, pw, ph) in parts_rects:
        # px, py are bottom-left
        pt_bl = to_pix(px, py)
        pt_tr = to_pix(px + pw, py + ph) # Top-Right
        
        cv2.rectangle(img, (pt_bl[0], pt_tr[1]), (pt_tr[0], pt_bl[1]), (220, 220, 220), -1)
        cv2.rectangle(img, (pt_bl[0], pt_tr[1]), (pt_tr[0], pt_bl[1]), (150, 150, 150), 1)

    # Draw Lines
    # Vertical - Blue
    for coords in v_lines:
        x1, y1, x2, y2 = coords
        pt1 = to_pix(x1, y1)
        pt2 = to_pix(x2, y2)
        cv2.line(img, pt1, pt2, (255, 0, 0), 2)
        
    # Horizontal - Green
    for coords in h_lines:
        x1, y1, x2, y2 = coords
        pt1 = to_pix(x1, y1)
        pt2 = to_pix(x2, y2)
        cv2.line(img, pt1, pt2, (0, 200, 0), 2)

    return Image.fromarray(img)
