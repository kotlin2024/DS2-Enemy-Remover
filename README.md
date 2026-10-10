# DS2 Enemy Remover — Comfort Filters

Developed by **HJP** (Nexus Mods username: **UNITYDEVELOPER**).

Public source for the `DS2EnemySelector-Comfort.exe` Windows desktop utility for **Dark Souls II: Scholar of the First Sin**. This repository is provided for source inspection and building, including review of executable false positives. Publication is not a claim of Nexus approval or antivirus clearance.

## Features and scope

- Select ordinary enemy families with illustrated Korean cards; 96 families and 409 allow-listed parameter IDs.
- Search, current-area filter, 18-family phobia filter and 14-family community nuisance filter. Category filters change visibility only, preserve selections, and combine as a union.
- Hide selected enemies, disable their collision, pause their AI update, and exclude their controllers from player lock-on candidates. This is reversible runtime control, not deleting enemies from installed game files.
- During travel or death/loading, clear old targets and wait for the new game context to remain stable for two seconds before reapplying. Manual stop/F8 cancels automatic resumption. Game exit, access errors and restoration errors disable application.
- Base-game and all three DLC enemy families are represented. Complete coverage of every variant and every DLC area is **not** verified. Bosses, NPCs and unidentified variants are excluded by the catalog.
- The offline checkbox is user confirmation, not automatic network-state detection. Use offline only. Compatibility with other trainers or modified executables is not guaranteed.

## Run or build from source

Use Windows and Python **3.10**. The packaged EXE does not require Python.

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe app.py
```

For a standalone EXE and ordinary ZIP package:

```powershell
.\build.ps1
```

`build.ps1` runs the 34 backend/CPU/controller tests, builds with PyInstaller onefile without UPX, and includes usage documentation, attribution, third-party notices and a SHA-256 file in the ZIP. It uses the local virtual environment; it does not depend on sibling private workspace folders. Optional tests are:

```powershell
.\.venv\Scripts\python.exe -m unittest test_removal test_ai_payload test_lockon_payload test_controller -v
.\.venv\Scripts\python.exe verify_cute_ui.py
```

The unit tests use fake memory or the Unicorn x64 emulator and do not connect to the game. The UI verification also does not start a game-memory worker.

Rebuilding can produce a different EXE hash due to packaging/toolchain differences. `SHA256-Comfort.txt` identifies the developer's existing distributed EXE, not a promise of bit-for-bit reproducibility. The EXE and ZIP are not stored in this source repository.

## Security review: actual behavior

The runtime does not send network requests, download updates, install services/drivers, or write installed game files or save files. It enumerates processes/modules, verifies the target executable SHA-256, reads the game state and only enables write access when required for an explicit removal session. It does not alter enemy HP, coordinates or gravity.

Supported installed executable SHA-256:

```text
0045931b8914504531b7864a9488d396dc50cbaf524964016e1d69c3d1173131
```

The removal backend modifies selected, identity-validated actors' display/hit bits, speed, action-stop state and collision permission. It also allocates a bounded remote pointer table and trampoline code. A 6-byte AI update instruction site and a 7-byte player lock-on candidate site are temporarily patched to skip only selected entries. The game threads are briefly suspended during patch changes, memory protection is restored, and the instruction cache is flushed. Remote trampoline allocations are retained until the game exits to avoid freeing code that may still be executing. This behavior can resemble malware techniques to security scanners; it does not establish that any particular detection is a false positive.

Stop/close attempts to restore owned values and original instructions. During loading or identity changes, stale actor addresses are discarded rather than written. Restoration of destroyed/unloaded actors cannot be guaranteed. Avoid running other memory tools against the same instruction sites.

Preferences are stored under `%LOCALAPPDATA%\DS2EnemySelector`. The optional diagnostic button writes a local JSON snapshot. Only the fixed F8 key is polled for emergency stop; there is no general keystroke capture.

Key files:

| File | Purpose |
| --- | --- |
| `winprocess.py` | Process access, executable fingerprint and bounded memory I/O |
| `memory.py` | Player/world readiness, enemy enumeration and identity validation |
| `removal.py` | Selective actor changes and guarded restoration |
| `aihook.py`, `lockon.py` | Selective runtime instruction patches and bounded target tables |
| `controller.py` | Worker, loading/resume delay, stop/error handling |
| `app.py`, `softui.py`, `art_catalog.py` | UI, F8/offline gates and optional filters |
| `catalog.json` | Shipped allow-list; no external cheat-table file is needed to build |

## Validation and limitations

34 backend, trampoline-emulation and controller lifecycle tests pass. UI checks cover search, category union, current-area filtering, preservation of selections and minimum window size. Limited in-game user tests confirmed Heide/Old Knights disappear, become passable and do not reappear when attacked; a later user test confirmed hidden enemies cannot receive a new lock-on. This is not a test of every family, already-active lock-on release, all DLC areas or prolonged stability. Travel automatic resumption is covered by lifecycle tests, not a complete in-game travel survey.

An early coordinate-moving experiment failed restoration verification and was abandoned. The current shipped source does not implement that approach. No Nexus/VirusTotal clearance is asserted.

## Documentation and attribution

- [Korean usage guide](사용안내.md)
- [Filter research and Nexus distribution guidance](필터%20조사%20및%20배포%20안내.md)
- [Artwork attribution](ART_SOURCES.md)
- [Third-party notices](THIRD_PARTY_NOTICES.txt)
- Reference projects: [SilkySouls2](https://github.com/borgCode/SilkySouls2), [DS2S-META](https://github.com/Nordgaren/DS2S-META). Offset/list research and installed-executable analysis informed the implementation; those projects do not endorse this utility.

The source is published for inspection. No blanket redistribution license is granted for the author's original code or artwork by this publication; third-party components retain their own licenses.
