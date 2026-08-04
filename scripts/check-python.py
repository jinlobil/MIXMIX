import sys

if sys.version_info < (3, 10):
    print(f"Python 3.10+ required (found {sys.version.split()[0]})")
    raise SystemExit(1)

print(f"Python {sys.version.split()[0]} OK")
