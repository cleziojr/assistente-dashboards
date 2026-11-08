from pathlib import Path

DIRETORIO_DATA = str(Path(__file__).resolve().parents[1] / "data")

MCP_CONFIG = {
    "dashboard": {
        "command": "python",
        "args": ["-m", "src.mcp.dashboard_server"],
        "transport": "stdio",
    },
    "filesystem": {
        "command": "npx",
        "args": ["-y", "@j0hanz/filesystem-mcp", DIRETORIO_DATA],
        "transport": "stdio",
    },
}