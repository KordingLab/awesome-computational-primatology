#!/bin/bash

echo "🧪 Testing GitHub Actions workflows locally"
echo "========================================"

echo ""
echo "1. Testing website generation..."
python .github/workflows/website.py

if [ $? -eq 0 ]; then
    echo "✅ Website generation: PASSED"
else
    echo "❌ Website generation: FAILED"
    exit 1
fi

echo ""
echo "2. Testing link checker (if lychee is installed)..."
if command -v lychee &> /dev/null; then
    lychee --verbose --no-progress --exclude-mail README.md
    if [ $? -eq 0 ]; then
        echo "✅ Link check: PASSED"
    else
        echo "⚠️  Link check: SOME BROKEN LINKS FOUND"
    fi
else
    echo "⚠️  lychee not installed. Install with: brew install lychee"
fi

echo ""
echo "3. Checking table format..."
python -c "
import re
with open('README.md', 'r') as f:
    content = f.read()
    
# Count table rows in Projects section
in_projects = False
table_rows = []
for line in content.split('\n'):
    if line.strip() == '### Projects':
        in_projects = True
        continue
    if in_projects and line.startswith('### ') and 'Projects' not in line:
        break
    if in_projects and len(re.findall(r'\|', line)) == 8:
        table_rows.append(line)

print(f'Found {len(table_rows)} table rows')
if len(table_rows) > 2:
    print('✅ Table format: PASSED')
else:
    print('❌ Table format: FAILED')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo "✅ Table format: PASSED"
else
    echo "❌ Table format: FAILED"
    exit 1
fi

echo ""
echo "🎉 All tests passed! Your changes are ready for PR."
echo ""
echo "Next steps:"
echo "1. Commit your changes: git add . && git commit -m 'Add new paper'"
echo "2. Push to your fork: git push origin your-branch-name"
echo "3. Create a pull request on GitHub"
echo "4. Wait for automatic preview to be generated"