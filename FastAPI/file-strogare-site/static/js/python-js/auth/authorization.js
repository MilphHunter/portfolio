// User sign-up
document.getElementById("registerForm").addEventListener("submit", async function (event) {
    event.preventDefault();
    const formData = new FormData(this);
    try {
        const response = await fetch("/auth/register", {
            method: "POST",
            body: formData,
        });

        if (response.ok) {
            const errorMsgElement = document.querySelector(".error-msg");
            errorMsgElement.style.display = "none";
            window.location.href = "/auth/sign-in";
        } else {
            const errorData = await response.json();
            const errorMsgElement = document.querySelector(".error-msg");
            //Excited email error
            if (errorData.detail === "email already registered") {
                errorMsgElement.style.display = "block";
                errorMsgElement.textContent = "This email has already been registered!";
            }
            //To short password error
            else if (Array.isArray(errorData.detail)) {
                const passwordError = errorData.detail.find(
                    (error) => error.loc && error.loc.includes("password") && error.msg.includes("at least 8 characters")
                );
                if (passwordError) {
                    errorMsgElement.style.display = "block";
                    errorMsgElement.textContent = "Password must be at least 8 characters!";
                    return;
                }
                //To short/big name error
                const nameError = errorData.detail.find(
                    (error) => error.loc && error.loc.includes("name") && (
                        error.msg.includes("at least 3 characters") || error.msg.includes("at most 16 characters")
                    )
                );
                if (nameError) {
                    errorMsgElement.style.display = "block";
                    if (nameError.msg.includes("at least 3 characters")) {
                        errorMsgElement.textContent = "Name must be at least 3 characters!";
                    } else if (nameError.msg.includes("at most 16 characters")) {
                        errorMsgElement.textContent = "Name must be at most 16 characters!";
                    }
                }
            }
        }
    } catch (error) {
        console.error("Error when submitting a form:", error);
    }
});