document.getElementById("search-user").addEventListener("input", function () {
    const query = this.value;

    if (query.length < 2) {
        document.getElementById("user-results").innerHTML = ""; // Clear the list if query is too short
        return;
    }

    fetch(`/search_users?query=${query}`)
        .then(response => response.json())
        .then(data => {
            const userResults = document.getElementById("user-results");
            userResults.innerHTML = ""; // Clear previous results

            data.users.forEach(user => {
                const li = document.createElement("li");
                li.textContent = user; // Display the username
                li.addEventListener("click", function () {
                    console.log(`Selected user: ${user}`); // Debugging
                    fetchUserComparison(user); // Call the comparison function with the selected username
                });
                userResults.appendChild(li);
            });
        })
        .catch(error => console.error("Error fetching users:", error));
});

function fetchUserComparison(selectedUser) {
    fetch(`/get_comparison?username=${selectedUser}`)
        .then(response => response.json())
        .then(data => {
            if (data.message === "User not found") {
                alert("User not found. Please try another username.");
                return;
            }
            visualizeComparison(data.currentUser, data.selectedUser); // Visualize the comparison
        })
        .catch(error => console.error("Error fetching comparison data:", error));
}

function visualizeComparison(currentUserData, selectedUserData) {
    const ctx = document.getElementById('comparisonChart').getContext('2d');

    // Destroy the previous chart instance if it exists
    if (window.comparisonChart instanceof Chart) {
        window.comparisonChart.destroy();
    }

    // Combine all data points to calculate the maximum value
    const allData = [
        ...Object.values(currentUserData),
        ...Object.values(selectedUserData)
    ];
    const maxValue = Math.max(...allData);

    // Create a new chart
    window.comparisonChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Average Shots', 'Average Goals', 'Average Fouls', 'Average Cards', 'Shot Accuracy'],
            datasets: [
                {
                    label: 'Current User',
                    data: [
                        currentUserData.avg_shots,
                        currentUserData.avg_goals,
                        currentUserData.avg_fouls,
                        currentUserData.avg_cards,
                        currentUserData.shot_accuracy,
                    ],
                    backgroundColor: 'rgba(75, 192, 192, 0.5)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1,
                },
                {
                    label: `Selected User (${selectedUserData.username})`,
                    data: [
                        selectedUserData.avg_shots,
                        selectedUserData.avg_goals,
                        selectedUserData.avg_fouls,
                        selectedUserData.avg_cards,
                        selectedUserData.shot_accuracy,
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
                y: {
                    beginAtZero: true,
                    max: Math.ceil(maxValue + 2), // Add some padding above the max value
                },
            },
        },
    });
}