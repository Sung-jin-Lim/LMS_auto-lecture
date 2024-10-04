document.addEventListener("DOMContentLoaded", function () {
  const addCourseBtn = document.getElementById("add-course-btn");
  const courseLinksContainer = document.getElementById("course-links-container");

  // Function to dynamically add new course link input fields
  addCourseBtn.addEventListener("click", function () {
    const newInput = document.createElement("input");
    newInput.setAttribute("type", "url");
    newInput.setAttribute("name", "course_link");
    newInput.setAttribute("placeholder", "Enter another course link");
    newInput.classList.add("course-link-input");
    courseLinksContainer.appendChild(newInput);
  });

  // Example of how you can display alerts (Success or Error)
  function showAlert(message, type) {
    const alertBox = document.querySelector(".alert");
    alertBox.textContent = message;
    alertBox.classList.add(type, "show");

    // Hide alert after 3 seconds
    setTimeout(function () {
      alertBox.classList.remove("show", type);
    }, 3000);
  }

  // Example: Triggering a success alert after form submission
  const form = document.querySelector("form");
  form.addEventListener("submit", function (e) {
    e.preventDefault();
    showAlert("Course links submitted successfully!", "success");
  });
});
