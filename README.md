# 🛡️ Secure Pass Pro v3.9

**🔐 Secure password generator with a multilingual Python GUI for Windows**

Secure Pass Pro is a modern desktop password generator built with Python and CustomTkinter.
It combines cryptographically secure password generation, multilingual interface, QR-code export, privacy controls, and a polished dark UI.

![v3.9 Preview](https://github.com/Maximka1993271/Password-Generator-Python/raw/main/Secure_Pass_MainWindow39.jpg)

---

## ✨ Main Features v3.9

- **Cryptographically secure generation**
  Uses Python `secrets` module and system CSPRNG for unpredictable password generation.

- **Multilingual interface**
  Instant switching between **RU**, **EN**, and **UA** interface languages.

- **Password strength audit**
  - Entropy-based strength evaluation.
  - Estimated crack-time category.
  - Five-star visual strength indicator.

- **Privacy and safety**
  - Clipboard auto-cleanup after 60 seconds.
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

## 🚀 What's New in v3.9

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

### 📄 Enhanced PDF Export
- **Full Unicode support** for Cyrillic characters (Russian & Ukrainian)
- **Embedded DejaVuSans.ttf** font for professional PDF output
- No more garbled text or missing characters in exported documents

### Additional Improvements
- Redesigned interface with balanced layout and **neon color-coded action buttons**
- Added entropy-based strength calculation with SHA-256 verification
- Smart character filtering to exclude similar characters (i, l, 1, o, O, 0)
- Enhanced mechanical mouse click sound (replaced standard winsound Beeps)
- Extended export & viewing support for `.txt`, `.log`, `.key`, and `.pdf` formats
- Fixed PDF export for Cyrillic and Ukrainian text using DejaVuSans font
- Removed deprecated progress bar for cleaner interface

**[📥 Download Secure Pass Pro v3.9 (.exe)](https://github.com/Maximka1993271/Password-Generator-Python/releases/download/SecurePassProv3.9/SecurePassPro.exe)**

---

## ⚙️ Developer Information

### Technology Stack

- **Language**: Python 3.9+
- **GUI**: `customtkinter`
- **Audio**: `Windows Multimedia API (winmm)`
- **Libraries**: `Pillow`, `qrcode`, `fpdf`
- **PDF Font**: `DejaVuSans.ttf` (embedded, full Cyrillic support)
- **Security**: `secrets`, `hashlib`, `random.SystemRandom`

### Changelog v3.9 (2026-05-10)

**New Features:**
- Added **Settings window** with language, theme, sound and corner radius controls
- Added **Language Switcher** (RU/EN/UA) with instant UI translation
- Added **Theme Selector** (System/Light/Dark) with safe theme switching
- Added **Sound Toggle** with mechanical click feedback
- Added **Corner Radius Slider** (0-25px) for UI customization
- Added **DejaVuSans.ttf font** for proper Cyrillic display in PDF exports
- Added **dedicated Settings button** in the main menu with green neon color

**Fixes:**
- Fixed theme change freezing issues
- Fixed PDF export for Cyrillic and Ukrainian text using DejaVuSans font
- Fixed Ukrainian author name spelling (Максим Мельніков)
- Fixed duplicate code in build commands

**Improvements:**
- Removed deprecated theme buttons from bottom panel
- Optimized window rendering for better performance
- Improved button highlighting for active theme/language selection
- Enhanced clipboard auto-cleanup mechanism
- Updated strength indicator with 5-star rating system
- **Full Unicode/UTF-8 support for PDF documents**

**Removed:**
- Removed deprecated progress bar for cleaner interface
- Removed duplicate controls from main window

---

## 📜 Classic Branch: v2.0.0

![v2.0.0 Preview](https://github.com/Maximka1993271/Password-Generator-Python/raw/main/Secure_Pass_MainWindow.png)

Classic branch for users who prefer a minimal Tkinter-based interface.

- **Stable classic UI** for older Windows systems.
- **Core features**: password generation, history, themes, and basic controls.

**[📥 Download v2.0.0 Classic](https://github.com/Maximka1993271/Password-Generator-Python/releases/download/SecurePassProv2.0.0/SecurePassPro.exe)**
