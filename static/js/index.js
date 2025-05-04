// Function to calculate Euclidean distance between two sets of stats
function calculateDistance(userStats, playerStats) {
    let sum = 0;
    for (const stat in userStats) {
        if (userStats.hasOwnProperty(stat) && playerStats.hasOwnProperty(stat)) {
            const diff = parseFloat(userStats[stat]) - parseFloat(playerStats[stat]);
            sum += diff * diff;
        }
    }
    return Math.sqrt(sum);
}

// Function to parse CSV text into an array of objects
function parseCSV(csvText) {
    const lines = csvText.split('\n');
    const headers = lines[0].split(',').map(header => header.trim());
    
    return lines.slice(1).map(line => {
        if (!line.trim()) return null; // Skip empty lines
        const values = line.split(',').map(value => value.trim());
        const player = {};
        headers.forEach((header, index) => {
            player[header] = values[index];
        });
        return player;
    }).filter(player => player !== null); // Remove null entries
}

// Store the players data globally after loading
let playersData = null;

// Function to load the CSV file from the server
async function loadCSV() {
    try {
        const response = await fetch('stats.csv');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const csvText = await response.text();
        playersData = parseCSV(csvText);
        return playersData;
    } catch (error) {
        console.error('Error loading CSV:', error);
        throw error;
    }
}

// Function to find the most similar player
function findMostSimilarPlayer(userStats) {
    if (!playersData) {
        throw new Error('Player data not loaded');
    }

    let mostSimilarPlayer = null;
    let minDistance = Infinity;

    // Compare against each player in the dataset
    for (const player of playersData) {
        const distance = calculateDistance(userStats, player);
        if (distance < minDistance) {
            minDistance = distance;
            mostSimilarPlayer = player;
        }
    }

    return mostSimilarPlayer;
}

// Function to display the similar player's stats
function displaySimilarPlayer(player) {
    const container = document.getElementById('similarPlayerContainer');
    const playerInfo = document.getElementById('playerInfo');
    const statsBody = document.getElementById('similarPlayerStatsBody');

    // Update player info
    playerInfo.innerHTML = `
        <h3>${player.DisplayName}</h3>
        <p><strong>Team:</strong> ${player.Team}</p>
        <p><strong>Year:</strong> ${player.Year}</p>
        <p><strong>Round:</strong> ${player.Round}</p>
    `;

    // Update stats table
    const stats = ['Kicks', 'Handballs', 'Marks', 'Goals', 'Behinds', 'Tackles', 'HitOuts', 'Clearances'];
    statsBody.innerHTML = stats.map(stat => `
        <tr>
            <td>${player[stat]}</td>
        </tr>
    `).join('');

    // Show the container
    container.style.display = 'block';
}

// Function to handle form submission
async function submitStats() {
    try {
        // If data isn't loaded yet, load it
        if (!playersData) {
            await loadCSV();
        }

        const inputs = document.querySelectorAll('input[type="number"]');
        const stats = {};
        inputs.forEach(input => {
            stats[input.name] = input.value || "0";
        });

        const similarPlayer = findMostSimilarPlayer(stats);
        if (similarPlayer) {
            displaySimilarPlayer(similarPlayer);
        } else {
            alert('No similar player found. Please try different stats.');
        }
    } catch (error) {
        console.error('Error finding similar player:', error);
        alert('Error finding similar player. Please try again.');
    }
}

// Add event listeners when the document is loaded
document.addEventListener('DOMContentLoaded', () => {
    const compareButton = document.querySelector('.center-button');
    compareButton.addEventListener('click', submitStats);
}); 