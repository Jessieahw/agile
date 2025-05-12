// Use the correct IDs for your search input and results list
document.getElementById("search-user").addEventListener("input", function () {
    const query = this.value;

    if (query.length < 2) {
        document.getElementById("user-results").innerHTML = "";
        return;
    }

    fetch(`/search_users?query=${query}`)
        .then(response => response.json())
        .then(data => {
            const userResults = document.getElementById("user-results");
            userResults.innerHTML = "";

            data.users.forEach(user => {
                const li = document.createElement("li");
                li.textContent = user; // If your backend returns usernames as strings
                li.addEventListener("click", function () {
                    fetch(`/get_comparison?username=${encodeURIComponent(user)}`)
                        .then(response => response.json())
                        .then(data => {
                            if (data.message) {
                                alert(data.message);
                                return;
                            }
                            visualizeComparison(data.currentUser, data.selectedUser);
                        });
                });
                userResults.appendChild(li);
            });
        })
        .catch(error => console.error("Error fetching users:", error));
});

// Visualization function for comparison
function visualizeComparison(currentUser, selectedUser) {
    const ctx = document.getElementById('comparisonChart').getContext('2d');
    if (window.comparisonChart instanceof Chart) {
        window.comparisonChart.destroy();
    }
    window.comparisonChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Average Shots', 'Average Goals', 'Average Fouls', 'Average Cards', 'Shot Accuracy'],
            datasets: [
                {
                    label: 'You',
                    data: [
                        currentUser.avg_shots,
                        currentUser.avg_goals,
                        currentUser.avg_fouls,
                        currentUser.avg_cards,
                        currentUser.shot_accuracy,
                    ],
                    backgroundColor: 'rgba(75, 192, 192, 0.5)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1,
                },
                {
                    label: `Selected User (${selectedUser.username})`,
                    data: [
                        selectedUser.avg_shots,
                        selectedUser.avg_goals,
                        selectedUser.avg_fouls,
                        selectedUser.avg_cards,
                        selectedUser.shot_accuracy,
                    ],
                    backgroundColor: 'rgba(255, 99, 132, 0.5)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 1,
                },
            ],
        },
        options: {
            responsive: true,
            scales: {
                y: { beginAtZero: true }
            },
        },
    });
}