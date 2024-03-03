document.addEventListener('DOMContentLoaded', function () {
    const tagButtons = document.querySelectorAll('.nav-button');
    tagButtons.forEach(function (button) {
        button.addEventListener('click', function (event) {
            event.preventDefault();
            const clickedTagId = button.dataset.tag;
            const activeTagIds = Array.from(document.querySelectorAll('.nav-button.active-tag')).map(tag => tag.getAttribute('data-tag'));
            let tagsString = activeTagIds.join(',');
            let url = `/workspace/all-notes/`;
            if (tagsString.length !== 0) {
                if (tagsString.length === 2) {
                    tagsString = tagsString.slice(0, -1);
                }
                url = `/workspace/all-notes/tags/${tagsString}`;
            }
            window.location.href = url;
        });
    });
});
