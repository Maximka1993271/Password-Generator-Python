# 🛡️ Secure Pass Pro v4.0

**🔐 Secure password generator with a multilingual Python GUI for Windows**

Secure Pass Pro is a modern desktop password generator built with Python and CustomTkinter.
It combines cryptographically secure password generation, multilingual interface, QR-code export, privacy controls, and a polished dark UI.

![v4.0 Preview](https://github.com/Maximka1993271/Password-Generator-Python/raw/main/Secure_Pass_MainWindow40.jpg)

---

## ✨ Main Features v4.0

- **Cryptographically secure generation**
  Uses Python `secrets` module and system CSPRNG for unpredictable password generation.

- **Multilingual interface**
  Instant switching between **RU**, **EN**, and **UA** interface languages.

- **Password strength audit**
  - Entropy-based strength evaluation.
  - Estimated crack-time category.
  - Five-star visual strength indicator.

- **Color-coded password field pulsation** ⚡
  - 🔴 **Red pulse** – Weak password (under 40 bits)
  - 🟠 **Orange pulse** – Medium password (40-79 bits)
  - 🟢 **Green pulse** – Strong password (80+ bits)

- **Privacy and safety**
  - Configurable clipboard auto-cleanup **(10-120 seconds, adjustable in settings)** – better than KeePassXC's fixed 30 seconds!
  - Local password history with one-click clearing.
  - Text export integrity check via **SHA-256**.
  - Protection against too-small character pools.

- **Modern dark GUI**
  - AMOLED-style dark interface.
  - High-DPI friendly layout.
  - Adjustable corner radius for UI elements in real time.
  - **New Neon-Glow effects for side menu buttons.**
  - **New dedicated Settings button** with green accent color.

- **Export and sharing**
  - Save and **Open** passwords as `.txt`, `.log`, `.key`, or `.pdf`.
  - **Full Cyrillic support in PDF exports** using embedded DejaVuSans.ttf font.
  - QR-code generation for quick transfer to mobile devices.

---

## 🚀 What's New in v4.0

### 🔒 Master Password Protection
Set a **master password** to protect access to the entire program. SHA-256 hashed with 5 attempts before lockout.

### ✅ File Integrity Verification
Automatic `.sha256` checksum creation when saving files and verification when opening them. Prevents tampering.

### 🔄 No Consecutive Repeats
New option to avoid repeated characters in a row (e.g., `aaa`, `111`).

### 👁️ Password Visibility Toggle
One-click **eye button** to show/hide the password, synced with the "Hide symbols" checkbox.

### ⌨️ Hotkeys Support
- **F5** – Generate new password
- **Ctrl+C** – Copy to clipboard
- **Ctrl+S** – Save to file
- **Ctrl+O** – Open file
- **Esc** – Close settings dialog

### 🎛️ Centralized Settings Panel
A brand new **Settings window** has been added, accessible via the **Settings** button in the main menu. All customization options are now conveniently located in one place.

### 🌐 Language Switcher
Quickly switch between **Русский**, **English**, and **Українська** directly from the settings panel. Interface language updates instantly without restart.

### 🎨 Theme Selector
Choose your preferred appearance:
- **System** – follows your Windows theme
- **Light** – bright and clean interface
- **Dark** – comfortable for night use

### 🔊 Sound Control
Toggle UI sound effects on/off with a single click. When enabled, mechanical mouse click sounds provide satisfying feedback.

### 📐 Corner Radius Control
A new slider allows you to customize the roundness of all UI elements from **0 to 25 pixels** – make it perfectly square or beautifully rounded.

### ⏱️ Configurable Clipboard Timeout (New!)
Adjust the clipboard auto-clear delay from **10 to 120 seconds** using a slider in settings. The setting is saved to `config.txt` and persists between sessions. This gives you more control than KeePassXC's fixed 30 seconds!

### 📄 Enhanced PDF Export
- **Full Unicode support** for Cyrillic characters (Russian & Ukrainian)
- **Embedded DejaVuSans.ttf** font for professional PDF output
- No more garbled text or missing characters in exported documents

### 🎨 Color Pulsation Animation (New!)
The password field now features a **0.3-second neon glow animation** after each generation, with colors indicating password strength:

| Strength | Entropy | Color | Effect |
|----------|---------|-------|--------|
| Weak | < 40 bits | 🔴 Red | Warning glow |
| Medium | 40–79 bits | 🟠 Orange | Caution glow |
| Strong | 80+ bits | 🟢 Green | Security glow |

This provides **instant visual feedback** about password quality without needing to read the rating text.

### Additional Improvements
- Redesigned interface with balanced layout and **neon color-coded action buttons**
- Added entropy-based strength calculation with SHA-256 verification
- Smart character filtering to exclude similar characters (i, l, 1, o, O, 0)
- Enhanced mechanical mouse click sound (replaced standard winsound Beeps)
- Extended export & viewing support for `.txt`, `.log`, `.key`, and `.pdf` formats
- Fixed PDF export for Cyrillic and Ukrainian text using DejaVuSans font
- Removed deprecated progress bar for cleaner interface

**[📥 Download Secure Pass Pro v4.0 (.exe)](https://github.com/Maximka1993271/Password-Generator-Python/releases/download/v4.0/SecurePassPro.exe)**

---

## ⚙️ Developer Information

### Technology Stack

- **Language**: Python 3.9+
- **GUI**: `customtkinter`
- **Audio**: `Windows Multimedia API (winmm)`
- **Libraries**: `Pillow`, `qrcode`, `fpdf`
- **PDF Font**: `DejaVuSans.ttf` (embedded, full Cyrillic support)
- **Security**: `secrets`, `hashlib`, `random.SystemRandom`
- **Animations**: Color-coded neon pulsation (Red/Orange/Green)

### Changelog v4.0 (2026-05-12)

**New Features:**
- Added **Master Password** protection with SHA-256 hashing (5 attempts limit)
- Added **File Integrity Verification** (`.sha256` checksums)
- Added **No Consecutive Repeats** option for password generation
- Added **Password Visibility Toggle** (eye button) with checkbox sync
- Added **Hotkeys support** (F5, Ctrl+C, Ctrl+S, Ctrl+O, Esc)
- Added **Settings window** with language, theme, sound and corner radius controls
- Added **Language Switcher** (RU/EN/UA) with instant UI translation
- Added **Theme Selector** (System/Light/Dark) with safe theme switching
- Added **Sound Toggle** with mechanical click feedback
- Added **Corner Radius Slider** (0-25px) for UI customization
- Added **Configurable Clipboard Timeout** (10-120 seconds slider, saves to config)
- Added **DejaVuSans.ttf font** for proper Cyrillic display in PDF exports
- Added **dedicated Settings button** in the main menu with green neon color
- Added **Color-coded password field pulsation** (Red/Orange/Green based on entropy)
- Added **Tooltips** for all buttons including the eye button

**Fixes:**
- Fixed checkbox/eye button synchronization
- Added fallback when password without repeats cannot be generated
- Fixed clipboard clearing timer issues
- Fixed theme change freezing issues
- Fixed PDF export for Cyrillic and Ukrainian text using DejaVuSans font
- Fixed Ukrainian author name spelling (Максим Мельніков)
- Fixed duplicate code in build commands

**Improvements:**
- Removed deprecated theme buttons from bottom panel
- Optimized window rendering for better performance
- Improved button highlighting for active theme/language selection
- Enhanced clipboard auto-cleanup mechanism with configurable timeout
- Updated strength indicator with 5-star rating system
- **Full Unicode/UTF-8 support for PDF documents**
- **Added visual feedback with color-coded password field animation**

**Removed:**
- Removed deprecated progress bar for cleaner interface
- Removed duplicate controls from main window

---

## 📜 Classic Branch: v2.0.0

![v2.0.0 Preview](https://github.com/Maximka1993271/Password-Generator-Python/raw/main/Secure_Pass_MainWindow.png)

### About v2.0.0 Classic

The **Classic branch** is a lightweight, stable version built with standard **Tkinter** (no external dependencies). It's perfect for users who:
- Prefer a minimal interface without animations
- Use older Windows systems with limited resources
- Want just the core password generation features

### ✨ v2.0.0 Features

| Feature | v2.0.0 Classic |
|---------|----------------|
| Cryptographic generation (secrets) | ✅ Yes |
| Password strength meter | ✅ Entropy-based |
| Crack time estimation (MD5) | ✅ Yes |
| QR code generation | ✅ Yes |
| Password history | ✅ Yes (last 5) |
| File export (`.txt`) | ✅ Save & Open |
| Multi-language (RU/EN/UA) | ✅ Yes |
| Light/Dark/System themes | ✅ Yes |
| Hotkeys (Ctrl+G, Ctrl+S, Ctrl+O) | ✅ Yes |
| SHA-256 integrity check | ❌ No |
| PDF export | ❌ No |
| Color pulsation animation | ❌ No |
| Corner radius control | ❌ No |
| Settings window | ❌ No |
| Master password | ❌ No |
| Configurable clipboard timeout | ❌ No |

### 🛠️ Tech Stack (v2.0.0)

- **Language**: Python 3.9+
- **GUI**: `tkinter` (built-in)
- **Libraries**: `Pillow`, `qrcode`
- **Security**: `secrets`, `hashlib`
- **Sound**: `winsound.Beep()`

### 📦 v2.0.0 Build Command

```bash
pyinstaller --noconfirm --onefile --windowed --icon="app_icon.ico" --add-data "app_icon.ico;." --name "SecurePassPro" Secure_Pass_Pro.pyw
