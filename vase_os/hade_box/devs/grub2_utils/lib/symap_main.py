#!/usr/bin/env python3

from ex_symbols import extract_all_symbols, save_symbols, validate_layout
import sys
import time
from datetime import datetime

## Testing
if __name__ == "__main__":
    timestamp = datetime.now().strftime("%Y%m%d")
    symbols = extract_all_symbols()
    save_symbols(symbols, f"symbols-{timestamp}.json")
    valid = validate_layout(sys.argv[1] if len(sys.argv) > 1 else "us", sys.argv[2] if len(sys.argv) > 2 else None, f"symbols-{timestamp}.json")
    sys.exit(0 if valid else 1)

