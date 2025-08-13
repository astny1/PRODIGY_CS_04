# Simple In‑App Key Input Logger (Consent‑First)

This demo captures keyboard input with explicit user consent and saves it to a local file. It supports two modes:
- In‑app logging: records keys only while this window is focused (default; no extra deps)
- Global logging (optional): records keys across apps (Word, browsers, etc.) while you are logged in and the app is running, using a system‑wide hook

It is not a stealth/system password sniffer and cannot capture the Windows lock‑screen password.

## Ethical guidelines
- Only run with informed consent of the active user
- Do not run without notice; keep the app window accessible
- Store logs locally and delete when done

## Requirements
- Python 3.9+ with Tk support (standard Windows Python includes Tk)
- For Global mode only: install `pynput`
  ```powershell
  python -m pip install pynput
  ```

## Run (PowerShell)
```powershell
cd "D:\CYS TASK 04"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python app.py
```

## Use
1. In the app window, read the notice and check the consent box
2. Optional: check "Enable global logging (across apps)" to log outside the app
3. Click "Start logging"
4. Type in this window (in‑app mode) or any app (global mode)
5. Click "Stop logging" to end; close the window to fully exit

## Output
- Events are appended to `logs/keystrokes.txt`
- Session boundaries are timestamped
- Printable characters are recorded directly; common special keys appear in brackets (e.g., `[BACKSPACE]`, `[ARROW_LEFT]`)

## Limitations and notes
- Does not log the Windows secure logon/lock screen (by design and OS security)
- Logging stops when the app is closed; keep it running for global mode
- Some IME/virtual keyboard inputs may behave differently depending on OS settings

## Optional: Package to EXE (Windows)
```powershell
python -m pip install pyinstaller
pyinstaller --noconsole --onefile app.py
```
The built executable will be in `dist/`.

## Files
- `app.py`: Tkinter GUI and logger (with optional global mode via `pynput`)
- `logs/keystrokes.txt`: created on first run
- `logs/README.txt`: folder placeholder
