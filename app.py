import os
import sys
import datetime
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional


class KeyInputLoggerApp:
	"""Consent-first, in-window key input logger using Tkinter."""

	def __init__(self, root: tk.Tk) -> None:
		self.root = root
		self.root.title("In-App Key Input Logger (Consent-First)")
		self.root.geometry("700x430")
		self.root.minsize(640, 380)

		self.logging_enabled: bool = False
		self.log_directory: str = os.path.join(os.path.dirname(__file__), "logs")
		self.log_file_path: str = os.path.join(self.log_directory, "keystrokes.txt")
		os.makedirs(self.log_directory, exist_ok=True)

		self.user_has_consented = tk.BooleanVar(value=False)
		self.global_mode = tk.BooleanVar(value=False)
		self._global_listener: Optional[object] = None  # pynput.keyboard.Listener when active

		self._build_ui()
		self._configure_events()

	def _build_ui(self) -> None:
		container = ttk.Frame(self.root, padding=16)
		container.pack(fill=tk.BOTH, expand=True)

		title = ttk.Label(
			container,
			text="Simple In-App Key Input Logger",
			font=("Segoe UI", 14, "bold"),
		)
		title.pack(anchor=tk.W)

		desc_text = (
			"Logs only the keys pressed while this window is focused. "
			"Requires explicit consent. Logs are saved to logs/keystrokes.txt."
		)
		desc = ttk.Label(container, text=desc_text, wraplength=640, justify=tk.LEFT)
		desc.pack(anchor=tk.W, pady=(6, 12))

		consent_frame = ttk.Frame(container)
		consent_frame.pack(fill=tk.X)
		consent_check = ttk.Checkbutton(
			consent_frame,
			text=(
				"I understand this will record the keys I type inside this window "
				"and consent to start logging."
			),
			variable=self.user_has_consented,
			command=self._on_consent_changed,
		)
		consent_check.pack(anchor=tk.W)

		controls = ttk.Frame(container)
		controls.pack(fill=tk.X, pady=(12, 8))

		self.start_button = ttk.Button(controls, text="Start logging", command=self.start_logging)
		self.stop_button = ttk.Button(controls, text="Stop logging", command=self.stop_logging, state=tk.DISABLED)
		self.open_folder_button = ttk.Button(controls, text="Open log folder", command=self.open_log_folder)
		self.clear_log_button = ttk.Button(controls, text="Clear log file", command=self.clear_log_file)
		self.global_check = ttk.Checkbutton(controls, text="Enable global logging (across apps)", variable=self.global_mode)

		self.start_button.pack(side=tk.LEFT)
		self.stop_button.pack(side=tk.LEFT, padx=(8, 0))
		self.open_folder_button.pack(side=tk.LEFT, padx=(8, 0))
		self.clear_log_button.pack(side=tk.LEFT, padx=(8, 0))
		self.global_check.pack(side=tk.LEFT, padx=(12, 0))

		status_frame = ttk.LabelFrame(container, text="Session status")
		status_frame.pack(fill=tk.BOTH, expand=True, pady=(12, 0))

		self.status_text = tk.Text(status_frame, height=10, wrap=tk.WORD, state=tk.DISABLED)
		self.status_text.pack(fill=tk.BOTH, expand=True)

		self._append_status(
			"Consent is required to enable logging. The logger records only while this window is active."
		)

	def _configure_events(self) -> None:
		self.root.protocol("WM_DELETE_WINDOW", self._on_close)

	def _on_consent_changed(self) -> None:
		self.start_button.config(state=(tk.NORMAL if self.user_has_consented.get() else tk.DISABLED))

	def start_logging(self) -> None:
		if not self.user_has_consented.get():
			messagebox.showwarning("Consent required", "Please provide consent before starting logging.")
			return
		if self.logging_enabled:
			return

		self.logging_enabled = True
		if self.global_mode.get():
			if not self._start_global_listener():
				self.logging_enabled = False
				return
		else:
			self.root.bind("<KeyPress>", self._on_key_press, add=True)
		self.start_button.config(state=tk.DISABLED)
		self.stop_button.config(state=tk.NORMAL)

		self._append_status("Logging started. Focus this window and type. Use 'Stop logging' to end.")
		self._append_file_line(f"\n--- Session started {self._timestamp()} ---\n")

	def stop_logging(self) -> None:
		if not self.logging_enabled:
			return
		self.logging_enabled = False
		self.root.unbind("<KeyPress>")
		self._stop_global_listener()
		self.start_button.config(state=(tk.NORMAL if self.user_has_consented.get() else tk.DISABLED))
		self.stop_button.config(state=tk.DISABLED)

		self._append_status("Logging stopped.")
		self._append_file_line(f"\n--- Session ended {self._timestamp()} ---\n")

	def open_log_folder(self) -> None:
		try:
			if sys.platform.startswith("win"):
				os.startfile(self.log_directory)  # type: ignore[attr-defined]
			else:
				# Fallback for other OSes
				import subprocess
				subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", self.log_directory])
		except Exception as exc:  # noqa: BLE001
			messagebox.showerror("Open folder failed", str(exc))

	def clear_log_file(self) -> None:
		try:
			with open(self.log_file_path, "w", encoding="utf-8") as f:
				f.write("")
			self._append_status("Log file cleared.")
		except Exception as exc:  # noqa: BLE001
			messagebox.showerror("Clear failed", str(exc))

	def _on_key_press(self, event: tk.Event) -> None:  # type: ignore[type-arg]
		if not self.logging_enabled:
			return

		key_repr = self._format_key_event(event)
		try:
			with open(self.log_file_path, "a", encoding="utf-8") as f:
				f.write(key_repr)
		except Exception as exc:  # noqa: BLE001
			self._append_status(f"Failed to write key: {exc}")

	def _format_key_event(self, event: tk.Event) -> str:  # type: ignore[type-arg]
		# Printable characters
		if getattr(event, "char", "") and event.char.isprintable():
			return event.char

		keysym = getattr(event, "keysym", "").lower()
		mapping = {
			"space": " ",
			"return": "\n",
			"backspace": "[BACKSPACE]",
			"tab": "\t",
			"escape": "[ESC]",
			"shift_l": "[SHIFT]",
			"shift_r": "[SHIFT]",
			"control_l": "[CTRL]",
			"control_r": "[CTRL]",
			"alt_l": "[ALT]",
			"alt_r": "[ALT]",
			"caps_lock": "[CAPSLOCK]",
			"left": "[ARROW_LEFT]",
			"right": "[ARROW_RIGHT]",
			"up": "[ARROW_UP]",
			"down": "[ARROW_DOWN]",
			"delete": "[DEL]",
			"insert": "[INS]",
			"home": "[HOME]",
			"end": "[END]",
			"prior": "[PAGE_UP]",
			"next": "[PAGE_DOWN]",
		}
		if keysym in mapping:
			return mapping[keysym]
		if keysym:
			return f"[{keysym.upper()}]"
		return ""

	def _start_global_listener(self) -> bool:
		"""Start a system-wide keyboard listener using pynput.

		Returns True if started, False if dependency missing or failed.
		"""
		try:
			from pynput import keyboard as pynput_keyboard  # type: ignore
		except Exception:  # noqa: BLE001
			messagebox.showerror(
				"Dependency required",
				(
					"Global logging requires the 'pynput' package.\n\n"
					"Install it in your environment and try again:\n"
					"pip install pynput"
				),
			)
			return False

		def on_press(key: object) -> None:
			if not self.logging_enabled:
				return
			text = self._format_pynput_key(key)
			if not text:
				return
			try:
				with open(self.log_file_path, "a", encoding="utf-8") as f:
					f.write(text)
			except Exception as exc:  # noqa: BLE001
				# Schedule a UI update safely from listener thread
				self.root.after(0, lambda: self._append_status(f"Failed to write key: {exc}"))

		listener = pynput_keyboard.Listener(on_press=on_press)
		listener.daemon = True
		try:
			listener.start()
			self._global_listener = listener
			self._append_status("Global logging enabled. Keys from other apps will be recorded.")
			return True
		except Exception as exc:  # noqa: BLE001
			messagebox.showerror("Global listener failed", str(exc))
			return False

	def _stop_global_listener(self) -> None:
		listener = self._global_listener
		if listener is None:
			return
		try:
			listener.stop()  # type: ignore[attr-defined]
		except Exception:
			pass
		finally:
			self._global_listener = None

	def _format_pynput_key(self, key: object) -> str:
		# Local import for typing without hard dependency when not used
		try:
			from pynput.keyboard import Key  # type: ignore
		except Exception:  # noqa: BLE001
			Key = object  # type: ignore

		# Alphanumeric
		try:
			# For character keys, key.char exists
			char = getattr(key, "char", None)
			if isinstance(char, str) and char.isprintable():
				return char
		except Exception:
			pass

		name = str(key)
		# Map common special keys
		mapping = {
			str(getattr(Key, "space", "space")): " ",
			str(getattr(Key, "enter", "enter")): "\n",
			str(getattr(Key, "tab", "tab")): "\t",
			str(getattr(Key, "backspace", "backspace")): "[BACKSPACE]",
			str(getattr(Key, "esc", "esc")): "[ESC]",
			str(getattr(Key, "shift", "shift")): "[SHIFT]",
			str(getattr(Key, "ctrl", "ctrl")): "[CTRL]",
			str(getattr(Key, "alt", "alt")): "[ALT]",
			str(getattr(Key, "caps_lock", "caps_lock")): "[CAPSLOCK]",
			str(getattr(Key, "left", "left")): "[ARROW_LEFT]",
			str(getattr(Key, "right", "right")): "[ARROW_RIGHT]",
			str(getattr(Key, "up", "up")): "[ARROW_UP]",
			str(getattr(Key, "down", "down")): "[ARROW_DOWN]",
			str(getattr(Key, "delete", "delete")): "[DEL]",
			str(getattr(Key, "insert", "insert")): "[INS]",
			str(getattr(Key, "home", "home")): "[HOME]",
			str(getattr(Key, "end", "end")): "[END]",
			str(getattr(Key, "page_up", "page_up")): "[PAGE_UP]",
			str(getattr(Key, "page_down", "page_down")): "[PAGE_DOWN]",
		}
		if name in mapping:
			return mapping[name]
		# Fallback: normalize like [KEY]
		clean = name.replace("Key.", "").upper()
		return f"[{clean}]"

	def _timestamp(self) -> str:
		return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

	def _append_status(self, message: str) -> None:
		self.status_text.config(state=tk.NORMAL)
		self.status_text.insert(tk.END, f"{message}\n")
		self.status_text.see(tk.END)
		self.status_text.config(state=tk.DISABLED)

	def _append_file_line(self, text: str) -> None:
		try:
			with open(self.log_file_path, "a", encoding="utf-8") as f:
				f.write(text)
		except Exception as exc:  # noqa: BLE001
			self._append_status(f"Failed writing to file: {exc}")

	def _on_close(self) -> None:
		if self.logging_enabled:
			self.stop_logging()
		self.root.destroy()


def main() -> None:
	root = tk.Tk()
	KeyInputLoggerApp(root)
	root.mainloop()


if __name__ == "__main__":
	main()
