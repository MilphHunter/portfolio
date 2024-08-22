// Include a tag to the record being edited/created
const csrftoken = document.cookie.match(/csrftoken=([\w-]+)/)[1];

function pinFolderFunction(folderId) {
    $.ajax({
        url: '/workspace/all-notes/folders/pin-folder/',
        method: 'POST',
        contentType: 'application/json',
        headers: {'X-CSRFToken': csrftoken},
        data: JSON.stringify({'folder_id': folderId}),
        success: function (response) {
            const tagSpan = $('[data-tag-id="' + folderId + '"] .nav-button.badge');
            const currentCount = parseInt(tagSpan.text());
            tagSpan.text(response['tag_count']);
        },
        error: function (error) {
            console.error(error);
        }
    });
}
