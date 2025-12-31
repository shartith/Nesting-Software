def generate_gcode(v_lines, h_lines, feed_rate=1000, unit="mm"):
    """
    Generates G-code string from mapped vertical and horizontal lines.
    v_lines: List of [x1, y1, x2, y2] (Vertical)
    h_lines: List of [x1, y1, x2, y2] (Horizontal)
    unit: 'mm' or 'inch'
    """
    gcode = []
    
    # Header
    gcode.append("%")
    gcode.append("O1000 (NESTING CUT)")
    
    if unit.lower() == "inch":
        gcode.append("G20 g90 (Inch, Absolute)")
    else:
        gcode.append("G21 g90 (Metric, Absolute)")
        
    gcode.append(f"F{feed_rate}")
    gcode.append("G0 Z0.5 (Safe Height)") # 0.5 inch is safer than 10 inches if unit is inch
    
    # 1. Vertical Cuts (1차)
    gcode.append("(--- 1st Pass: VERTICAL ---)")
    for i, line in enumerate(v_lines):
        x1, y1, x2, y2 = line
        gcode.append(f"(Vertical Cut #{i+1})")
        gcode.append(f"G0 X{x1:.2f} Y{y1:.2f}") # Move to start
        gcode.append("M3 (Cut On)")
        gcode.append(f"G1 X{x2:.2f} Y{y2:.2f}") # Cut to end
        gcode.append("M5 (Cut Off)")
        
    # 2. Horizontal Cuts (2차)
    gcode.append("(--- 2nd Pass: HORIZONTAL ---)")
    for i, line in enumerate(h_lines):
        x1, y1, x2, y2 = line
        gcode.append(f"(Horizontal Cut #{i+1})")
        gcode.append(f"G0 X{x1:.2f} Y{y1:.2f}")
        gcode.append("M3 S1000") # Start spindle/laser again if needed, S value optional
        gcode.append(f"G1 X{x2:.2f} Y{y2:.2f}")
        gcode.append("M5")
        
    # Footer
    gcode.append("G0 Z10.0")
    gcode.append("G0 X0 Y0")
    gcode.append("M30 (End of Program)")
    gcode.append("%")
    
    return "\n".join(gcode)
