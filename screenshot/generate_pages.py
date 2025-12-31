"""
Source Code Screenshot Generator
Generates HTML pages for each code file, split by 50 lines
"""
import os
import math
import html

# Configuration
LINES_PER_PAGE = 50
OUTPUT_DIR = r"c:\Workspace\Nesting-Software\screenshot"
SOURCE_DIR = r"c:\Workspace\Nesting-Software"

# Files to process
FILES = [
    "main.py",
    "gui_main.py", 
    "gcode_generator.py",
    "image_processor.py",
    "nesting_engine.py",
    "pdf_loader.py"
]

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{file_name} - Page {page_num}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/python.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            background: #0d1117;
            color: #c9d1d9;
            padding: 30px;
            min-height: 100vh;
        }}
        .code-container {{
            background: #161b22;
            border-radius: 12px;
            border: 1px solid #30363d;
            overflow: hidden;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
            max-width: 1200px;
            margin: 0 auto;
        }}
        .file-header {{
            background: linear-gradient(135deg, #238636 0%, #2ea043 100%);
            padding: 15px 25px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .file-name {{
            font-size: 18px;
            font-weight: 600;
            color: #ffffff;
        }}
        .page-info {{
            font-size: 14px;
            color: rgba(255, 255, 255, 0.85);
            background: rgba(0, 0, 0, 0.2);
            padding: 5px 15px;
            border-radius: 20px;
        }}
        .code-content {{ padding: 0; }}
        pre {{ margin: 0 !important; padding: 0 !important; background: transparent !important; }}
        code {{
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace !important;
            font-size: 13px !important;
            line-height: 1.6 !important;
        }}
        .code-table {{ width: 100%; border-collapse: collapse; }}
        .code-table td {{ vertical-align: top; padding: 0; }}
        .line-numbers {{
            width: 60px;
            background: #0d1117;
            text-align: right;
            padding: 15px 15px 15px 10px !important;
            color: #484f58;
            font-size: 13px;
            line-height: 1.6;
            user-select: none;
            border-right: 1px solid #21262d;
        }}
        .line-numbers span {{ display: block; }}
        .code-lines {{ padding-left: 20px !important; }}
        .hljs {{ background: transparent !important; padding: 15px 0 !important; }}
        .footer {{
            background: #0d1117;
            padding: 12px 25px;
            border-top: 1px solid #21262d;
            font-size: 12px;
            color: #8b949e;
            display: flex;
            justify-content: space-between;
        }}
    </style>
</head>
<body>
    <div class="code-container">
        <div class="file-header">
            <span class="file-name">{file_name}</span>
            <span class="page-info">Page {page_num} / {total_pages} (Lines {start_line}-{end_line})</span>
        </div>
        <div class="code-content">
            <table class="code-table">
                <tr>
                    <td class="line-numbers">{line_numbers}</td>
                    <td class="code-lines">
                        <pre><code class="language-python">{code_content}</code></pre>
                    </td>
                </tr>
            </table>
        </div>
        <div class="footer">
            <span>Nesting-Software</span>
            <span>Total: {total_lines} lines</span>
        </div>
    </div>
    <script>hljs.highlightAll();</script>
</body>
</html>'''

def generate_html_pages():
    """Generate HTML pages for each file split by lines"""
    generated_files = []
    
    for filename in FILES:
        filepath = os.path.join(SOURCE_DIR, filename)
        
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
            continue
            
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        total_lines = len(lines)
        total_pages = math.ceil(total_lines / LINES_PER_PAGE)
        
        print(f"\n{filename}: {total_lines} lines -> {total_pages} pages")
        
        for page in range(total_pages):
            start_idx = page * LINES_PER_PAGE
            end_idx = min((page + 1) * LINES_PER_PAGE, total_lines)
            
            start_line = start_idx + 1
            end_line = end_idx
            
            # Get lines for this page
            page_lines = lines[start_idx:end_idx]
            code_content = html.escape(''.join(page_lines))
            
            # Generate line numbers
            line_numbers = ''.join([f'<span>{i}</span>' for i in range(start_line, end_line + 1)])
            
            # Generate HTML
            html_content = HTML_TEMPLATE.format(
                file_name=filename,
                page_num=page + 1,
                total_pages=total_pages,
                start_line=start_line,
                end_line=end_line,
                total_lines=total_lines,
                line_numbers=line_numbers,
                code_content=code_content
            )
            
            # Save HTML file
            base_name = filename.replace('.py', '')
            html_filename = f"{base_name}_page{page + 1:02d}.html"
            html_path = os.path.join(OUTPUT_DIR, html_filename)
            
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            generated_files.append(html_filename)
            print(f"  Created: {html_filename}")
    
    return generated_files

if __name__ == "__main__":
    print("=" * 50)
    print("Source Code Screenshot Generator")
    print("=" * 50)
    print(f"Lines per page: {LINES_PER_PAGE}")
    print(f"Output directory: {OUTPUT_DIR}")
    
    files = generate_html_pages()
    
    print("\n" + "=" * 50)
    print(f"Generated {len(files)} HTML files")
    print("=" * 50)
