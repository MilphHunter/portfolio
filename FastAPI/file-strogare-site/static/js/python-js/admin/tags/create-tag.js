// Tag Create
document.getElementById("tagCreateForm").addEventListener('submit', async function (event) {
    event.preventDefault();
    const formData = new FormData(this);
    try {
        const response = await fetch("/admin/tags/create-tag", {
            method: "POST",
            body: formData,
        });
        const errorMsgElement = document.querySelector(".error-msg");
        if (response.ok) {
            errorMsgElement.style.display = "none";
            window.location.href = "/admin/tags";
        } else {
            const errorData = await response.json();
            if (Array.isArray(errorData.detail)) {
                //To long title
                const titleError = errorData.detail.find(
                    (error) => error.loc && error.loc.includes("title") && (error.msg.includes("at most 30 characters")
                    )
                );
                if (titleError) {
                    errorMsgElement.style.display = "block";
                    errorMsgElement.textContent = "Name must be at most 30 characters!";
                }
            }
        }
    }
    catch
        (error)
        {
            console.error("Error when submitting a form:", error);
        }
    }
)