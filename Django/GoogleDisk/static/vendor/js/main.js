//Slide sidebar
document.addEventListener('DOMContentLoaded', function () {
    const sidebar = document.querySelector('.sidebar');
    const navScroller = document.querySelector('.nav-button');
    const toggleSidebar = document.getElementById('toggle-sidebar');

    sidebar.style.left = '0rem';

    toggleSidebar.addEventListener('click', function (event) {
        event.preventDefault();

        sidebar.style.left = (sidebar.style.left === '-40rem') ? '0px' : '-40rem';

        navScroller.style.marginLeft = (navScroller.style.marginLeft === '-12rem') ? '0px' : '-12rem';
    });
});
//Switching the tag color
function toggleColor(element) {
    element.classList.toggle('active-tag');
}
//Changing text on hover
document.addEventListener('DOMContentLoaded', function () {
    var flexContainers = document.querySelectorAll('.flex-container');

    function handleHover(event) {
        var currentFlexContainer = event.currentTarget;

        currentFlexContainer.querySelector('.add-icon').style.setProperty('height', '1.6rem', 'important');
        currentFlexContainer.querySelector('.add-icon').style.setProperty('width', '1.6rem', 'important');
        currentFlexContainer.querySelector('.section-name').style.setProperty('color', '#535353', 'important');
    }

    function handleLeave(event) {
        var currentFlexContainer = event.currentTarget;

        currentFlexContainer.querySelector('.add-icon').style.setProperty('height', '', 'important');
        currentFlexContainer.querySelector('.add-icon').style.setProperty('width', '', 'important');
        currentFlexContainer.querySelector('.section-name').style.setProperty('color', '', 'important');
    }

    flexContainers.forEach(function (flexContainer) {
        flexContainer.addEventListener('mouseover', handleHover);
        flexContainer.addEventListener('mouseout', handleLeave);
    });
});
//Changing text on hover
document.addEventListener('DOMContentLoaded', function () {
    var flexContainers = document.querySelectorAll('.d-flex');

    function handleHover(event) {
        var currentFlexContainer = event.currentTarget;// текущий элемент, на который был совершен ввод мыши

        currentFlexContainer.querySelector('.text-hover').style.setProperty('color', '#383838', 'important');
        currentFlexContainer.querySelector('.note-icon').style.setProperty('height', '2.2rem', 'important');
        currentFlexContainer.querySelector('.note-icon').style.setProperty('width', '2.2rem', 'important');
        currentFlexContainer.querySelector('.note-icon').style.setProperty('margin-right', '0.3rem', 'important');
    }

    function handleLeave(event) {
        var currentFlexContainer = event.currentTarget;

        currentFlexContainer.querySelector('.text-hover').style.setProperty('color', '', 'important');
        currentFlexContainer.querySelector('.note-icon').style.setProperty('height', '', 'important');
        currentFlexContainer.querySelector('.note-icon').style.setProperty('width', '', 'important');
        currentFlexContainer.querySelector('.note-icon').style.setProperty('margin-right', '', 'important');
    }

    flexContainers.forEach(function (flexContainer) {
        flexContainer.addEventListener('mouseover', handleHover);
        flexContainer.addEventListener('mouseout', handleLeave);
    });
});
//Changing text on hover
document.addEventListener('DOMContentLoaded', function () {
    var flexContainers = document.querySelectorAll('.nav-item');

    function handleHover(event) {
        var currentFlexContainer = event.currentTarget;

        currentFlexContainer.querySelector('.sidebar__tagName').style.setProperty('letter-spacing', '0.13rem', 'important');
        currentFlexContainer.querySelector('.sidebar__img').style.setProperty('transform', 'scale(1.07)', 'important');
    }

    function handleLeave(event) {
        var currentFlexContainer = event.currentTarget;

        currentFlexContainer.querySelector('.sidebar__tagName').style.setProperty('letter-spacing', '', 'important');
        currentFlexContainer.querySelector('.sidebar__img').style.setProperty('transform', 'scale(1)', 'important');
    }

    flexContainers.forEach(function (flexContainer) {
        flexContainer.addEventListener('mouseover', handleHover);
        flexContainer.addEventListener('mouseout', handleLeave);
    });
});
//showEditBtn
function showEditBtn(element) {
    // Найти вложенный элемент .edit__btn и добавить ему класс, чтобы показать его
    const editBtn = element.querySelector('.edit__btn');
    if (editBtn) {
        editBtn.classList.add('show');
        editBtn.style.display = 'flex';
    }
}
//hideEditBtn
function hideEditBtn(element) {
    // Найти вложенный элемент .edit__btn и удалить класс, чтобы скрыть его
    const editBtn = element.querySelector('.edit__btn');
    if (editBtn) {
        editBtn.classList.remove('show');
        editBtn.style.display = 'flex';
    }
}

//Switch between inputs when entering a password
function moveToNextInput(currentInput, event) {
    const maxLength = parseInt(currentInput.getAttribute('maxlength'), 10);
    const currentLength = currentInput.value.length;

    if (event.key === 'Backspace' && currentLength === 0) {
        const prevInput = currentInput.previousElementSibling;
        if (prevInput && prevInput.tagName === 'INPUT') {
            prevInput.focus();
            return;
        }
    }

    if (currentLength >= maxLength) {
        const nextInput = currentInput.nextElementSibling;
        if (nextInput && nextInput.tagName === 'INPUT') {
            nextInput.focus();
        }
    }

    if (event.key === 'ArrowLeft') {
        const prevInput = currentInput.previousElementSibling;
        if (prevInput && prevInput.tagName === 'INPUT') {
            prevInput.focus();
        }
    }

    if (event.key === 'ArrowRight' || currentLength >= maxLength) {
        const nextInput = currentInput.nextElementSibling;
        if (nextInput && nextInput.tagName === 'INPUT') {
            nextInput.focus();
        }
    }
}

document.addEventListener('keydown', function (event) {
    const focusedInput = document.activeElement;
    if (focusedInput && focusedInput.classList.contains('passEnter__input')) {
        moveToNextInput(focusedInput, event);
    }
});


// Function that will be called when clicking on the image to make it bigger
function imageClickHandler(event) {
    var overlay = document.getElementById('overlay');
    var clickedImage = event.target;

    if (clickedImage.classList.contains('clickable')) {
        var clonedImage = clickedImage.cloneNode(true);

        clonedImage.style.height = '35rem';
        clonedImage.style.width = '35rem';
        clonedImage.style.transition = '';
        clonedImage.style.cursor = '';
        clonedImage.style.transform = 'scale(1)';
        clonedImage.style.cursor = 'default';

        overlay.innerHTML = '';
        overlay.appendChild(clonedImage);
        overlay.style.height = '100%';
        overlay.style.width = '100%';
        overlay.style.display = overlay.style.display === 'flex' ? 'none' : 'flex';
    }
}

// Get the parent element for all images
var parentElement = document.getElementById('imageContainer');

// Add an event handler to the parent element
parentElement.addEventListener('click', imageClickHandler);

// Add an event handler for pressing the Esc key
document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') {
        var overlay = document.getElementById('overlay');
        overlay.style.display = 'none';
    }
});

const video = document.querySelector('.videoContent');
const customButton = document.querySelector('.custom-button');

document.addEventListener('DOMContentLoaded', function () {
    var scrollToTopBtn = document.getElementById('scrollToTopBtn');

    scrollToTopBtn.addEventListener('click', function (e) {
        e.preventDefault();
        scrollToTop();
    });

    function scrollToTop() {
        document.body.scrollTop = 0; // For Safari
        document.documentElement.scrollTop = 0; // For Chrome, Firefox, IE, and Opera
    }
});

// Change text (change password)
document.getElementById('forgotPasswordBtn').addEventListener('click', function () {
    var link = this;

    setTimeout(function () {
        link.innerText = 'Пароль надіслано на пошту';
    }, 500);
});