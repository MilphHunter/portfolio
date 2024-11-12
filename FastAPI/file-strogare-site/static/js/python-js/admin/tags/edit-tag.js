document.addEventListener("DOMContentLoaded", function () {
    let currentTagTitle = null;

    document.querySelectorAll('.edit').forEach(button => {
        button.addEventListener("click", function () {
            const tagName = this.getAttribute("data-tag-name");
            currentTagTitle = tagName;

            // Заполняем поле ввода текущим названием тега
            const inputField = document.querySelector("#editTagModal input.form-control");
            inputField.value = tagName;
        });
    });

    // Обработка сохранения нового имени тега
    document.querySelector("#editTagModal .btn-success").addEventListener("click", function () {
        const newTagName = document.querySelector("#editTagModal input.form-control").value;

        fetch(`/admin/tags/upgrade/${currentTagTitle}`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ title: newTagName })
        })
            .then(response => response.json())
            .then(data => {
                if (data.message === "Tag updated") {
                    window.location.reload();
                } else {
                    console.error("Failed to update tag.");
                }
            })
            .catch(error => {
                console.error("Error updating tag:", error);
                alert("Error updating tag.");
            });
    });
});
