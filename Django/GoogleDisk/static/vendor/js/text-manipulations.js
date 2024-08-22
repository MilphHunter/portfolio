//Editing size of textarea
const textarea = document.getElementById('id_note_content');
        textarea.addEventListener('input', autoresize);

        function autoresize() {
            const minHeight = 100; // Минимальная высота
            const lineHeight = 10; // Высота одной строки текста

            const currentHeight = textarea.scrollHeight;
            const lines = Math.floor(currentHeight / lineHeight);

            const newHeight = Math.max(lines * lineHeight, minHeight);

            textarea.style.height = newHeight + 'px';
        }

        // Call autoresize when loading a document


        // Resize text in textarea by pressing the button
        function changeFontSize(element, fontSize) {
            const dropdown = element.closest('.dropdown');
            const button = dropdown.querySelector('.btn');
            button.innerHTML = fontSize;

            const activeButton = document.querySelector('.dropdown-item.active');
            if (activeButton) {
                activeButton.classList.remove('active');
            }

            element.classList.add('active');
            textarea.style.fontSize = fontSize + 'rem';
        }