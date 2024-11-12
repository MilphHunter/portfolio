// Set the file ID to the “Delete” button in the modal window
document.querySelectorAll('.delete').forEach(button => {
    button.addEventListener('click', function (event) {
        const row = event.target.closest('.download-history');
        const fileId = row.getAttribute('data-file-id');

        const deleteButton = document.querySelector('#confirmDeleteButton');
        deleteButton.setAttribute('data-file-id', fileId);
    });
});

// Handler of pressing the “Delete” button
document.querySelector('#confirmDeleteButton').addEventListener('click', function () {
    const fileId = this.getAttribute('data-file-id');

    fetch(`/admin/files/delete-file/${fileId}`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            $('#deleteFileModal').modal('hide');
            location.reload();
        } else {
            alert('Error deleting file');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error deleting file');
    });
});
