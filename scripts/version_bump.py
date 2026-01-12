import sys
import os
import re
from datetime import datetime

def bump_version(current_v, bump_type):
    parts = list(map(int, current_v.split('.')))
    if bump_type == 'major':
        parts[0] += 1
        parts[1] = 0
        parts[2] = 0
    elif bump_type == 'minor':
        parts[1] += 1
        parts[2] = 0
    else: # patch
        parts[2] += 1
    return '.'.join(map(str, parts))

def main():
    if len(sys.argv) < 2:
        print("Usage: python version_bump.py [patch|minor|major]")
        sys.exit(1)
    
    bump_type = sys.argv[1].lower()
    version_file = 'VERSION'
    readme_file = 'README.md'
    changelog_file = 'CHANGELOG.md'

    if not os.path.exists(version_file):
        print("VERSION file not found")
        sys.exit(1)

    with open(version_file, 'r') as f:
        current_version = f.read().strip()

    new_version = bump_version(current_version, bump_type)
    print(f"Bumping version: {current_version} -> {new_version}")

    # 1. Update VERSION file
    with open(version_file, 'w') as f:
        f.write(new_version + '\n')

    # 2. Update README.md
    if os.path.exists(readme_file):
        with open(readme_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace badge: version-X.X.X-blue
        content = re.sub(r'version-\d+\.\d+\.\d+-blue', f'version-{new_version}-blue', content)
        # Replace Header: V3.0.0
        content = re.sub(r'V\d+\.\d+\.\d+ 更新', f'V{new_version} 更新', content)
        
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(content)

    # 3. Update CHANGELOG.md (Insert template for new version)
    if os.path.exists(changelog_file):
        with open(changelog_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        date_str = datetime.now().strftime('%Y-%m-%d')
        new_entry = [
            f"## 🔖 [{new_version}] - {date_str}\n",
            "\n",
            "### ✨ Added (新增)\n",
            "- \n",
            "\n",
            "### 🔧 Changed (变更)\n",
            "- \n",
            "\n",
            "### 🐛 Fixed (修复)\n",
            "- \n",
            "\n"
        ]
        
        # Find the first version header and insert above it
        insert_idx = -1
        for i, line in enumerate(lines):
            if line.startswith('## 🔖 ['):
                insert_idx = i
                break
        
        if insert_idx != -1:
            new_lines = lines[:insert_idx] + new_entry + lines[insert_idx:]
            with open(changelog_file, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)

    print(f"Successfully bumped to {new_version}")

if __name__ == '__main__':
    main()
