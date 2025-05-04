document.getElementById("searchButton").addEventListener("click", function () {
    const query = document.getElementById("userSearch").value;

    if (query.length < 2) {
        document.getElementById("userList").innerHTML = ""; // Clear the list if query is too short
        return;
    }

    fetch(`/search_users?query=${query}`)
        .then(response => response.json())
        .then(data => {
            const userList = document.getElementById("userList");
            userList.innerHTML = ""; // Clear previous results

            data.users.forEach(user => {
                const li = document.createElement("li");
                li.textContent = user.username;
                li.addEventListener("click", function () {
                    // Highlight the selected user
                    document.querySelectorAll("#userList li").forEach(li => li.classList.remove("selected"));
                    this.classList.add("selected");
                });
                userList.appendChild(li);
            });
        })
        .catch(error => console.error("Error fetching users:", error));
});