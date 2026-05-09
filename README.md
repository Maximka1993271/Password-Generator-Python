# 🛡️ Secure Pass Pro v3.9

**🔐 Secure password generator with a multilingual Python GUI for Windows**

Secure Pass Pro is a modern desktop password generator built with Python and CustomTkinter.
It combines cryptographically secure password generation, multilingual interface, QR-code export, privacy controls, and a polished dark UI.

![v3.9 Preview](https://github.com/Maximka1993271/Password-Generator-Python/raw/main/Secure_Pass_MainWindow39.png)

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

- **Export and sharing**
  - Save and **Open** passwords as `.txt`, `.log`, `.key`, or `.pdf`.
  - Unicode PDF export support.
  - QR-code generation for quick transfer to mobile devices.

---

## 🚀 What’s New in v3.9

1. **Redesigned interface**
   Balanced layout with a dedicated side menu and **neon color-coded action buttons**.

2. **Improved security logic**
   Added entropy-based strength calculation, SHA-256 read-back verification for text exports, and safer clipboard cleanup.

3. **Triple localization**
   Full interface support for Russian, English, and Ukrainian.

4. **Smart character filtering**
   Exclude similar characters like `i`, `l`, `1`, `o`, `0`, and unclear punctuation symbols.

5. **Enhanced Sound Engine**
   Professional mechanical mouse click sound (replaced standard `winsound` Beeps).

6. **Extended export & viewing support**
   Stable saving and **opening** for `.txt`, `.log`, `.key`, and `.pdf` formats.

**[📥 Download Secure Pass Pro v3.9 (.exe)](https://github.com/Maximka1993271/Password-Generator-Python/releases/download/SecurePassProv3.9/SecurePassPro.exe)**

---

## 📜 Classic Branch: v2.0.0

![v2.0.0 Preview](https://github.com/Maximka1993271/Password-Generator-Python/raw/main/Secure_Pass_MainWindow.png)

Classic branch for users who prefer a minimal Tkinter-based interface.

- **Stable classic UI** for older Windows systems.
- **Core features**: password generation, history, themes, and basic controls.

**[📥 Download v2.0.0 Classic](https://github.com/Maximka1993271/Password-Generator-Python/releases/download/SecurePassProv2.0.0/SecurePassPro.exe)**

---

## ⚙️ Developer Information

### Technology Stack

- **Language**: Python 3.9+
- **GUI**: `customtkinter`
- **Audio**: `Windows Multimedia API (winmm)`
- **Libraries**: `Pillow`, `qrcode`, `fpdf`
- **Security**: `secrets`, `hashlib`, `random.SystemRandom`

### Build Command

To build a standalone Windows executable:

```bash
pyinstaller --noconfirm --onefile --windowed --clean --icon="icon.ico" --add-data "icon.ico;." --add-data "Computer Mouse Click.mp3;." --collect-all qrcode --collect-all customtkinter --hidden-import="PIL._tkinter_finder" --name "SecurePassPro" Secure_Pass_Pro.pyw
