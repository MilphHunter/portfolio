/* ========== toggle style switcher ========== */
const styleSwitcherToggle = document.querySelector(".style-switcher-toggler");
styleSwitcherToggle.addEventListener("click", () => {
    document.querySelector(".style-switcher").classList.toggle("open");
})

// hide style switcher on scroll
window.addEventListener("scroll", () => {
    if (document.querySelector(".style-switcher").classList.contains("open")) {
        document.querySelector(".style-switcher").classList.remove("open");
    }
})

/* ========== theme light and dark mode ========== */
// Функция для установки куки
function setCookie(name, value, days) {
    const date = new Date();
    date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
    const expires = "expires=" + date.toUTCString();
    document.cookie = name + "=" + value + ";" + expires + ";path=/";
}

// Функция для получения куки
function getCookie(name) {
    const nameEQ = name + "=";
    const ca = document.cookie.split(';');
    for (let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) === ' ') c = c.substring(1, c.length);
        if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
    }
    return null;
}

const dayNight = document.querySelector(".day-night");

dayNight.addEventListener("click", () => {
    dayNight.querySelector("i").classList.toggle("fa-sun");
    dayNight.querySelector("i").classList.toggle("fa-moon");
    document.body.classList.toggle("dark");

    // Сохраняем состояние темы в куки
    if (document.body.classList.contains("dark")) {
        setCookie("theme", "dark", 7); // Сохраняем тему "dark" на 7 дней
    } else {
        setCookie("theme", "light", 7); // Сохраняем тему "light" на 7 дней
    }
});

window.addEventListener("load", () => {
    // Проверяем, есть ли куки с темой и применяем её
    const savedTheme = getCookie("theme");
    if (savedTheme) {
        if (savedTheme === "dark") {
            document.body.classList.add("dark");
            dayNight.querySelector("i").classList.add("fa-sun");
            dayNight.querySelector("i").classList.remove("fa-moon");
        } else {
            document.body.classList.remove("dark");
            dayNight.querySelector("i").classList.add("fa-moon");
            dayNight.querySelector("i").classList.remove("fa-sun");
        }
    } else {
        // Если куки нет, ставим значок в зависимости от текущей темы
        if (document.body.classList.contains("dark")) {
            dayNight.querySelector("i").classList.add("fa-sun");
        } else {
            dayNight.querySelector("i").classList.add("fa-moon");
        }
    }
});

/* ========== save the current style using cookies ========== */
$(document).ready(function () {
    // Function for setting cookies
    function setCookie(name, value, days) {
        const date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        const expires = "expires=" + date.toUTCString();
        document.cookie = name + "=" + value + ";" + expires + ";path=/";
    }

    // Function for obtaining cookies
    function getColorName(name) {
        const nameEQ = name + "=";
        const ca = document.cookie.split(';');
        for (let i = 0; i < ca.length; i++) {
            let c = ca[i];
            while (c.charAt(0) === ' ') c = c.substring(1, c.length);
            if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
        }
        return null;
    }

    // Applying a saved style on page load
    const savedStyle = getColorName('selectedStyle');
    if (savedStyle) {
        applyStyle(savedStyle);
    }

    // Function for applying the style
    function applyStyle(styleName) {
        $('link.alternate-style').each(function () {
            this.disabled = true;
            if (this.getAttribute('title') === styleName) {
                this.disabled = false;
            }
        });
    }

    // When you select a style, save it to a cookie and apply it
    $('.style-switcher-button').on('click', function () {
        const styleName = $(this).data('style');
        applyStyle(styleName);
        setCookie('selectedStyle', styleName, 7);
    });
});
