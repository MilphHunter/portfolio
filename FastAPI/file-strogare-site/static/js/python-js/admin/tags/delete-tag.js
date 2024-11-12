// The feature is big because instead of refreshing the page after deleting it, I preferred to fill it in manually
document.addEventListener("DOMContentLoaded", function () {
    let tagTitleToDelete = null;

    document.querySelectorAll('.delete').forEach(button => {
        button.addEventListener("click", function () {
            tagTitleToDelete = this.getAttribute("data-tag-title");
        });
    });

    document.querySelector("#deleteConfirm").addEventListener("click", function () {
        if (tagTitleToDelete) {
            const lastTagRow = document.querySelector("#tagsTable tr:last-child th:nth-child(2)");
            const lastTagTitle = lastTagRow ? lastTagRow.textContent.trim() : null;

            fetch(`/admin/tags/delete/${tagTitleToDelete}`, {
                method: "DELETE",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ last_tag_title: lastTagTitle })
            })
                .then(response => response.json())
                .then(data => {
                    if (data.message === "Tag deleted") {
                        const userRow = document.getElementById(`tag-row-${tagTitleToDelete}`);
                        if (userRow) {
                            userRow.remove();
                        }

                        tagTitleToDelete = null;

                        const modal = document.getElementById("deleteTagModal");
                        modal.classList.remove('show');
                        modal.style.display = "none";
                        document.body.classList.remove('modal-open');
                        const backdrop = document.querySelector('.modal-backdrop');
                        if (backdrop) {
                            backdrop.remove();
                        }

                        if (data.next_tag) {
                            const nextTag = data.next_tag;
                            const tagsTable = document.getElementById("tagsTable");
                            const row = document.createElement("tr");
                            row.id = `tag-row-${nextTag.title}`;
                            row.innerHTML = `
                                <th>
                                    <span class="custom-checkbox">
                                        <input type="checkbox" id="${nextTag.title}" name="option[]" value="1">
                                        <label for="checkbox1"></label>
                                    </span>
                                </th>
                                <th>${nextTag.title}</th>
                                <th style="text-transform: lowercase">${nextTag.count_files}</th>
                                <th style="text-transform: lowercase">${nextTag.created_at}</th>
                                <th style="text-transform: lowercase">${nextTag.files_downloaded}</th>
                                <th>
                                    <a href="#editTagModal" class="edit" data-toggle="modal"
                                       data-tag-name="${nextTag.title}">
                                        <i class="material-icons" data-toggle="tooltip" title="Edit">&#xE254;</i>
                                    </a>
                                    <a href="#deleteTagModal" class="delete" data-toggle="modal"
                                    data-tag-title="${nextTag.title}">
                                        <i class="material-icons" data-toggle="tooltip" title="Delete">&#xE872;</i>
                                    </a>
                                </th>
                            `;
                            tagsTable.appendChild(row);
                            const deleteButton = row.querySelector('.delete');
                            deleteButton.addEventListener("click", function () {
                                tagTitleToDelete = this.getAttribute("data-tag-title");
                            });
                        }
                    } else {
                        console.error("Failed to delete the tag.");
                    }
                })
                .catch(error => {
                    console.error("Error deleting tag:", error);
                    alert("Error deleting tag.");
                });
        }
    });
});
