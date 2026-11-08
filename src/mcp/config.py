import sys
import shutil
from pathlib import Path

DIRETORIO_DATA = str(Path(__file__).resolve().parents[1] / "data")

npx_path = shutil.which("npx") or shutil.which("npx.cmd")

MCP_CONFIG = {
    "dashboard": {
        "command": sys.executable,
        "args": ["-m", "src.mcp.dashboard_server"],
        "transport": "stdio",
    },
}

if npx_path:
    MCP_CONFIG["filesystem"] = {
        "command": npx_path,
        "args": ["-y", "@j0hanz/filesystem-mcp", DIRETORIO_DATA],
        "transport": "stdio",
    }