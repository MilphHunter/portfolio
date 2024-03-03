const createTagBtn = document.getElementById('createTagBtn');
const tagForm = document.getElementById('tagForm');

const createFolderBtn = document.getElementById('createFolderBtn');
const folderForm = document.getElementById('folderForm');

const createTagBtn1 = document.getElementById('createTagBtn1');
const createFolderBtn1 = document.getElementById('createFolderBtn1');

const createTagBtn2 = document.getElementById('createTagBtn2');
const createFolderBtn2 = document.getElementById('createFolderBtn2');

const createPassBtn = document.getElementById('createPassBtn');
const passForm = document.getElementById('passForm');

//Open form for adding tags/folders
document.addEventListener('DOMContentLoaded', function () {
    var createTagBtn = document.getElementById('createTagBtn');

    createTagBtn.addEventListener('click', function (event) {
        event.preventDefault();
        tagForm.classList.toggle('show-form');
        tagForm.classList.remove('close-form');
        folderForm.classList.add('close-form');
        folderForm.classList.remove('show-form');
        passForm.classList.add('close-form');
        passForm.classList.remove('show-form');
    });
});

//Close by pressing Escape
document.addEventListener('keydown', function (e) {
    if (e.keyCode == 27) {
        tagForm.classList.add('close-form');
        tagForm.classList.remove('show-form');
    }
});

//Open form for adding tags/folders
document.addEventListener('DOMContentLoaded', function () {

    createFolderBtn.addEventListener('click', function (event) {
        event.preventDefault();
        folderForm.classList.toggle('show-form');
        folderForm.classList.remove('close-form');
        tagForm.classList.add('close-form');
        tagForm.classList.remove('show-form');
        passForm.classList.add('close-form');
        passForm.classList.remove('show-form');
    });
});

//Close by pressing Escape
document.addEventListener('keydown', function (e) {
    if (e.keyCode == 27) {
        folderForm.classList.add('close-form');
        folderForm.classList.remove('show-form');
    }
});

//Open form for adding tags/folders
document.addEventListener('DOMContentLoaded', function () {

    createTagBtn1.addEventListener('click', function (event) {
        event.preventDefault();
        tagForm.classList.toggle('show-form');
        tagForm.classList.remove('close-form');
        folderForm.classList.add('close-form');
        folderForm.classList.remove('show-form');
        passForm.classList.add('close-form');
        passForm.classList.remove('show-form');
    });
});

//Open form for adding tags/folders
document.addEventListener('DOMContentLoaded', function () {

    createFolderBtn1.addEventListener('click', function (event) {
        event.preventDefault();
        folderForm.classList.toggle('show-form');
        folderForm.classList.remove('close-form');
        tagForm.classList.add('close-form');
        tagForm.classList.remove('show-form');
        passForm.classList.add('close-form');
        passForm.classList.remove('show-form');
    });
});

//Open form for adding tags/folders
document.addEventListener('DOMContentLoaded', function () {

    createTagBtn2.addEventListener('click', function (event) {
        event.preventDefault();
        tagForm.classList.toggle('show-form');
        tagForm.classList.remove('close-form');
        folderForm.classList.add('close-form');
        folderForm.classList.remove('show-form');
        passForm.classList.add('close-form');
        passForm.classList.remove('show-form');
    });
});

//Open form for adding tags/folders
document.addEventListener('DOMContentLoaded', function () {

    createFolderBtn2.addEventListener('click', function (event) {
        event.preventDefault();
        folderForm.classList.toggle('show-form');
        folderForm.classList.remove('close-form');
        tagForm.classList.add('close-form');
        tagForm.classList.remove('show-form');
        passForm.classList.add('close-form');
        passForm.classList.remove('show-form');
    });
});

//Opening the form for entering the vault
document.addEventListener('DOMContentLoaded', function () {

    createPassBtn.addEventListener('click', function (event) {
        event.preventDefault();
        passForm.classList.toggle('show-form');
        passForm.classList.remove('close-form');
        folderForm.classList.add('close-form');
        folderForm.classList.remove('show-form');
        tagForm.classList.add('close-form');
        tagForm.classList.remove('show-form');
    });
});

//Close by pressing Escape
document.addEventListener('keydown', function (e) {
    if (e.keyCode == 27) {
        passForm.classList.add('close-form');
        passForm.classList.remove('show-form');
    }
});