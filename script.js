// Ждем полной загрузки контента
document.addEventListener("DOMContentLoaded", () => {
    
    // Опции для наблюдателя (Observer)
    const observerOptions = {
        threshold: 0.1 // Анимация начнется, когда 10% карточки появится на экране
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // При появлении в зоне видимости
                entry.target.style.opacity = "1";
                entry.target.style.transform = "translateY(0)";
                // Прекращаем наблюдение за этой карточкой после активации анимации
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Выбираем все карточки (в нашем HTML это класс .card)
    const cards = document.querySelectorAll('.card, .download-card');

    cards.forEach((card, index) => {
        // Устанавливаем начальное состояние (скрыто)
        card.style.opacity = "0";
        card.style.transform = "translateY(30px)";
        card.style.transition = `all 0.6s ease-out ${index * 0.1}s`; // Добавляем небольшую задержку для каждой следующей карточки
        
        // Начинаем слежку
        observer.observe(card);
    });

    console.log("Secure Pass Pro Web: UI Animations initialized.");
});