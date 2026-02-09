#!/usr/bin/env python3
"""Get DATABASE_URL from Railway CLI"""
import subprocess
import json
import sys

try:
    # Try JSON output first
    result = subprocess.run(['railway', 'variables', '--json'], 
                          capture_output=True, text=True, timeout=10)
    if result.returncode == 0:
        data = json.loads(result.stdout)
        db_url = data.get('DATABASE_URL', '')
        if db_url:
            print(db_url)
            sys.exit(0)
except:
    pass

# Fallback: try regular output
try:
    result = subprocess.run(['railway', 'variables'], 
                          capture_output=True, text=True, timeout=10)
    if result.returncode == 0:
        for line in result.stdout.split('\n'):
            if 'DATABASE_URL' in line and 'postgresql://' in line:
                # Extract the URL (between │ characters)
                parts = line.split('│')
                if len(parts) >= 2:
                    db_url = parts[1].strip()
                    if db_url.startswith('postgresql://'):
                        print(db_url)
                        sys.exit(0)
except:
    pass

print('NOT_FOUND', file=sys.stderr)
sys.exit(1)
