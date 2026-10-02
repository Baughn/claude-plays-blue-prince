# Removing BepInEx from Blue Prince
Installed 2026-10-02 (BepInEx 6.0.0-be.788 IL2CPP win-x64). To remove:
1. Steam → Blue Prince → Properties → Launch Options: delete `WINEDLLOVERRIDES="winhttp=n,b" %command%`
2. Delete from the game folder: `winhttp.dll`, `doorstop_config.ini`, `.doorstop_version`, `BepInEx/` (incl. plugins/ClaudeProbe.dll), `dotnet/`
Nothing else in the game folder was modified.
