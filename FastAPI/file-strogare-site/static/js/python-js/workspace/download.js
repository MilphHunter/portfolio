// Attempting to upload a file before verifying that the user has an authorization token
document.querySelectorAll('.download-main-btn').forEach(button => {
    button.addEventListener('click', async function () {
        const fileId = this.getAttribute('data-file-id');
        const token = localStorage.getItem('access_token');

        if (!token) {
            alert('You need to log in first.');
            return;
        }

        const response = await fetch(`/files/download/${fileId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
            },
        });

        if (response.ok) {
            const blob = await response.blob();

            const contentDisposition = response.headers.get('Content-Disposition');
            let fileName = fileId;

            if (contentDisposition) {
                const match = contentDisposition.match(/filename\*?=['"]?utf-8['"]?''(.+)/i);
                if (match && match[1]) {
                    fileName = decodeURIComponent(match[1]);
                }
            }

            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = fileName;
            link.click();
            URL.revokeObjectURL(link.href);
        } else {
            alert('Error downloading file: ' + response.statusText);
        }
    });
});
