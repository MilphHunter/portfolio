document.getElementById("logout-link").addEventListener("click", function (event) {
    event.preventDefault();

    fetch("/auth/logout", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
    })
        .then(response => response.json())
        .then(data => {
            if (data.message === "The user has successfully logged out.") {
                window.location.href = "/auth/sign-in";
            } else {
                console.error("Exit error:", data);
            }
        })
        .catch(error => {
            console.error("Query error:", error);
        });
});