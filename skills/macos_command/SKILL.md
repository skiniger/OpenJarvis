---
name: macos_command
version: "1.0.0"
description: Native macOS control via AppleScript, Finder, Notifications, and System Monitoring.
author: kinggeorge
tags: [macos, system, automation, applescript, native]
required_capabilities: [system:execute]
---

# macOS Command Skill

Control your Mac natively through AppleScript and system tools.

## Actions

### `applescript`
Execute AppleScript code.

**Args:**
- `script` (string, required): The AppleScript to run.

**Security:** `do shell script` is blocked. Use the `shell_exec` tool for shell commands.

**Example:**
```json
{"action": "applescript", "args": {"script": "tell application 'Finder' to activate"}}
```

### `finder`
Control the macOS Finder.

**Args:**
- `action` (string, required): `open`, `reveal`, or `close`.
- `path` (string, required for `open`/`reveal`): File or folder path.

**Example:**
```json
{"action": "finder", "args": {"action": "open", "path": "~/Documents"}}
```

### `notification`
Send a native macOS notification.

**Args:**
- `title` (string, default: "Jarvis"): Notification title.
- `message` (string, required): Notification body.

**Example:**
```json
{"action": "notification", "args": {"title": "Build", "message": "Deployment complete"}}
```

### `system_info`
Get system information (CPU, RAM, disk, battery).

**Args:** none

**Requires:** `psutil` (`uv pip install psutil`)

**Example:**
```json
{"action": "system_info", "args": {}}
```

### `clipboard`
Read or write the system clipboard.

**Args:**
- `action` (string, required): `get` or `set`.
- `text` (string, required for `set`): Text to copy.

**Example:**
```json
{"action": "clipboard", "args": {"action": "set", "text": "Hello world"}}
```

### `volume`
Set system volume level.

**Args:**
- `level` (integer, required): 0–100.

**Example:**
```json
{"action": "volume", "args": {"level": 75}}
```

### `say`
Text-to-speech via the macOS `say` command.

**Args:**
- `text` (string, required): Text to speak.

**Example:**
```json
{"action": "say", "args": {"text": "Hello from Jarvis"}}
```

## Security

- AppleScript cannot execute shell commands (`do shell script` is blocked).
- Finder cannot access `/System`, `/private`, `/dev`, or `/Volumes`.
- Sudo is only available through AppleScript's `with administrator privileges`.
