<div align="center">

# 🛡️ Secure Pass Pro — Wiki

**Добро пожаловать в официальную документацию**

</div>

---

## 📚 Содержание Wiki

| Страница | Описание |
|----------|----------|
| 🏠 **[Home](Home)** | Эта страница — общий обзор |
| 🚀 **[Установка и запуск](Installation)** | Windows EXE, Python, сборка из исходников |
| 🖥️ **[Интерфейс](Interface)** | Главное окно, кнопки, горячие клавиши |
| 🔐 **[Генератор паролей](Password-Generator)** | Параметры, энтропия, сила пароля |
| 🎲 **[Фразы-пароли Diceware](Passphrase)** | Diceware, настройки, примеры |
| 👤 **[Генератор имён](Name-Generator)** | 8 режимов, примеры |
| 🗄️ **[База паролей](Password-Vault)** | Хранилище, категории, избранное |
| 🔒 **[Мастер-пароль](Master-Password)** | Защита, Argon2id, блокировка |
| 🛡️ **[Двухфакторная аутентификация](2FA)** | TOTP, QR-код, резервные коды |
| 📤 **[Импорт и экспорт](Import-Export)** | Все форматы: KeePass, Bitwarden, 1Password |
| ☁️ **[Облачная синхронизация](Cloud-Sync)** | WebDAV, Nextcloud |
| ⌨️ **[Auto-Type](Auto-Type)** | Автовставка пароля |
| 🔒 **[Архитектура безопасности](Security)** | Шифрование, память, анти-отладка |
| ⚙️ **[Настройки](Settings)** | Темы, язык, RGB, авто-блокировка |
| 🏗️ **[Сборка EXE](Building)** | PyInstaller, `build.py` |
| 🐛 **[Известные проблемы](Troubleshooting)** | FAQ и решения |

---

## ⚡ Быстрый старт

```bash
# 1. Клонировать
git clone https://github.com/Maximka1993271/Password-Generator-Python.git
cd Password-Generator-Python

# 2. Зависимости
pip install -r requirements.txt

# 3. Запустить
python Secure_Pass_Pro.pyw
```

Или скачайте готовый `SecurePassPro.exe` из [Releases](https://github.com/Maximka1993271/Password-Generator-Python/releases).

---

## 🔑 Ключевые принципы

> **Всё шифрование — локально.** Мастер-пароль и ключи никогда не покидают устройство.  
> **Нет телеметрии.** Программа не отправляет никаких данных на внешние серверы.  
> **Открытый исходный код.** Весь код доступен для аудита.
