// User login
document.getElementById("loginForm").addEventListener('submit', async function (event) {
    event.preventDefault();
    const formData = new FormData(this);
    try {
        const response = await fetch("/auth/login", {
            method: "POST",
            body: formData,
        });
        const errorMsgElement = document.querySelector(".error-msg");
        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('access_token', data.access_token);
            window.location.href = "/workspace";
        } else {
            const errorData = await response.json();
            if (errorData.detail === "data incorrect") {
                errorMsgElement.style.display = "block";
                errorMsgElement.textContent = "The data is incorrect!";
            }
        }
    } catch (error) {
        console.error("Error when submitting a form:", error);
    }
})