function toggleTheme() {
    const htmlEl = document.documentElement;
    const currentTheme = htmlEl.getAttribute('data-bs-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    htmlEl.setAttribute('data-bs-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
}

function updateThemeIcon(theme) {
    const icon = document.getElementById('themeIcon');
    if (icon) {
        if (theme === 'dark') {
            icon.className = 'bi bi-sun-fill text-warning';
        } else {
            icon.className = 'bi bi-moon-stars-fill';
        }
    }
}

function toggleAccessibility() {
    document.body.classList.toggle('accessibility-mode');
    const isAccess = document.body.classList.contains('accessibility-mode');
    localStorage.setItem('accessibility', isAccess ? 'true' : 'false');
}

function changeLanguage(lang) {
    localStorage.setItem('selectedLang', lang);
    document.getElementById('currentLang').innerText = lang.toUpperCase();

    const elements = document.querySelectorAll('[data-lang-' + lang + ']');
    elements.forEach(el => {
        el.innerText = el.getAttribute('data-lang-' + lang);
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-bs-theme', savedTheme);
    updateThemeIcon(savedTheme);

    if (localStorage.getItem('accessibility') === 'true') {
        document.body.classList.add('accessibility-mode');
    }

    const savedLang = localStorage.getItem('selectedLang') || 'kz';
    changeLanguage(savedLang);
});