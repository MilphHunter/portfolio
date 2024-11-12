// Fill the modal window for editing with information
document.querySelectorAll('.edit').forEach(button => {
    button.addEventListener('click', function (event) {
        const row = event.target.closest('.download-history');
        const fileId = row.getAttribute('data-file-id');
        const title = row.children[1].innerText;
        const tags = row.children[5].innerText;
        const status = row.children[6].innerText.trim().toLowerCase() === 'true' ? 'option1' : 'option2';

        document.querySelector('#editFileModal #titleInput').value = title;
        document.querySelector('#editFileModal #tagsInput').value = tags;
        document.querySelector(`#editFileModal input[id="${status}"]`).checked = true;

        document.querySelector('#editFileModal .btn-success').setAttribute('data-file-id', fileId);
    });
});
// Handler of the “Save” button
document.querySelector('#editFileModal .btn-success').addEventListener('click', function() {
    const fileId = this.getAttribute('data-file-id');
    const title = document.querySelector('#editFileModal #titleInput').value;
    const tags = document.querySelector('#editFileModal #tagsInput').value;
    const status = document.querySelector('#editFileModal input[name="inlineRadioOptions"]:checked').value;

    const tagsArray = tags.split(',').map(tag => tag.trim()).filter(tag => tag.length > 0);

    fetch('/admin/files/update-file', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            id: fileId,
            title: title,
            tags: tagsArray,
            status: status === 'option1',
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            $('#editFileModal').modal('hide');
            location.reload();
        } else {
            alert('Error updating file');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error updating file');
    });
});
