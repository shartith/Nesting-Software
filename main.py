
import argparse
import sys
import os
import cv2
from pdf_loader import load_pdf_image
from image_processor import detect_lines, map_coordinates
from gcode_generator import generate_gcode


def process_file(input_path, width_mm, height_mm, output_path, debug=False):
    """
    Core logic to process the file and generate G-code.
    Returns a log string or raises Exception.
    """
    logs = []
    def log(msg):
        print(msg)
        logs.append(msg)

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"File {input_path} not found.")

    log(f"Processing {input_path}...")
    
    if input_path.lower().endswith('.pdf'):
        img = load_pdf_image(input_path)
    else:
        img = cv2.imread(input_path)

    if img is None:
        raise ValueError("Failed to load image.")

    h, w = img.shape[:2]
    log(f"Image Resolution: {w}x{h} pixels")
    log(f"Target Size: {width_mm}mm x {height_mm}mm")

    # 2. Detect Lines
    log("Detecting lines...")
    v_lines, h_lines = detect_lines(img)
    log(f"Found {len(v_lines)} Vertical lines and {len(h_lines)} Horizontal lines.")

    # 3. Map Coordinates
    mapped_v = map_coordinates(v_lines, w, h, width_mm, height_mm)
    mapped_h = map_coordinates(h_lines, w, h, width_mm, height_mm)

    # 4. Generate G-Code
    gcode = generate_gcode(mapped_v, mapped_h)
    
    # 5. Save Output
    with open(output_path, "w") as f:
        f.write(gcode)
    
    log(f"G-code saved to {output_path}")

    # Debug Visualization
    if debug:
        debug_img = img.copy()
        # Draw Vertical (Blue)
        for line in v_lines:
            x1, y1, x2, y2 = line
            cv2.line(debug_img, (x1, y1), (x2, y2), (255, 0, 0), 2)
        # Draw Horizontal (Green)
        for line in h_lines:
            x1, y1, x2, y2 = line
            cv2.line(debug_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
        debug_path = os.path.splitext(output_path)[0] + "_debug.jpg"
        cv2.imwrite(debug_path, debug_img)
        log(f"Debug image saved to {debug_path}")
        
    return "\n".join(logs)

def main():
    parser = argparse.ArgumentParser(description="Convert PDF/Image Nesting Layout to G-Code")
    parser.add_argument("input_file", help="Path to input PDF or Image file")
    parser.add_argument("--width", type=float, help="Total Width of the Plate in mm", required=True)
    parser.add_argument("--height", type=float, help="Total Height of the Plate in mm", required=True)
    parser.add_argument("--output", help="Output G-code file path", default="output.nc")
    parser.add_argument("--debug", action="store_true", help="Save debug image with detected lines")

    args = parser.parse_args()

    try:
        process_file(args.input_file, args.width, args.height, args.output, args.debug)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
