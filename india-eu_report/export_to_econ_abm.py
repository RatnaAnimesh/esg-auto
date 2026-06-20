import os
import glob
import shutil
import re

src_dir = "/Users/ashishmishra/animeshratna/nsral/india-eu_report/abm_simulation/src"
export_dir = "/Users/ashishmishra/animeshratna/nsral/india-eu_report/econ-abm-export"

# Get all .py files in src_dir and its subdirectories
py_files = glob.glob(os.path.join(src_dir, "**/*.py"), recursive=True)

# Copy to export_dir and modify imports
for path in py_files:
    filename = os.path.basename(path)
    if filename == "__init__.py":
        continue
        
    dest_path = os.path.join(export_dir, filename)
    with open(path, "r") as f:
        content = f.read()
        
    # Replace `from src.X.Y import Z` with `from Y import Z`
    # The pattern should match `from src.something.module import` and replace with `from module import`
    content = re.sub(r'from src\.[a-zA-Z0-9_]+\.([a-zA-Z0-9_]+) import', r'from \1 import', content)
    # Also `import src.something.module` might be there, we can handle it if needed
    
    with open(dest_path, "w") as f:
        f.write(content)
        
print("Export complete.")
