import cv2
import numpy as np

def detect_lines(image):
    """
    Detects vertical and horizontal lines in the image.
    Returns a tuple (vertical_lines, horizontal_lines).
    Each line is [x1, y1, x2, y2].
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Use adaptive thresholding to isolate lines
    # valid lines are black, background is white.
    # Invert so lines are white.
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY_INV, 11, 2)

    # Use morphological operations to refine valid lines
    # Vertical kernel
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 20))
    # Horizontal kernel
    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 1))
    
    # Detect Vertical lines
    v_temp = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, v_kernel, iterations=2)
    v_lines_p = cv2.HoughLinesP(v_temp, 1, np.pi/180, threshold=50, minLineLength=50, maxLineGap=10)
    
    # Detect Horizontal lines
    h_temp = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, h_kernel, iterations=2)
    h_lines_p = cv2.HoughLinesP(h_temp, 1, np.pi/180, threshold=50, minLineLength=50, maxLineGap=10)
    
    v_lines = []
    if v_lines_p is not None:
        for line in v_lines_p:
            x1, y1, x2, y2 = line[0]
            # Ensure vertical line (small x difference)
            if abs(x1 - x2) < 5: 
                v_lines.append(line[0])

    h_lines = []
    if h_lines_p is not None:
        for line in h_lines_p:
            x1, y1, x2, y2 = line[0]
            # Ensure horizontal line (small y difference)
            if abs(y1 - y2) < 5:
                h_lines.append(line[0])
                
    return merge_lines(v_lines, 'vertical'), merge_lines(h_lines, 'horizontal')

def merge_lines(lines, orientation, tolerance=10):
    """
    Merges lines that are close to each other.
    Simple clustering based on 'x' for vertical and 'y' for horizontal.
    """
    if not lines:
        return []

    # Sort based on primary coordinate
    idx = 0 if orientation == 'vertical' else 1
    lines.sort(key=lambda l: l[idx])
    
    merged = []
    current_group = [lines[0]]
    
    for i in range(1, len(lines)):
        line = lines[i]
        prev_line = current_group[-1]
        
        # Check proximity
        if abs(line[idx] - prev_line[idx]) < tolerance:
            current_group.append(line)
        else:
            merged.append(average_lines(current_group, orientation))
            current_group = [line]
            
    if current_group:
        merged.append(average_lines(current_group, orientation))
        
    return merged

def average_lines(group, orientation):
    """
    Averages a group of close lines into a single line.
    Extends the line to the min/max of the opposing coordinate.
    """
    x1s = [l[0] for l in group]
    y1s = [l[1] for l in group]
    x2s = [l[2] for l in group]
    y2s = [l[3] for l in group]
    
    if orientation == 'vertical':
        # Average X, Min Y, Max Y
        avg_x = int((sum(x1s) + sum(x2s)) / (2 * len(group)))
        min_y = min(min(y1s), min(y2s))
        max_y = max(max(y1s), max(y2s))
        return [avg_x, min_y, avg_x, max_y]
    else:
        # Average Y, Min X, Max X
        avg_y = int((sum(y1s) + sum(y2s)) / (2 * len(group)))
        min_x = min(min(x1s), min(x2s))
        max_x = max(max(x1s), max(x2s))
        return [min_x, avg_y, max_x, avg_y]

def map_coordinates(lines, img_width, img_height, total_width_mm, total_height_mm):
    """
    Converts pixel coordinates to real-world MM coordinates.
    Returns list of mapped lines.
    """
    x_scale = total_width_mm / img_width
    y_scale = total_height_mm / img_height
    
    mapped_lines = []
    for line in lines:
        x1, y1, x2, y2 = line
        mx1 = x1 * x_scale
        my1 = (img_height - y1) * y_scale # G-code usually has 0,0 at bottom-left, image is top-left
        mx2 = x2 * x_scale
        my2 = (img_height - y2) * y_scale
        mapped_lines.append([mx1, my1, mx2, my2])
    return mapped_lines
