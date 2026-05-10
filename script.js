// Secure Pass Pro v3.9 - Premium UI Animations
// Анимации при прокрутке, плавное появление элементов

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

    // --- ОБРАБОТЧИК ДЛЯ КНОПОК СКАЧИВАНИЯ (опционально) ---
    const downloadBtns = document.querySelectorAll('.btn-primary, .btn-secondary');
    downloadBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            // Можно добавить аналитику или дополнительную логику здесь
            console.log(`Download clicked: ${btn.textContent}`);
        });
    });

    console.log("Secure Pass Pro v3.9 Web: UI Animations initialized.");
});

// --- ДОПОЛНИТЕЛЬНАЯ АНИМАЦИЯ ПРИ ЗАГРУЗКЕ СТРАНИЦЫ (Preloader эффект) ---
window.addEventListener('load', () => {
    // Убираем возможный белый экран или добавляем класс для body
    document.body.style.visibility = 'visible';
    
    // Небольшая задержка для демонстрации анимации
    setTimeout(() => {
        document.body.classList.add('loaded');
    }, 100);
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
`;
document.head.appendChild(pageStyle);