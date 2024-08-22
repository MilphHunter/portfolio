// Include a tag to the record being edited/created
const csrftoken = document.cookie.match(/csrftoken=([\w-]+)/)[1];
const urlParts = window.location.pathname.split('/');
const noteId = urlParts[urlParts.length - 3];

function callPythonFunction(tagId) {
    $.ajax({
        url: '/workspace/note/add-tag/',
        method: 'POST',
        contentType: 'application/json',
        headers: {'X-CSRFToken': csrftoken},
        data: JSON.stringify({'tag_id': tagId, 'note_id': noteId}),
        success: function (response) {
            const tagSpan = $('[data-tag-id="' + tagId + '"] .nav-button.badge');
            const currentCount = parseInt(tagSpan.text());
            tagSpan.text(response['tag_count']);
        },
        error: function (error) {
            console.error(error);
        }
    });
}
