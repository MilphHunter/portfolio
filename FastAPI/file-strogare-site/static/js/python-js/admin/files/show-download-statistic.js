// Display the download history for the selected file
document.querySelector('tbody').addEventListener('click', function (event) {
    if (event.target.closest('.edit') || event.target.closest('.delete')) return;

    if (event.target.closest('.download-history')) {
        const row = event.target.closest('.download-history');
        const fileId = row.getAttribute('data-file-id');

        $('.modal').modal('hide');

        $('#showStatistic').modal('show');

        const tableBody = document.querySelector('#downloadHistoryTableBody');
        tableBody.innerHTML = '';

        const downloadHistory = `{{ download_histories|tojson | safe }}`;

        const history = downloadHistory[fileId] || [];
        if (history.length > 0) {
            history.forEach((record, index) => {
                const rowData = document.createElement('tr');
                rowData.innerHTML = `
                    <th scope="row">${index + 1}</th>
                    <td>${record[0]}</td> <!-- File title -->
                    <td>${record[1]}</td> <!-- User name -->
                    <td>${record[2]}</td> <!-- Download time -->
                `;
                tableBody.appendChild(rowData);
            });
        } else {
            const row = document.createElement('tr');
            row.innerHTML = `<td colspan="4" class="text-center">No download history available</td>`;
            tableBody.appendChild(row);
        }
    }
});
