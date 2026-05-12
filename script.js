// Secure Pass Pro v4.0 - Premium UI Animations
// Анимации при прокрутке, плавное появление элементов
// Выпадающее меню, модальное окно "О нас", подсветка активного пункта

document.addEventListener("DOMContentLoaded", () => {
    
    // --- ВЫПАДАЮЩЕЕ МЕНЮ С ЗАДЕРЖКОЙ (не закрывается сразу) ---
    const dropdowns = document.querySelectorAll('.dropdown');
    let closeTimeout;
    
    dropdowns.forEach(dropdown => {
        const dropdownContent = dropdown.querySelector('.dropdown-content');
        
        if (dropdownContent) {
            dropdown.addEventListener('mouseenter', () => {
                clearTimeout(closeTimeout);
                dropdownContent.style.display = 'block';
            });
            
            dropdown.addEventListener('mouseleave', () => {
                closeTimeout = setTimeout(() => {
                    dropdownContent.style.display = 'none';
                }, 200);
            });
            
            // Чтобы подменю не закрывалось при наведении на него
            dropdownContent.addEventListener('mouseenter', () => {
                clearTimeout(closeTimeout);
            });
            
            dropdownContent.addEventListener('mouseleave', () => {
                closeTimeout = setTimeout(() => {
                    dropdownContent.style.display = 'none';
                }, 200);
            });
        }
    });
    
    // --- МОДАЛЬНОЕ ОКНО "О НАС" ---
    const modal = document.getElementById('github-modal');
    const aboutBtn = document.getElementById('about-btn');
    const closeBtn = document.getElementById('close-modal');
    
    if (aboutBtn && modal) {
        aboutBtn.onclick = function(e) {
            e.preventDefault();
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        };
    }
    
    if (closeBtn && modal) {
        closeBtn.onclick = function() {
            modal.classList.remove('active');
            document.body.style.overflow = 'auto';
        };
    }
    
    if (modal) {
        window.onclick = function(e) {
            if (e.target == modal) {
                modal.classList.remove('active');
                document.body.style.overflow = 'auto';
            }
        };
    }
    
    // --- ОПЦИИ ДЛЯ НАБЛЮДАТЕЛЯ (Observer) ---
    const observerOptions = {
        threshold: 0.1,
        rootMargin: "0px 0px -50px 0px"
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = "1";
                entry.target.style.transform = "translateY(0)";
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // --- ВЫБИРАЕМ ВСЕ ЭЛЕМЕНТЫ ДЛЯ АНИМАЦИИ ---
    const animatedElements = document.querySelectorAll('.card, .download-card, .tech-item');
    
    // Hero-контент
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
        element.style.opacity = "0";
        element.style.transform = "translateY(30px)";
        element.style.transition = `all 0.6s cubic-bezier(0.4, 0, 0.2, 1) ${index * 0.08}s`;
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
                const secondaryNav = document.querySelector('.nav-secondary');
                const extraOffset = secondaryNav ? secondaryNav.offsetHeight : 0;
                const targetPosition = targetElement.getBoundingClientRect().top + window.pageYOffset - headerHeight - extraOffset;
                
                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
                
                history.pushState(null, null, targetId);
            }
        });
    });

    // --- ПОДСВЕТКА АКТИВНОГО ПУНКТА МЕНЮ ПРИ ПРОКРУТКЕ ---
    const sections = document.querySelectorAll('section[id]');
    const navLinks = document.querySelectorAll('nav ul li a');
    const secondaryLinks = document.querySelectorAll('.nav-secondary ul li a');
    const allNavLinks = [...navLinks, ...secondaryLinks];
    
    if (sections.length > 0 && allNavLinks.length > 0) {
        window.addEventListener('scroll', () => {
            let current = '';
            const scrollPosition = window.scrollY + 120;
            
            sections.forEach(section => {
                const sectionTop = section.offsetTop;
                const sectionHeight = section.offsetHeight;
                
                if (scrollPosition >= sectionTop && scrollPosition < sectionTop + sectionHeight) {
                    current = section.getAttribute('id');
                }
            });
            
            allNavLinks.forEach(link => {
                link.classList.remove('active');
                const href = link.getAttribute('href');
                if (href && href.substring(1) === current) {
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
        
        .nav-secondary ul li a.active {
            color: var(--accent-color, #4EC9B0);
        }
        
        .hero-content, .hero-image {
            will-change: transform, opacity;
        }
    `;
    document.head.appendChild(style);

    // --- ЗАЩИТА ОТ ДРОЖАНИЯ ПРИ РЕСАЙЗЕ ---
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
    const downloadBtns = document.querySelectorAll('.btn-primary, .btn-secondary, .download-btn-small');
    downloadBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            console.log(`Secure Pass Pro v4.0: Download clicked - ${btn.textContent}`);
            
            btn.style.transform = 'scale(0.98)';
            setTimeout(() => {
                btn.style.transform = '';
            }, 150);
        });
    });

    // --- ЭФФЕКТ ПЕЧАТИ ДЛЯ ЗАГОЛОВКА ---
    const heroTitle = document.querySelector('.hero h1');
    if (heroTitle && !sessionStorage.getItem('title-animated')) {
        heroTitle.style.opacity = '0';
        setTimeout(() => {
            heroTitle.style.opacity = '1';
            heroTitle.style.animation = 'fadeInUp 0.8s ease-out';
            sessionStorage.setItem('title-animated', 'true');
        }, 300);
    }

    // --- ДОБАВЛЯЕМ АНИМАЦИИ ---
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
        
        @keyframes clipboardGlow {
            0% { border-left-color: #FFA500; }
            50% { border-left-color: #FF8C00; box-shadow: 0 0 10px rgba(255, 165, 0, 0.2); }
            100% { border-left-color: #FFA500; }
        }
        
        .clipboard-highlight {
            animation: clipboardGlow 2s infinite;
        }
        
        /* Анимация для появления карточек */
        .card, .download-card, .tech-item {
            transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
        }
    `;
    document.head.appendChild(fadeAnimation);

    console.log("Secure Pass Pro v4.0 Web: UI Animations initialized. Выпадающее меню работает корректно!");

    // --- ДОБАВЛЯЕМ ТУЛТИПЫ ДЛЯ БЕЙДЖЕЙ ---
    const tooltipMap = {
        'Clipboard Timeout 10-120s': 'Очистка буфера: 10-120 секунд (настраивается)',
        'CSPRNG Secrets': 'Криптографически стойкий генератор',
        'Master Password PBKDF2': 'PBKDF2 хеширование, 100,000 итераций, 5 попыток',
        'SHA-256 Integrity': 'Контроль целостности файлов SHA-256'
    };
    
    document.querySelectorAll('.badge').forEach(badge => {
        const text = badge.textContent.trim();
        if (tooltipMap[text]) {
            badge.setAttribute('data-tooltip', tooltipMap[text]);
        }
    });
    
    // Стили для тултипов
    const tooltipStyle = document.createElement('style');
    tooltipStyle.textContent = `
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
            pointer-events: none;
        }
        
        /* Анимация для кнопок */
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
    `;
    document.head.appendChild(tooltipStyle);
});

// --- ПЛАВНОЕ ПОЯВЛЕНИЕ СТРАНИЦЫ ---
window.addEventListener('load', () => {
    document.body.style.visibility = 'visible';
    
    setTimeout(() => {
        document.body.classList.add('loaded');
    }, 100);
    
    console.log("%c✨ Secure Pass Pro v4.0 ✨\n%cНовинка: Настраиваемая очистка буфера обмена (10-120 секунд)!\n%cНовинка: RGB анимация границ окна!\n%cНовинка: Кроссплатформенный звук (Windows/Mac/Linux)!", 
                "color: #4EC9B0; font-size: 14px; font-weight: bold;",
                "color: #FFA500; font-size: 12px;",
                "color: #00AAFF; font-size: 12px;",
                "color: #2ECC71; font-size: 12px;");
});

// Стили для body
const pageStyle = document.createElement('style');
pageStyle.textContent = `
    body {
        visibility: hidden;
        transition: visibility 0.1s ease;
    }
    body.loaded {
        visibility: visible;
    }
`;
document.head.appendChild(pageStyle);