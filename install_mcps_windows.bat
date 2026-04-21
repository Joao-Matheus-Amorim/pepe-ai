@echo off
echo Instalando MCPs...
npm install -g @github/github-mcp-server
npm install -g @modelcontextprotocol/server-git
npm install -g @modelcontextprotocol/server-filesystem
npm install -g @modelcontextprotocol/server-memory
npm install -g @modelcontextprotocol/server-sequential-thinking
npm install -g @modelcontextprotocol/server-fetch
npm install -g @modelcontextprotocol/server-brave-search
npm install -g @upstash/context7-mcp
npm install -g @playwright/mcp
pip install mcp mcp-server-sqlite
echo.
echo Instalacao concluida!
pause
