@echo off
set TEMP=D:\temp
set TMP=D:\temp
set npm_config_cache=D:\npm-cache
set PATH=D:\node-v24.22.3-win-x64;D:\Ollama;%PATH%
set DATABASE_PATH=D:\ai-agency-tools\flowise\data2
set BLOB_STORAGE_PATH=D:\ai-agency-tools\flowise\storage
set LOG_PATH=D:\ai-agency-tools\flowise\logs
"D:\node-v24.22.3-win-x64\node.exe" "D:\ai-agency-tools\flowise-runtime\node_modules\flowise\bin\run" start
