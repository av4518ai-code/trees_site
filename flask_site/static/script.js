// Скрипт для плавного появления карточек при скролле
document.addEventListener('DOMContentLoaded', function() {
    // Находим все карточки
    const cards = document.querySelectorAll('.card');
    
    // Настраиваем Intersection Observer
    const observerOptions = {
        root: null, // viewport
        rootMargin: '0px',
        threshold: 0.1 // когда 10% карточки видно
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                // Добавляем класс для анимации появления
                entry.target.classList.add('visible');
                // Перестаём наблюдать после появления
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    // Начинаем наблюдение за каждой карточкой
    cards.forEach(function(card, index) {
        // Добавляем задержку для каскадного появления
        card.style.transitionDelay = (index * 0.1) + 's';
        observer.observe(card);
    });
});