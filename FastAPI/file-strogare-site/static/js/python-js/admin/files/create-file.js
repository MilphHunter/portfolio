// Function for tag definition by file extension
function getTagByFileExtension(filename) {
    const imgExtensions = ['.jpeg', '.jpg', '.jpe', '.jfif', '.ico', '.png', '.gif', '.svg', '.tiff', '.tif', '.webp', '.eps'];
    const videoExtensions = ['.mov', '.mpeg4', '.mp4', '.avi', '.wmv', '.mpegps', '.flv', '.3gpp', '.webm'];
    const audioExtensions = ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.m4r', '.aiff', '.wma', '.amr', '.midi'];

    const extension = filename.slice(filename.lastIndexOf('.')).toLowerCase();

    if (imgExtensions.includes(extension)) {
        return "Image,";
    } else if (videoExtensions.includes(extension)) {
        return "Video,";
    } else if (audioExtensions.includes(extension)) {
        return "Audio,";
    } else {
        return "Other,";
    }
}

// Handler for displaying the file name and tag definition
document.getElementById("fileInput").addEventListener("change", function () {
    const fileInput = this;
    const fileName = fileInput.files[0]?.name || "";

    document.getElementById("fileTitle").value = fileName;

    const fileTag = getTagByFileExtension(fileName);
    document.getElementById("fileTags").value = fileTag;
});

// Submit form handler
document.getElementById("fileCreateForm").addEventListener('submit', async function (event) {
    event.preventDefault();
    const formData = new FormData(this);
    try {
        const response = await fetch("/admin/files/create-file", {
            method: "POST",
            body: formData,
        });
        const errorMsgElement = document.querySelector(".error-msg");
        if (response.ok) {
            errorMsgElement.style.display = "none";
            location.reload();
        } else {
            const errorData = await response.json();
            errorMsgElement.style.display = "block";
            errorMsgElement.textContent = errorData.detail || "An error occurred";
        }
    } catch (error) {
        console.error("Error when submitting form:", error);
    }
});
