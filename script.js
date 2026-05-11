// Secure Pass Pro v4.0 - Premium UI Animations
// Анимации при прокрутке, плавное появление элементов
// Новое: визуальные эффекты для настраиваемой очистки буфера обмена

document.addEventListener("DOMContentLoaded", () => {
    
    // --- ОПЦИИ ДЛЯ НАБЛЮДАТЕЛЯ (Observer) ---
    const observerOptions = {
        threshold: 0.1,      // Анимация начнется, когда 10% элемента появится на экране
        rootMargin: "0px 0px -50px 0px" // Небольшой отступ снизу для более плавного срабатывания
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // При появлении в зоне видимости
                entry.target.style.opacity = "1";
                entry.target.style.transform = "translateY(0)";
                // Прекращаем наблюдение за этим элементом после активации анимации
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // --- ВЫБИРАЕМ ВСЕ ЭЛЕМЕНТЫ ДЛЯ АНИМАЦИИ ---
    // Карточки функций, карточки загрузок, элементы технологий
    const animatedElements = document.querySelectorAll('.card, .download-card, .tech-item');
    
    // Также добавляем hero-контент для плавного появления при загрузке страницы
    const heroContent = document.querySelector('.hero-content');
    const heroImage = document.querySelector('.hero-image');
    
    if (heroContent) {
        heroContent.style.opacity = "0";
        heroContent.style.transform = "translateY(30px)";
        heroContent.style.transition = "all 0.8s ease-out 0.2s";
        setTimeout(() => {
            heroContent.style.opacity = "1";
            heroContent.style.transform = "translateY(0)";
        }, 100);
    }
    
    if (heroImage) {
        heroImage.style.opacity = "0";
        heroImage.style.transform = "translateX(30px)";
        heroImage.style.transition = "all 0.8s ease-out 0.4s";
        setTimeout(() => {
            heroImage.style.opacity = "1";
            heroImage.style.transform = "translateX(0)";
        }, 100);
    }

    // --- ПРИМЕНЯЕМ АНИМАЦИИ К КАРТОЧКАМ ---
    animatedElements.forEach((element, index) => {
        // Устанавливаем начальное состояние (скрыто)
        element.style.opacity = "0";
        element.style.transform = "translateY(30px)";
        // Добавляем небольшую задержку для каждой следующей карточки
        element.style.transition = `all 0.6s cubic-bezier(0.4, 0, 0.2, 1) ${index * 0.08}s`;
        // Начинаем слежку
        observer.observe(element);
    });

    // --- ПЛАВНАЯ ПРОКРУТКА ДЛЯ ЯКОРНЫХ ССЫЛОК ---
    const smoothLinks = document.querySelectorAll('a[href^="#"]');
    
    smoothLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            
            if (targetId === "#" || targetId === "") return;
            
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                e.preventDefault();
                
                const headerHeight = document.querySelector('header')?.offsetHeight || 70;
                const targetPosition = targetElement.getBoundingClientRect().top + window.pageYOffset - headerHeight;
                
                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
                
                // Обновляем URL без скачка
                history.pushState(null, null, targetId);
            }
        });
    });

    // --- ПОДСВЕТКА АКТИВНОГО ПУНКТА МЕНЮ ПРИ ПРОКРУТКЕ ---
    const sections = document.querySelectorAll('section[id]');
    const navLinks = document.querySelectorAll('nav ul li a');
    
    if (sections.length > 0 && navLinks.length > 0) {
        window.addEventListener('scroll', () => {
            let current = '';
            const scrollPosition = window.scrollY + 100; // Отступ для хедера
            
            sections.forEach(section => {
                const sectionTop = section.offsetTop;
                const sectionHeight = section.offsetHeight;
                
                if (scrollPosition >= sectionTop && scrollPosition < sectionTop + sectionHeight) {
                    current = section.getAttribute('id');
                }
            });
            
            navLinks.forEach(link => {
                link.classList.remove('active');
                const href = link.getAttribute('href').substring(1);
                if (href === current) {
                    link.classList.add('active');
                }
            });
        });
    }

    // --- ДОБАВЛЯЕМ СТИЛИ ДЛЯ АКТИВНОЙ ССЫЛКИ ---
    const style = document.createElement('style');
    style.textContent = `
        nav ul li a.active {
            color: var(--accent-color, #4EC9B0);
            border-bottom: 2px solid var(--accent-color, #4EC9B0);
            padding-bottom: 5px;
        }
        
        .hero-content, .hero-image {
            will-change: transform, opacity;
        }
    `;
    document.head.appendChild(style);

    // --- ПРОСТАЯ ЗАЩИТА ОТ ДРОЖАНИЯ ПРИ РЕСАЙЗЕ ---
    let resizeTimer;
    window.addEventListener('resize', () => {
        document.body.classList.add('resize-animation-stopper');
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => {
            document.body.classList.remove('resize-animation-stopper');
        }, 400);
    });
    
    style.textContent += `
        .resize-animation-stopper * {
            animation: none !important;
            transition: none !important;
        }
    `;

    // --- ВИЗУАЛЬНЫЙ ЭФФЕКТ ДЛЯ КАРТОЧКИ ОЧИСТКИ БУФЕРА ---
    const clipboardCard = document.querySelector('.card:has(.card-icon:contains("⏱️"))');
    if (clipboardCard) {
        clipboardCard.addEventListener('mouseenter', () => {
            clipboardCard.style.boxShadow = '0 0 20px rgba(255, 165, 0, 0.3)';
        });
        clipboardCard.addEventListener('mouseleave', () => {
            clipboardCard.style.boxShadow = '';
        });
    }

    // --- АНИМАЦИЯ ДЛЯ БЕЙДЖЕЙ ПРИ НАВЕДЕНИИ ---
    const badges = document.querySelectorAll('.badge');
    badges.forEach(badge => {
        badge.addEventListener('mouseenter', () => {
            badge.style.transform = 'scale(1.05)';
            badge.style.transition = 'all 0.2s ease';
        });
        badge.addEventListener('mouseleave', () => {
            badge.style.transform = 'scale(1)';
        });
    });

    // --- ОБРАБОТЧИК ДЛЯ КНОПОК СКАЧИВАНИЯ ---
    const downloadBtns = document.querySelectorAll('.btn-primary, .btn-secondary');
    downloadBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            // Можно добавить аналитику или дополнительную логику здесь
            console.log(`Secure Pass Pro v4.0: Download clicked - ${btn.textContent}`);
            
            // Визуальная обратная связь при клике
            btn.style.transform = 'scale(0.98)';
            setTimeout(() => {
                btn.style.transform = '';
            }, 150);
        });
    });

    // --- ЭФФЕКТ ПЕЧАТИ ДЛЯ ЗАГОЛОВКА (опционально, только на главной) ---
    const heroTitle = document.querySelector('.hero h1');
    if (heroTitle && !sessionStorage.getItem('title-animated')) {
        const originalText = heroTitle.innerHTML;
        heroTitle.style.opacity = '0';
        
        setTimeout(() => {
            heroTitle.style.opacity = '1';
            heroTitle.style.animation = 'fadeInUp 0.8s ease-out';
            sessionStorage.setItem('title-animated', 'true');
        }, 300);
    }

    // Добавляем анимацию fadeInUp если её нет в CSS
    const fadeAnimation = document.createElement('style');
    fadeAnimation.textContent = `
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        /* Дополнительная анимация для карточек с таймаутом */
        @keyframes clipboardGlow {
            0% { border-left-color: #FFA500; }
            50% { border-left-color: #FF8C00; box-shadow: 0 0 10px rgba(255, 165, 0, 0.2); }
            100% { border-left-color: #FFA500; }
        }
        
        .clipboard-highlight {
            animation: clipboardGlow 2s infinite;
        }
    `;
    document.head.appendChild(fadeAnimation);

    console.log("Secure Pass Pro v4.0 Web: UI Animations initialized. Новое: таймаут буфера 10-120 секунд!");
});

// --- ДОПОЛНИТЕЛЬНАЯ АНИМАЦИЯ ПРИ ЗАГРУЗКЕ СТРАНИЦЫ (Preloader эффект) ---
window.addEventListener('load', () => {
    // Убираем возможный белый экран или добавляем класс для body
    document.body.style.visibility = 'visible';
    
    // Небольшая задержка для демонстрации анимации
    setTimeout(() => {
        document.body.classList.add('loaded');
    }, 100);
    
    // Показываем маленькое уведомление в консоли о новой функции
    console.log("%c✨ Secure Pass Pro v4.0 ✨\n%cНовинка: Настраиваемая очистка буфера обмена (10-120 секунд)!", 
                "color: #4EC9B0; font-size: 14px; font-weight: bold;",
                "color: #FFA500; font-size: 12px;");
});

// --- ПЛАВНОЕ ПОЯВЛЕНИЕ СТРАНИЦЫ ---
const pageStyle = document.createElement('style');
pageStyle.textContent = `
    body {
        visibility: hidden;
        transition: visibility 0.1s ease;
    }
    body.loaded {
        visibility: visible;
    }
    
    /* Анимация для кнопки скачивания v4.0 */
    .btn-primary {
        position: relative;
        overflow: hidden;
    }
    
    .btn-primary::after {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 0;
        height: 0;
        background: rgba(255, 255, 255, 0.2);
        border-radius: 50%;
        transform: translate(-50%, -50%);
        transition: width 0.6s, height 0.6s;
    }
    
    .btn-primary:active::after {
        width: 300px;
        height: 300px;
    }
    
    /* Tooltip эффект для бейджей */
    .badge {
        position: relative;
        cursor: help;
    }
    
    .badge:hover::after {
        content: attr(data-tooltip);
        position: absolute;
        bottom: 100%;
        left: 50%;
        transform: translateX(-50%);
        background: #1a1a1a;
        color: #fff;
        padding: 5px 10px;
        border-radius: 8px;
        font-size: 0.7rem;
        white-space: nowrap;
        z-index: 100;
        border: 1px solid #333;
        margin-bottom: 8px;
    }
`;
document.head.appendChild(pageStyle);

// Добавляем data-tooltip для бейджей
document.addEventListener('DOMContentLoaded', () => {
    const tooltipMap = {
        'Clipboard Timeout': 'Очистка буфера: 10-120 секунд (настраивается)',
        'CSPRNG Secrets': 'Криптографически стойкий генератор',
        'Master Password': 'SHA-256 хеширование, 5 попыток',
        'SHA-256 Integrity': 'Контроль целостности файлов'
    };
    
    document.querySelectorAll('.badge').forEach(badge => {
        const text = badge.textContent.trim();
        if (tooltipMap[text]) {
            badge.setAttribute('data-tooltip', tooltipMap[text]);
        }
    });
});