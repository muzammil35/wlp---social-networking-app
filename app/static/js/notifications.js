document.addEventListener("DOMContentLoaded", function () {
  const authorId = document.body.getAttribute("data-author-id");
  const checkNotificationsUrl = `/api/v1/authors/${authorId}/check_notifications/`;

  function checkForNewNotifications() {
    fetch(checkNotificationsUrl, {
      method: "GET",
      credentials: "include",
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Network response was not ok");
        }
        return response.json();
      })
      .then((data) => {
        const badge = document.getElementById("notification-badge");
        if (data.has_new) {
          // Update the badge to show the count of new notifications
          badge.textContent = data.unseen_count;
          badge.style.display = "block";
        } else {
          badge.style.display = "none";
        }
      })
      .catch((error) =>
        console.error("Error checking for new notifications:", error)
      );
  }

  // Poll for new notifications every 3 seconds
  setInterval(checkForNewNotifications, 10000);
  checkForNewNotifications();
});
