# 🏗️ Сборка EXE (PyInstaller)

## Быстрый способ — `build.py`

```bash
cd "Secure Pass Pro"
python build.py
```

Готовый файл: `dist/SecurePassPro.exe`

### Опции build.py

```bash
python build.py --no-clean    # не удалять предыдущую сборку
python build.py --verbose     # показать полную команду PyInstaller
python build.py --lang EN     # язык вывода: RU / EN / UA
```

---

## Ручная команда PyInstaller

```bat
pyinstaller ^
  --noconfirm --onefile --windowed --clean ^
  --name "SecurePassPro" ^
  --icon="Icons/icon.ico" ^
  --add-data "Icons;Icons" ^
  --add-data "Sounds;Sounds" ^
  --add-data "Resources;Resources" ^
  --add-data "Langs;Langs" ^
  --add-data "core;core" ^
  --add-data "gui;gui" ^
  --add-data "security;security" ^
  --add-data "storage;storage" ^
  --add-data "utils;utils" ^
  --add-data "config.example.json;." ^
  --collect-all customtkinter ^
  --collect-all PIL ^
  --collect-all cryptography ^
  --collect-all argon2 ^
  --collect-all qrcode ^
  --collect-all fpdf ^
  --collect-all pykeepass ^
  --collect-all requests ^
  "Secure_Pass_Pro.pyw"
```

Полная актуальная команда с hidden-imports: см. файл `build_command.bat` в Releases.

---

## Требования для сборки

```bash
pip install pyinstaller>=6.0.0
pip install -r requirements.txt
```

---

## Структура после сборки

```
dist/
└── SecurePassPro.exe    # ~60 MB, всё включено
build/                   # временные файлы PyInstaller (можно удалить)
SecurePassPro.spec       # spec-файл (можно использовать повторно)
```

---

## Проверка целостности

После сборки сгенерируйте SHA-256 хэш для публикации в Releases:

```bat
certutil -hashfile dist\SecurePassPro.exe SHA256
```

```bash
# Linux / macOS
sha256sum dist/SecurePassPro.exe
```

---

## GitHub Actions

В репозитории настроен автоматический CI/CD:

| Workflow | Триггер | Описание |
|----------|---------|----------|
| `build.yml` | push в main | Проверка сборки |
| `nightly.yml` | каждую ночь | Ночная сборка |
| `release.yml` | тег `v*` или ручной | Публикация в Releases |

Создание релиза:
1. Создайте тег: `git tag v4.0.1 && git push origin v4.0.1`
2. GitHub Actions соберёт EXE и опубликует в Releases автоматически
