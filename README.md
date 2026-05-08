# 🛡️ Secure Pass Pro v3.9

**🔐 Профессиональный генератор криптостойких паролей для Windows 11 Pro**

Современный, быстрый и безопасный инструмент, созданный для генерации максимально надежных паролей. Полная оптимизация под Windows 11, поддержка динамического дизайна и продвинутая система фильтрации символов.

![v3.9 Preview](https://github.com/Maximka1993271/Password-Generator-Python/raw/main/Secure_Pass_MainWindow39.png)

---

## ✨ Основные возможности v3.9 | Main Features | Основні можливості

### 🇷🇺 Русский
- **Криптостойкость**: Генерация на базе модуля `secrets` (CSPRNG).
- **Custom UI**: Регулировка закругления углов всех элементов в реальном времени.
- **Умная фильтрация**: Исключение похожих (i, l, 1) и **не однозначных** знаков.
- **Безопасность**: Очистка буфера обмена через 60 секунд.
- **Локализация**: Полная поддержка RU, EN, UA с мгновенным переключением.

### 🇺🇸 English
- **Crypto-Secure**: Built using the `secrets` module for maximum randomness.
- **Custom UI**: Real-time corner radius adjustment for all interface elements.
- **Smart Filtering**: Option to exclude ambiguous (i, l, 1) and **non-obvious** characters.
- **Security**: Automatic clipboard clearing after 60 seconds.
- **Localization**: Full RU, EN, UA support with on-the-fly switching.

### 🇺🇦 Українська
- **Криптостійкість**: Генерація на базі модуля `secrets` (CSPRNG).
- **Custom UI**: Регулювання закруглення кутів усіх елементів у реальному часі.
- **Розумна фільтрація**: Виключення схожих (i, l, 1) та **не однозначних** знаків.
- **Безпека**: Очищення буфера обміну через 60 секунд.
- **Локалізація**: Повна підтримка RU, EN, UA з миттєвим перемиканням.

---

## 🚀 Что нового в версии 3.9 | What's New | Що нового

1.  **Design 2.0**: Полный редизайн на `CustomTkinter` с боковым меню и адаптивной светлой темой.
2.  **Terminology Fix**: Обновлена логика фильтров — теперь «сложные знаки» заменены на более точные **«не однозначные»**.
3.  **Win 11 Optimization**: Нативная поддержка звуков `winsound` и корректное отображение на High DPI мониторах.
4.  **File Support**: Работа с расширениями `.key`, `.log` и `.txt` сохранена для полной совместимости.

**[📥 Скачать / Download v3.9 Stable](https://github.com/Maximka1993271/Password-Generator-Python/releases/download/SecurePassProv3.9/SecurePassPro.exe)**

---

## 📜 Classic Branch: v2.0.0

![v2.0.0 Preview](https://github.com/Maximka1993271/Password-Generator-Python/raw/main/Secure_Pass_MainWindow.png)

**Secure Pass Pro v2.0.0** — это надежная классическая ветка проекта для тех, кому важна максимальная стабильность и минимализм на базе стандартного Tkinter.

- **Стабильность**: Проверенный временем движок генерации.
- **Темы**: Поддержка светлой, темной и системной тем оформления.
- **История**: Базовый лог сгенерированных паролей.

**[📥 Скачать / Download v2.0.0 Classic](https://github.com/Maximka1993271/Password-Generator-Python/releases/download/SecurePassProv2.0.0/SecurePassPro.exe)**

---

## ⚙️ Техническая информация | Tech Specs

- **Language**: Python 3.9+
- **OS**: Windows 11 Pro (Optimized)
- **Libraries**: `customtkinter`, `qrcode`, `pillow`

```bash
pip install qrcode[pil] pillow customtkinter
