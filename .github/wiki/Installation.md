# 🚀 Установка и запуск

## Способ 1 — Готовый EXE (Windows, рекомендуется)

1. Перейдите в [Releases](https://github.com/Maximka1993271/Password-Generator-Python/releases)
2. Скачайте `SecurePassPro.exe`
3. Запустите — установка не требуется

> При первом запуске Windows SmartScreen может показать предупреждение. Нажмите **«Подробнее»** → **«Всё равно запустить»**.

---

## Способ 2 — Запуск из исходников (Python)

### Системные требования

| | Минимум | Рекомендуется |
|---|---------|--------------|
| **Python** | 3.14 | 3.14+ |
| **ОС** | Windows 10, Ubuntu 20.04, macOS 12 | Windows 11 |
| **RAM** | 100 MB | 200 MB |

### Установка

```bash
# 1. Клонировать репозиторий
git clone https://github.com/Maximka1993271/Password-Generator-Python.git
cd Password-Generator-Python

# 2. (Опционально) виртуальное окружение
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux / macOS

# 3. Установить зависимости
pip install -r requirements.txt

# 4. Запустить
python Secure_Pass_Pro.pyw
```

### Ключевые зависимости

| Пакет | Назначение |
|-------|-----------|
| `customtkinter` | Современный GUI |
| `cryptography` | AES-256-GCM шифрование |
| `argon2-cffi` | Хэширование мастер-пароля |
| `Pillow` | Иконки и изображения |
| `qrcode[pil]` | Генерация QR-кодов |
| `fpdf2` | Экспорт PDF |
| `pykeepass` | KeePass `.kdbx` импорт/экспорт |
| `requests` | HIBP API, WebDAV |
| `psutil` | Информация о системе |
| `pywin32` | Windows API (только Windows) |

---

## Способ 3 — Сборка EXE самостоятельно

```bash
python build.py
```

Готовый файл появится в папке `dist/SecurePassPro.exe`.  
Подробнее: **[Сборка EXE](Building)**

---

## Аргументы командной строки

```bash
python Secure_Pass_Pro.pyw --disable-vm-check      # отключить проверку VM (для разработки)
python Secure_Pass_Pro.pyw --disable-anti-debug    # отключить анти-отладку (для разработки)
```

---

## Структура файлов после первого запуска

```
.securepass/
├── config.json          # настройки
├── data/
│   ├── passwords.db     # зашифрованная база (SQLCipher)
│   ├── master.key       # хэш мастер-пароля
│   ├── db.salt          # соль для ключа БД
│   └── sessions.json    # сессии
└── logs/
    └── securepass.log   # лог (пароли отфильтрованы)
```

> Папка `.securepass` скрыта на Windows (`SetFileAttributesW`).
