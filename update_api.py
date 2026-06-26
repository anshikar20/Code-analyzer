import os
import glob

directory = r"C:\Users\anshi\Downloads\project folder\project folder\dashboard\src\pages"
files = glob.glob(os.path.join(directory, "*.tsx"))

for file_path in files:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Replace const API
    content = content.replace("const API = 'http://localhost:8000';", "const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';")
    content = content.replace("const API = 'http://127.0.0.1:8000';", "const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';")
    
    # Replace inline fetch in Analytics
    content = content.replace("fetch('http://127.0.0.1:8000/analytics')", "fetch(`${import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'}/analytics`)")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
        
print("Updated API URLs successfully!")
