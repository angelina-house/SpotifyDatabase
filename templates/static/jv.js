// static/jv.js

// Attach click event listeners to each "View Tracks" button and "Save to Database" button
document.addEventListener("DOMContentLoaded", function () {
    // Event listener for "View Tracks" buttons
    document.querySelectorAll('.view-tracks-btn').forEach(button => {
        button.addEventListener('click', function () {
            const playlistId = button.getAttribute('data-id');
            viewPlaylistTracks(playlistId);
        });
    });

    // Event listener for "Save to Database" buttons
    document.querySelectorAll('.save-to-db-btn').forEach(button => {
        button.addEventListener('click', function () {
            const playlistId = button.getAttribute('data-id');
            addPlaylistToDatabase(playlistId);
        });
    });
});

// Function to fetch and display playlist tracks
function viewPlaylistTracks(playlistId) {
    fetch(`/get_playlist_tracks/${playlistId}`)
        .then(response => response.json())
        .then(data => {
            const trackTable = document.getElementById("trackTable");
            trackTable.innerHTML = `
                <tr>
                    <th>Track Name</th>
                    <th>Artist</th>
                    <th>Album</th>
                    <th>URI</th>
                </tr>
            `;
            data.forEach(track => {
                const row = `
                    <tr>
                        <td>${track.track_name}</td>
                        <td>${track.artist}</td>
                        <td>${track.album}</td>
                        <td>${track.uri}</td>
                    </tr>
                `;
                trackTable.innerHTML += row;
            });
            openModal();
        })
        .catch(error => console.error('Error fetching playlist tracks:', error));
}

// Function to add playlist to the database
function addPlaylistToDatabase(playlistId) {
    fetch(`/add_playlist_to_db/${playlistId}`, { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if(data.message){
                alert(data.message); // Show success message
            }
            if(data.error){
                alert(data.error); // Show error message
            }
        })
        .catch(error => console.error('Error adding playlist to database:', error));
}

// Function to open the modal
function openModal() {
    document.getElementById("playlistModal").style.display = "block";
}

// Function to close the modal
function closeModal() {
    document.getElementById("playlistModal").style.display = "none";
}

// Close modal when clicking outside of it
window.onclick = function(event) {
    const modal = document.getElementById("playlistModal");
    if (event.target === modal) {
        closeModal();
    }
}
