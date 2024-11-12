// The feature is big because instead of refreshing the page after deleting it, I preferred to fill it in manually
document.addEventListener("DOMContentLoaded", function () {
    let userEmailToDelete = null;

    document.querySelectorAll('.delete').forEach(button => {
        button.addEventListener("click", function () {
            userEmailToDelete = this.getAttribute("data-user-email");
        });
    });

    document.querySelector(".btn-success").addEventListener("click", function () {
        if (userEmailToDelete) {
            const lastUserRow = document.querySelector("#usersTable tr:last-child th:nth-child(3)");
            const lastUserEmail = lastUserRow ? lastUserRow.textContent.trim() : null;

            fetch(`/admin/users/ban/${userEmailToDelete}`, {
                method: "DELETE",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({last_user_email: lastUserEmail})
            })
                .then(response => response.json())
                .then(data => {
                    if (data.message === "User deleted") {
                        const userRow = document.getElementById(`user-row-${userEmailToDelete}`);
                        if (userRow) {
                            userRow.remove();
                        }

                        userEmailToDelete = null;

                        const modal = document.getElementById("deleteUserModal");
                        modal.classList.remove('show');
                        modal.style.display = "none";
                        document.body.classList.remove('modal-open');
                        const backdrop = document.querySelector('.modal-backdrop');
                        if (backdrop) {
                            backdrop.remove();
                        }

                        if (data.next_user) {
                            const nextUser = data.next_user;
                            const usersTable = document.getElementById("usersTable");
                            const row = document.createElement("tr");
                            row.id = `user-row-${nextUser.email}`;
                            row.innerHTML = `
                                <th>
                                    <span class="custom-checkbox">
                                        <input type="checkbox" id="${nextUser.email}" name="option[]" value="1">
                                        <label for="checkbox1"></label>
                                    </span>
                                </th>
                                <th>${nextUser.name}</th>
                                <th style="text-transform: lowercase">${nextUser.email}</th>
                                <th style="text-transform: lowercase">${nextUser.latest_activity}</th>
                                <th style="text-transform: lowercase">${nextUser.files_downloaded}</th>
                                <th>
                                    <a href="#deleteUserModal" style="margin-left: 0.8rem;" class="delete"
                                       data-toggle="modal" data-user-email="${nextUser.email}">
                                        <i class="material-icons" data-toggle="tooltip" title="Delete">block</i>
                                    </a>
                                </th>
                            `;
                            usersTable.appendChild(row);
                            const deleteButton = row.querySelector('.delete');
                            deleteButton.addEventListener("click", function () {
                                userEmailToDelete = this.getAttribute("data-user-email");
                            });
                        }
                    } else {
                        console.error("Failed to ban the user.");
                    }
                })
                .catch(error => {
                    console.error("Error deleting user:", error);
                    alert("Error deleting user.");
                });
        }
    });
});
