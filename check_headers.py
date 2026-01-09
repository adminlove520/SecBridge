import os
import re

# Get the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.join(script_dir, "Vulnerability-Wiki-PoC")
total_md = 0
has_repro = 0
missing_repro = []

# Regex to match the section header
# Matches lines starting with 1-3 #s, followed by optional whitespace, then "漏洞复现" or "POC" or "EXP"
# Case insensitive
pattern = re.compile(r'^#{1,3}\s*(漏洞复现|POC|EXP)', re.IGNORECASE | re.MULTILINE)

print(f"Scanning {repo_root}...")

for root, dirs, files in os.walk(repo_root):
    if '.git' in root:
        continue
        
    for file in files:
        if file.lower().endswith('.md') and file.lower() != 'readme.md':
            total_md += 1
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if pattern.search(content):
                        has_repro += 1
                    else:
                        missing_repro.append(path)
            except Exception as e:
                print(f"Error reading {file}: {e}")

print(f"Total MD files (excluding README.md): {total_md}")
print(f"Files with '漏洞复现/POC/EXP': {has_repro}")
print(f"Files MISSING the section: {len(missing_repro)}")

if missing_repro:
    print("\n--- Example files missing the section (First 10) ---")
    for p in missing_repro[:10]:
        print(os.path.relpath(p, repo_root))
        # Print first few lines of the first missed file to see structure
        if p == missing_repro[0]:
             print("\n[Preview of first missing file start]")
             with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                 print(f.read()[:200])
             print("[Preview end]\n")
