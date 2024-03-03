// Change the value depending on the pressed folder
function sendFolderData(folderName) {
    var csrftoken = document.cookie.match(/csrftoken=([\w-]+)/)[1];
    // Отправляем данные на сервер с помощью AJAX-запроса
    $.ajax({
        url: 'http://127.0.0.1:8000/workspace/note/add-folder/',
        method: 'POST',
        headers: {'X-CSRFToken': csrftoken},
        data: {'folder_name': folderName},
        success: function (response) {
            console.log(response);
        },
        error: function (error) {
            console.error(error);
        }
    });
}

document.addEventListener('DOMContentLoaded', function () {
    const folderButtons = document.querySelectorAll('.folder-btn');
    const folderBtn = document.getElementById('folder-btn');
    const folderImg = document.getElementById('folder-img');
    folderButtons.forEach(function (button) {
        button.addEventListener('click', function (event) {
            const folder = button.dataset.folder;
            const imgSrc = button.dataset.img;
            folderBtn.innerText = folder;
            folderImg.src = imgSrc;
        });
    });
});