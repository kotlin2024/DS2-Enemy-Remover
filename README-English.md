# DS2 Enemy Selector — Korean / English

One Windows program with a language selector. Run `DS2EnemySelector-BilingualSoft.exe`, then choose **English** or **한국어** from the selector at the top. Your language and selected enemy families are remembered, but application is always off when the program starts.

1. Start Dark Souls II: Scholar of the First Sin offline and load your character.
2. If an older selector is open, move away from enemies, press F8 to stop/restore, and close that selector before opening this version.
3. Search for enemies or select their cards. Korean names, English names, source variant labels and IDs are searchable in either language.
4. Optional **Phobia-related** and **Frustrating enemies** filters narrow the list only. Enabling both shows the combined list; hidden cards keep their selections. **Only show enemies found in this area** is an additional filter.
5. Confirm **My game is running offline**, then press **Start hiding selected enemies**.
6. **Stop & restore (F8)** stops application and attempts to restore enemies. Move away from them first.

Changing language immediately updates names, labels, counts and status messages without changing selected enemies, offline confirmation, filters or an active session. New names use the English source data; see `ENGLISH_NAMES.md`.

Travel and death/loading temporarily pause application. The same game process resumes once the new context has remained stable for two seconds. Manual stop cancels resumption. Game exit, access errors or restoration errors disable application.

The utility hides enemies, disables collision, pauses their AI and excludes them from lock-on candidates. It does not edit installed game files, mods, saves, HP or coordinates. It temporarily modifies game memory and instruction sites. The offline checkbox is a user confirmation, not automatic online detection.

Scope: 96 ordinary enemy families / 409 parameter IDs, including families from all three DLCs. Bosses, NPCs and unidentified variants are excluded. Coverage and removal behavior have not been verified across every enemy, area or long session. Restoration after destroyed/unloaded actors cannot be guaranteed. Preferences and local diagnostics are saved under `%LOCALAPPDATA%\DS2EnemySelector`.

Developed by HJP. English UI support does not imply Nexus approval or antivirus clearance. Third-party notices and artwork attribution accompany the package.
