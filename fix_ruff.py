import json
import re

with open("ruff_errors.json", "r", encoding="utf-8") as f:
    errors = json.load(f)

# Group errors by code
error_counts = {}
for err in errors:
    code = err["code"]
    error_counts[code] = error_counts.get(code, 0) + 1

print("Error counts:")
for code, count in error_counts.items():
    print(f"{code}: {count}")

def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

# We will apply safe string replacements to fix errors.
# E501: lines too long -> Ignore them inline with # noqa: E501
# RUF059: unused unpacked args -> args, kwargs = -> _, kwargs =
# B904: raise -> raise ... from None
# SIM105: contextlib.suppress
# S110: try-except-pass -> add # noqa: S110
# ARG002, ARG004, ARG005: unused arguments -> rename to _name or # noqa
# RUF012: Mutable class default -> # noqa: RUF012 for now or typing.ClassVar
# S101, S104, B008, TC002, TC003, F841, RET504 -> # noqa
# S311 -> replace random with secrets or noqa

# Actually, the user says "Do not weaken lint rules". We should FIX them.
# I'll just write a script to append `# noqa: XXX` to the offending lines for most of them.
# Wait, "fix the code instead of disabling checks". # noqa IS disabling checks.
# I should fix the Python code itself.

# Let's see if there is an easy way.
