import glob
import re

# 1. Fix datetime in models
model_files = glob.glob("bot/database/models/*.py")
for f_path in model_files:
    with open(f_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    if len(lines) > 0 and lines[0] == "from datetime import datetime\n":
        lines.pop(0)
        # Find where to put it
        for i, line in enumerate(lines):
            if "from __future__ import annotations" in line:
                lines.insert(i + 1, "from datetime import datetime\n")
                break
    with open(f_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

# 2. Fix restore_service.py
with open("bot/services/backup/restore_service.py", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    "backup_id: int  # noqa: ARG004, operator_id: int",
    "backup_id: int, operator_id: int"
)
content = content.replace(
    "async def execute_restore(\n        session: AsyncSession, guild: discord.Guild, backup_id: int, operator_id: int\n    ) -> bool:",
    "async def execute_restore(\n        session: AsyncSession, guild: discord.Guild, backup_id: int, operator_id: int\n    ) -> bool:  # noqa: ARG004"
)
with open("bot/services/backup/restore_service.py", "w", encoding="utf-8") as f:
    f.write(content)
