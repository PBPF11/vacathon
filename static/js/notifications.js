function getCsrfToken() {
    const cookieValue = document.cookie
        .split("; ")
        .find((row) => row.startsWith("csrftoken="));
    return cookieValue ? decodeURIComponent(cookieValue.split("=")[1]) : "";
}

document.addEventListener("DOMContentLoaded", () => {
    const inbox = document.querySelector(".notifications-inbox");
    if (!inbox) {
        return;
    }

    const endpoint = inbox.dataset.endpoint;
    const refreshButton = inbox.querySelector("[data-refresh-notifications]");

    const renderNotifications = (payload) => {
        const listWrapper = inbox.querySelector(".notification-list");
        if (!payload.results.length) {
            inbox.innerHTML = `
                <div class="empty-state">
                    <h3>You're all caught up!</h3>
                    <p>Registrations and system alerts will appear here.</p>
                </div>
            `;
            return;
        }
        if (!listWrapper) {
            return;
        }
        listWrapper.innerHTML = "";
        payload.results.forEach((note) => {
            const li = document.createElement("li");
            li.dataset.notificationId = note.id;
            li.className = note.is_read ? "" : "unread";
            li.innerHTML = `
                <div>
                    <h2>${note.title}</h2>
                    <p>${note.message}</p>
                    <p class="meta">${new Date(note.created_at).toLocaleString()}</p>
                </div>
                <div class="actions">
                    ${note.link_url ? `<a class="link" href="${note.link_url}">Open</a>` : ""}
                    ${
                        note.is_read
                            ? ""
                            : `<button class="link-button" data-mark-read data-endpoint="/notifications/api/${note.id}/read/">Mark as read</button>`
                    }
                </div>
            `;
            listWrapper.appendChild(li);
        });
        attachMarkReadHandlers();
    };

    const fetchNotifications = () => {
        if (!endpoint) {
            return;
        }
        fetch(endpoint, {
            headers: {
                "X-Requested-With": "XMLHttpRequest",
            },
        })
            .then((response) => {
                if (!response.ok) {
                    throw new Error("Failed to load notifications");
                }
                return response.json();
            })
            .then(renderNotifications)
            .catch(() => {
                // keep existing content on failure
            });
    };

    const attachMarkReadHandlers = () => {
        inbox.querySelectorAll("[data-mark-read]").forEach((button) => {
            if (button.dataset.bound === "true") {
                return;
            }
            button.dataset.bound = "true";
            button.addEventListener("click", () => {
                const url = button.dataset.endpoint;
                if (!url) {
                    return;
                }
                fetch(url, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": getCsrfToken(),
                        "X-Requested-With": "XMLHttpRequest",
                    },
                })
                    .then((response) => response.json())
                    .then((data) => {
                        if (!data.success) {
                            return;
                        }
                        const container = button.closest("li");
                        if (container) {
                            container.classList.remove("unread");
                            button.remove();
                        }
                    })
                    .catch(() => {
                        // ignore errors
                    });
            });
        });
    };

    attachMarkReadHandlers();
    if (refreshButton) {
        refreshButton.addEventListener("click", fetchNotifications);
    }
});
