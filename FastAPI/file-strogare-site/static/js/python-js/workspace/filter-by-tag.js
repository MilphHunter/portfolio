// Sorting by tags next to the title
document.addEventListener('DOMContentLoaded', function () {
    // Обработчик клика на тег
    document.querySelectorAll('.item-tag').forEach(tag => {
        tag.addEventListener('click', function () {
            const selectedTag = this.textContent.slice(1).trim();

            window.location.href = `/workspace/tag?tags=${encodeURIComponent(selectedTag)}`;
        });
    });
});
// Sorting by tags:
document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.nav-link').forEach(tag => {
        tag.addEventListener('click', async function (event) {
            event.preventDefault();

            this.classList.toggle('link-primary');

            const selectedTags = Array.from(document.querySelectorAll('.nav-link.link-primary'))
                                      .map(tag => tag.childNodes[0].textContent.trim());

            if (selectedTags.length > 0) {
                const cleanTags = selectedTags.map(tag => tag.replace(/\s+/g, ' '));

                const queryString = cleanTags.map(tag => encodeURIComponent(tag)).join(',');

                window.location.href = `/workspace/tag?tags=${queryString}`;
            } else {
                alert('Pick at least one tag!');
            }
        });
    });
});


