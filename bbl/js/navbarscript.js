// Get all buttons with the class "nav-btn".
const buttons = document.querySelectorAll(".nav-btn");

// Get all articles with the class "page-content".
const articles = document.querySelectorAll(".page-content");

// Add click event listeners to each button to hook the article visibility functionality to them.
buttons.forEach(button => {
  button.addEventListener("click", () => {
    // Find the target article ID from the button's data attribute.
    const target = button.getAttribute("data-target");

    // Hide all articles by removing the "active" class attribute.
    articles.forEach(article => {
      article.classList.remove("active");
    });

    // Show target article
    document.getElementById(target).classList.add("active");
  });
});