#!/usr/bin/env python3
import re
from pathlib import Path
import json
import sys

def extract_all_symbols():
    symbols_dir = Path("/usr/share/X11/xkb/symbols")
    all_symbols = {}

    if not symbols_dir.exists():
        print("Error: Could not find symbols directory")
        return {}

    for layout_file in symbols_dir.iterdir():
        if layout_file.is_file() and not layout_file.name.startswith('.'):
            layout_name = layout_file.name
            variants = []

            try:
                with open(layout_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                pattern = re.compile(r'xkb_symbols\s*"([^"]+)"')
                matches = pattern.findall(content)
                variants = list(set(matches))

                if variants:
                    all_symbols[layout_name] = sorted(variants)

            except Exception as e:
                print(f"Error reading {layout_name}: {e}")
                continue

    return all_symbols

symbols = extract_all_symbols()

def save_symbols(symbols_dict, output_file="symbols.json"):
    with open(output_file, 'w') as f:
        json.dump(symbols_dict, f, indent=2, sort_keys=True)
    total_variants = sum(len(v) for v in symbols.values())
    print(f"Exported: {len(symbols_dict)} layouts to {output_file} Total: {total_variants} variants")

def load_symbols(symbols_file="symbols.json"):
    try:
        with open(symbols_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {symbols_file} not found")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error parsing {symbols_file}: {e}")
        return {}

def validate_layout(layout, variant=None, symbols_file="symbols.json"):
    symbols = load_symbols(symbols_file)

    if not symbols:
        return False

    if layout not in symbols:
        print(f"Layout '{layout}' not found")
        return False

    if not variant:
        print(f"Found l: {layout}")
        return True

    if variant in symbols[layout]:
        print(f"Found lv: {layout} ({variant})")
        return True
    else:
        print(f"Variant '{variant}' not found for layout '{layout}'")
        print(f"Available variants for {layout}: {', '.join(symbols[layout])}")
        return False
