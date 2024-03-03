//Input files without update
function uploadFile() {
    var csrftoken = document.cookie.match(/csrftoken=([\w-]+)/)[1];
    var formData = new FormData();
    var fileInput = document.getElementById('fileInput');
    for (var i = 0; i < fileInput.files.length; i++) {
        formData.append('file', fileInput.files[i]);
    }
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/workspace/note/upload/', true);
    xhr.setRequestHeader('X-CSRFToken', csrftoken);
    xhr.onload = function () {
        if (xhr.status === 200) {
            var response = JSON.parse(xhr.responseText);
            var keys = Object.keys(response.files)
            keys.forEach(function (key) {
                if (Array.isArray(response.files[key]) && response.files[key].length > 0) {
                    if (key === 'note_img') {
                        updateImageListAfterInput(response.files[key])
                    } else if (key === 'note_video') {
                        updateVideoList(response.files[key])
                    } else if (key === 'note_audio') {
                        updateAudioList(response.files[key])
                    } else if (key === 'note_other') {
                        updateOtherList(response.files[key])
                    }
                }
            })
        }
    };
    xhr.send(formData);
}

function updateImageListAfterInput(img) {
    const imageContainer = document.getElementById('imageContainer');
    imageContainer.innerHTML = ''; // Очистить контейнер перед добавлением новых файлов

    img.forEach(function (file) {
        const imgElement = document.createElement('img');
        imgElement.src = file;
        imgElement.className = 'rounded imageContent ms-2 mt-3 mb-1 clickable';
        imgElement.alt = 'Card image';

        const closeButton = document.createElement('button');
        closeButton.type = 'button';
        closeButton.className = 'btn-close position-absolute close_img_btn';
        closeButton.setAttribute('data-file', file);
        closeButton.setAttribute('data-type', 'img');
        closeButton.setAttribute('aria-label', 'Close');

        const div = document.createElement('div');
        div.className = 'position-relative';
        div.appendChild(imgElement);
        div.appendChild(closeButton);
        imageContainer.appendChild(div);
    });

    var divOverlay = document.createElement('div');
    divOverlay.setAttribute('id', 'overlay');
    divOverlay.className = 'overlay';
    imageContainer.appendChild(divOverlay);
}

function updateVideoList(video) {
    var videoContainer = document.getElementById('videoContainer');
    videoContainer.innerHTML = ''; // Очистить контейнер перед добавлением новых файлов

    video.forEach(function (file) {
        var videoElement = document.createElement('video');
        videoElement.className = 'videoContent';
        videoElement.controls = true;
        var source = document.createElement('source');
        source.src = file;
        source.type = 'video/mp4';
        videoElement.appendChild(source)

        var divCustomControls = document.createElement('div')
        divCustomControls.className = 'custom-controls'
        var closeButton = document.createElement('button');
        closeButton.type = 'button';
        closeButton.className = 'btn-close position-absolute close_vid_btn';
        closeButton.setAttribute('data-file', file);
        closeButton.setAttribute('data-type', 'video');
        closeButton.setAttribute('aria-label', 'Close');
        divCustomControls.appendChild(closeButton)

        var div = document.createElement('div');
        div.className = 'ms-2 custom-video-player position-relative';
        div.appendChild(videoElement);
        div.appendChild(divCustomControls);
        videoContainer.appendChild(div);
    });
}

function updateAudioList(audio) {
    let audioContainer = document.getElementById('audioContainer');
    audioContainer.innerHTML = ''; // Очистить контейнер перед добавлением новых файлов

    audio.forEach(function (file) {
        let divTop = document.createElement('div');
        divTop.className = 'bg-image hover-overlay ripple';
        divTop.setAttribute('data-mdb-ripple-color', 'light');
        let audioImg = document.createElement('img');
        audioImg.className = 'card-img-top'
        audioImg.className = 'card-img-top'
        audioImg.src = file['note_audio_img'] ? file['note_audio_img'] : "/static/vendor/img/icon/music_img.png";
        audioImg.alt = 'Card image cap'
        divTop.appendChild(audioImg)

        let divClose = document.createElement('div');
        divClose.className = 'custom-controls';
        let closeButton = document.createElement('button');
        closeButton.type = 'button';
        closeButton.className = 'btn-close position-absolute close_aud_btn';
        closeButton.setAttribute('data-file', file['note_audio']);
        closeButton.setAttribute('data-type', 'audio');
        closeButton.setAttribute('aria-label', 'Close');
        divClose.appendChild(closeButton);


        let divMiddle = document.createElement('div');
        divMiddle.className = 'card-body text-center';
        let titleName = document.createElement('h5')
        titleName.className = 'h5 font-weight-bold';
        titleName.innerText = file['note_audio_title']
        let titleAuthor = document.createElement('p');
        titleAuthor.className = 'mb-0';
        titleAuthor.innerText = file['note_audio_author'];
        let audioMusic = document.createElement('audio');
        audioMusic.className = 'music';
        let audioSource = document.createElement('source');
        audioSource.src = file['note_audio_url'];
        audioMusic.appendChild(audioSource);

        let divDown = document.createElement('div');
        divDown.className = 'audioplayer';
        let control = document.createElement('a');
        control.addEventListener("click", function () {
            togglePlayPause(control);
        });
        control.className = 'audioplayer';
        let playBtn = document.createElement('img');
        playBtn.src = "/static/vendor/img/icon/play-button.png";
        playBtn.className = 'pButton fas fa-play';
        playBtn.alt = 'playBtn';
        playBtn.addEventListener("click", function () {
            addEventListenersToNewElements();
        });
        control.appendChild(playBtn);
        let timeline = document.createElement('div');
        timeline.className = 'timeline';
        let playHead = document.createElement('div');
        playHead.className = 'playhead';
        timeline.appendChild(playHead);
        timeline.onclick = function (event) {
            updateTime(this, event);
        };
        divDown.appendChild(control);
        divDown.appendChild(timeline);

        divMiddle.appendChild(titleName);
        divMiddle.appendChild(titleAuthor);
        divMiddle.appendChild(audioMusic);
        divMiddle.appendChild(divDown);
        let divCard = document.createElement('div');
        divCard.className = 'card';
        divCard.appendChild(divTop);
        divCard.appendChild(divClose);
        divCard.appendChild(divMiddle);
        let divAll = document.createElement('div');
        divAll.className = 'mobile-box me-2 position-relative';
        divAll.appendChild(divCard);
        audioContainer.appendChild(divAll);
    });
}

function updateOtherList(other) {
    const otherContainer = document.getElementById('otherContainer');
    otherContainer.innerHTML = '';

    other.forEach(function (file) {
        const fileImg = document.createElement('img');
        fileImg.src = '/static/vendor/img/icon/file.png';
        fileImg.className = 'border-bottom';
        fileImg.alt = 'file-img';

        const divBody = document.createElement('div');
        divBody.className = 'card-body'
        const divClose = document.createElement('div');
        divClose.className = 'custom-controls';
        const closeButton = document.createElement('button');
        closeButton.type = 'button';
        closeButton.className = 'btn-close position-absolute close_file_btn';
        closeButton.setAttribute('data-file', file['note_other_name']);
        closeButton.setAttribute('data-type', 'other');
        closeButton.setAttribute('aria-label', 'Close');
        divClose.appendChild(closeButton);
        const cardText = document.createElement('p');
        cardText.className = 'card-text';
        cardText.innerText = file['note_other_name'].startsWith('/content/') ? file['note_other_name'].slice(9) : file['note_other_name'];
        const divDownload = document.createElement('div');
        divDownload.className = 'd-flex justify-content-between align-items-center';
        const divGroup = document.createElement('div');
        divGroup.className = 'btn-group';
        const downloadBtn = document.createElement('button');
        downloadBtn.id = 'downloadBtn';
        downloadBtn.setAttribute('data-file-path', '/content/files/other/' + file['note_other_name']);
        downloadBtn.setAttribute('data-file-name', file['note_other_name']);
        downloadBtn.className = 'btn btn-sm btn-outline-secondary btn-download';
        downloadBtn.innerText = 'Download'
        divGroup.appendChild(downloadBtn);
        const smallText = document.createElement('small');
        smallText.className = 'text-muted';
        smallText.innerText = file['note_other_size'] + 'mb';
        divDownload.appendChild(divGroup);
        divDownload.appendChild(smallText);
        divBody.appendChild(divClose);
        divBody.appendChild(cardText);
        divBody.appendChild(divDownload);

        const divAll = document.createElement('div');
        divAll.className = 'card shadow-sm mt-3 mb-1 ms-3 file_card';
        divAll.appendChild(fileImg);
        divAll.appendChild(divBody);
        otherContainer.appendChild(divAll);
    });
}

//DeleteFIle
$(document).on('click', '.btn-close', function () {
    var csrftoken = document.cookie.match(/csrftoken=([\w-]+)/)[1];
    var fileToDelete = $(this).data('file');
    var fileType = $(this).data('type');
    $.ajax({
        url: '/workspace/note/file-delete/',
        method: 'POST',
        headers: {'X-CSRFToken': csrftoken},
        data: {'fileToDelete': fileToDelete, 'fileType': fileType},
        success: function (response) {
            console.log(response);
            updateImageListAfterDelete(fileToDelete, fileType);
        },
        error: function (error) {
            console.error(error);
        }
    });
});

function updateImageListAfterDelete(fileToDelete, fileType) {
    if (fileType === 'img') {
        var deletedFile = $('[data-file="' + fileToDelete + '"]');
        deletedFile.parent().first().remove();
    } else if (fileType === 'video') {
        $('[data-file="' + fileToDelete + '"]').closest('.custom-video-player').first().remove();
    } else if (fileType === 'audio') {
        console.log(fileToDelete)
        $('[data-file="' + CSS.escape(fileToDelete) + '"]').closest('.mobile-box').first().remove();
    } else {
        $('[data-file="' + fileToDelete + '"]').closest('.file_card').first().remove();
    }
}

//Sending a file to the user by pressing the button
document.addEventListener('click', function (event) {
    if (event.target && event.target.classList.contains('btn-download')) {
        let button = event.target;
        let filePath = button.getAttribute('data-file-path');
        let fileName = button.getAttribute('data-file-name');
        let downloadLink = document.createElement('a');
        downloadLink.href = filePath;
        downloadLink.download = fileName;
        document.body.appendChild(downloadLink);
        downloadLink.click();
        document.body.removeChild(downloadLink);
    }
});