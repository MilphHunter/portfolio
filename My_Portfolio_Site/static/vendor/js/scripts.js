/* ========== typing animation ========== */
document.addEventListener('DOMContentLoaded', function () {
    var options = {
        strings: ["Python Back-end Developer", "Python Developer", "Good Guy"],
        typeSpeed: 100,
        backSpeed: 60,
        loop: true
    };

    var typed = new Typed(".typing", options);
});

/* ========== change active page on click ========== */
const btns = document.querySelectorAll(".compas");

function setActivePage(page) {
    var links = document.querySelectorAll('a.compas');
    links.forEach(function (link) {
        link.classList.remove('active');
    });
    page.classList.add('active');
}

/* ========== change active page on scroll ========== */
function setActiveSection() {
    let sections = document.querySelectorAll('section');
    let navLinks = document.querySelectorAll('ul li a');

    let currentSection = '';

    sections.forEach(section => {
        let sectionTop = section.offsetTop;
        let sectionHeight = section.clientHeight;

        if (pageYOffset >= (sectionTop - sectionHeight / 3)) {
            currentSection = section.getAttribute('id');
        }
    });

    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href').includes(currentSection)) {
            link.classList.add('active');
        }
    });
}

window.addEventListener('scroll', setActiveSection);

/* ========== send message to gmail ========== */
$(document).ready(function () {
    // Function for setting cookies
    function setCookie(name, value, seconds) {
        const date = new Date();
        date.setTime(date.getTime() + (seconds * 1000));
        const expires = "expires=" + date.toUTCString();
        document.cookie = name + "=" + value + ";" + expires + ";path=/";
    }

    // Function for getting cookies
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

    const $submitButton = $('#sendMailForm').find('button[type="submit"]');

    // Check if there is a timer in the cookie
    const timerCookie = getCookie('submitTimer');
    if (timerCookie) {
        const endTime = parseInt(timerCookie);
        const currentTime = Date.now();
        const remainingTime = endTime - currentTime;

        if (remainingTime > 0) {
            $submitButton.addClass('inactive').removeClass('btn');
            $('#message').text(`PLEASE WAIT ${Math.ceil(remainingTime / 1000)} SECONDS BEFORE SENDING ANOTHER MESSAGE.`);
            setTimeout(function () {
                $submitButton.removeClass('inactive').addClass('btn');
                document.cookie = "submitTimer=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
            }, remainingTime);
        }
    }

    $('#sendMailForm').on('submit', function (event) {
        event.preventDefault();

        if ($submitButton.hasClass('inactive')) {
                alert("PLEASE WAIT BEFORE SENDING ANOTHER MESSAGE.");
            return;
        }

        const csrftoken = document.cookie.match(/csrftoken=([\w-]+)/)[1];
        const formData = {
            email_name: $('#id_email_name').val(),
            email_email: $('#id_email_email').val(),
            email_subject: $('#id_email_subject').val(),
            email_text: $('#id_email_text').val(),
        };

        $.ajax({
            url: '/send-email/',
            method: 'POST',
            contentType: 'application/json',
            headers: {'X-CSRFToken': csrftoken},
            data: JSON.stringify(formData),
            success: function (response) {
                $('#message').text(response.message);
                if (response.success) {
                    $('#message').css('color', 'green');
                } else {
                    $('#message').css('color', 'red');
                }

                $submitButton.addClass('inactive').removeClass('btn');

                // Set the timer for 120 seconds
                const blockTime = Date.now() + (120 * 1000);
                setCookie('submitTimer', blockTime, 120);

                setTimeout(function () {
                    $submitButton.removeClass('inactive').addClass('btn');
                    document.cookie = "submitTimer=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
                }, 120 * 1000);
            }
        });
    });
});
