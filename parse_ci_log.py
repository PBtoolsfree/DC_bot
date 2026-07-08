import re

with open("ci.log", "r", encoding="utf-16le", errors="ignore") as f:
    lines = f.readlines()

in_test_failures = False
failures = []

for line in lines:
    if "=================================== ERRORS ====================================" in line or "=================================== FAILURES ===================================" in line:
        in_test_failures = True
    
    if in_test_failures:
        failures.append(line.strip())
        
    if "=========================== short test summary info ===========================" in line:
        in_test_failures = False
        failures.append(line.strip())

with open("test_failures.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(failures))
