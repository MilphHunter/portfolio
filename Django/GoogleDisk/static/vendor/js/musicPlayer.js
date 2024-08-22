// Switch playback buttons
function togglePlayPause(button) {
    const music = button.closest('.card').querySelector('.music');
    const pButton = button.querySelector('.pButton');

    if (music.paused) {
        music.play();
        pButton.classList.remove('fa-play');
        pButton.classList.add('fa-pause');
        pButton.src = "/static/vendor/img/icon/pause-button.png";
    } else {
        music.pause();
        pButton.classList.remove('fa-pause');
        pButton.classList.add('fa-play');
        pButton.src = "/static/vendor/img/icon/play-button.png";
    }
}

// Music skip
function updateTime(timeline, e) {
    e = e || window.event;
    const music = timeline.closest('.card').querySelector('.music');
    const timelineRect = timeline.getBoundingClientRect();

    let percent = (e.clientX - timelineRect.left) / timelineRect.width;

    if (percent < 0) {
        percent = 0;
    } else if (percent > 1) {
        percent = 1;
    }
    music.currentTime = percent * music.duration;
}


var parentElement = document;

parentElement.addEventListener('click', function(event) {
    if (event.target.classList.contains('playhead')) {
        updateTime(event.target.closest('.timeline'), event);
    }
});

function updateInterface(music, playhead, pButton) {
    music.currentTime = 0;
    pButton.classList.remove('fa-pause');
    pButton.classList.add('fa-play');
    pButton.src = '/static/vendor/img/icon/play-button.png';
}

document.getElementById('audio-tab-pane').addEventListener('click', function (e) {
    const target = e.target;

    if (target.classList.contains('timeline')) {
        updateTime(target, e);
    }

    if (target.classList.contains('audioplayer')) {
        togglePlayPause(target);
    }
});

// Function for adding event handlers and bindings to elements
function addEventListenersToNewElements() {
    document.querySelectorAll('.audioplayer').forEach(function (player) {
        const music = player.closest('.card').querySelector('.music');
        const playhead = player.querySelector('.playhead');
        const timeline = player.querySelector('.timeline');
        const pButton = player.querySelector('.pButton');

        music.addEventListener('timeupdate', function () {
            const timelineWidth = timeline.offsetWidth;
            const playPercent = (timelineWidth * (music.currentTime / music.duration));
            playhead.style.width = playPercent + 'px';
        });

        music.addEventListener('ended', function () {
            updateInterface(music, playhead, pButton);
        });
    });
}

// Add an event handler that will call a function to update event handlers and element bindings
document.body.addEventListener('click', function (event) {
    if (event.target.classList.contains('audioplayer')) {
        addEventListenersToNewElements();
    }
});

// Call the function to add event handlers and element bindings for existing elements
addEventListenersToNewElements();