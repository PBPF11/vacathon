function getCsrfToken() {
    const cookieValue = document.cookie
        .split("; ")
        .find((row) => row.startsWith("csrftoken="));
    return cookieValue ? decodeURIComponent(cookieValue.split("=")[1]) : "";
}

function renderAchievementCard(achievement, options = {}) {
    const { showLink = true, includeDelete = true } = options;
    const card = document.createElement("article");
    card.className = "achievement-card";
    card.dataset.achievementId = achievement.id;

    const parts = [];
    parts.push(`<h3>${achievement.title}</h3>`);
    if (achievement.achieved_on) {
        parts.push(`<p class="meta">${new Date(achievement.achieved_on).toLocaleDateString()}</p>`);
    }
    if (achievement.description) {
        parts.push(`<p>${achievement.description}</p>`);
    }
    const footer = [];
    if (showLink && achievement.link) {
        footer.push(
            `<a class="link" href="${achievement.link}" target="_blank" rel="noopener">View proof</a>`
        );
    }
    if (includeDelete && achievement.delete_url) {
        footer.push(
            `<button class="link-button" data-delete-achievement type="button" data-delete-url="${achievement.delete_url}">Remove</button>`
        );
    }
    parts.push(`<footer>${footer.join("")}</footer>`);
    card.innerHTML = parts.join("");
    return card;
}

function renderAchievementListItem(achievement) {
    const item = document.createElement("li");
    item.dataset.achievementId = achievement.id;
    const achieved = achievement.achieved_on
        ? `<span class="meta">${new Date(achievement.achieved_on).toLocaleDateString()}</span>`
        : "";
    item.innerHTML = `
        <div>
            <h3>${achievement.title}</h3>
            ${achieved}
            <p>${achievement.description || ""}</p>
        </div>
        ${
            achievement.delete_url
                ? `<button class="link-button" data-delete-achievement type="button"
                        data-delete-url="${achievement.delete_url}">
                    Remove
                </button>`
                : ""
        }
    `;
    return item;
}

function attachAchievementDeletionHandlers(root) {
    root.querySelectorAll("[data-delete-achievement]").forEach((button) => {
        if (button.dataset.bound === "true") {
            return;
        }
        button.dataset.bound = "true";
        button.addEventListener("click", () => {
            const url = button.dataset.deleteUrl;
            if (!url) {
                return;
            }
            fetch(url, {
                method: "DELETE",
                headers: {
                    "X-CSRFToken": getCsrfToken(),
                    "X-Requested-With": "XMLHttpRequest",
                },
            })
                .then((response) => {
                    if (!response.ok) {
                        throw new Error("Failed to delete achievement");
                    }
                    return response.json();
                })
                .then((data) => {
                    if (!data.success) {
                        return;
                    }
                    const container = button.closest("[data-achievement-id]");
                    if (container) {
                        container.remove();
                    } else {
                        button.closest("li")?.remove();
                    }
                })
                .catch(() => {
                    alert("Unable to remove achievement right now.");
                });
        });
    });
}

document.addEventListener("DOMContentLoaded", () => {
    const dashboard = document.querySelector(".profile-dashboard");
    if (dashboard) {
        const profileEndpoint = dashboard.dataset.profileEndpoint;
        const achievementEndpoint = dashboard.dataset.achievementEndpoint;
        const grid = dashboard.querySelector("[data-achievement-grid]");
        const statsTotal = dashboard.querySelector("[data-stat-total]");
        const statsCompleted = dashboard.querySelector("[data-stat-completed]");
        const statsUpcoming = dashboard.querySelector("[data-stat-upcoming]");
        const upcomingList = dashboard.querySelector("[data-history-upcoming]");
        const completedList = dashboard.querySelector("[data-history-completed]");

        if (profileEndpoint) {
            fetch(profileEndpoint, { headers: { "X-Requested-With": "XMLHttpRequest" } })
                .then((response) => response.json())
                .then((data) => {
                    if (statsTotal) statsTotal.textContent = data.history.length;
                    if (statsCompleted && Array.isArray(data.history)) {
                        const completedCount = data.history.filter((item) => item.status === "completed").length;
                        statsCompleted.textContent = completedCount;
                    }
                    if (statsUpcoming && Array.isArray(data.history)) {
                        const upcomingCount = data.history.filter((item) =>
                            ["upcoming", "registered"].includes(item.status)
                        ).length;
                        statsUpcoming.textContent = upcomingCount;
                    }

                    if (upcomingList) {
                        upcomingList.innerHTML = "";
                        const upcomingItems = data.history.filter((item) =>
                            ["upcoming", "registered"].includes(item.status)
                        );
                        if (!upcomingItems.length) {
                            upcomingList.innerHTML = "<li>No upcoming events yet.</li>";
                        } else {
                            upcomingItems.slice(0, 5).forEach((item) => {
                                const li = document.createElement("li");
                                li.innerHTML = `
                                    <strong>${item.event}</strong>
                                    <span>${new Date(item.registration_date).toLocaleDateString()}</span>
                                    <span class="badge">${item.status.replace("_", " ")}</span>
                                `;
                                upcomingList.appendChild(li);
                            });
                        }
                    }

                    if (completedList) {
                        completedList.innerHTML = "";
                        const completedItems = data.history.filter((item) => item.status === "completed");
                        if (!completedItems.length) {
                            completedList.innerHTML = "<li>No completed events yet.</li>";
                        } else {
                            completedItems.slice(0, 5).forEach((item) => {
                                const li = document.createElement("li");
                                const finishTime = item.finish_time
                                    ? `${Math.floor(item.finish_time / 3600)}h ${Math.floor(
                                          (item.finish_time % 3600) / 60
                                      )}m`
                                    : "-";
                                li.innerHTML = `
                                    <strong>${item.event}</strong>
                                    <span>${finishTime}</span>
                                    <span class="badge accent">Completed</span>
                                `;
                                completedList.appendChild(li);
                            });
                        }
                    }

                    if (grid && Array.isArray(data.achievements) && achievementEndpoint) {
                        grid.innerHTML = "";
                        if (!data.achievements.length) {
                            grid.innerHTML = "<p>No achievements logged yet. Celebrate your milestones!</p>";
                        } else {
                            data.achievements.forEach((achievement) => {
                                achievement.delete_url = `${achievementEndpoint}${achievement.id}/`;
                                const card = renderAchievementCard(achievement);
                                grid.appendChild(card);
                            });
                            attachAchievementDeletionHandlers(grid);
                        }
                    }
                })
                .catch(() => {
                    // Keep server-rendered content on failure.
                });
        }

        const modal = document.querySelector("[data-achievement-modal]");
        const modalForm = modal?.querySelector("[data-achievement-form]");
        const openButton = dashboard.querySelector("[data-open-achievement-modal]");
        if (modal && modalForm && openButton && grid && achievementEndpoint) {
            openButton.addEventListener("click", () => modal.showModal());
            modal.querySelectorAll("[data-close-modal]").forEach((btn) => {
                btn.addEventListener("click", () => modal.close());
            });

            modalForm.addEventListener("submit", (event) => {
                event.preventDefault();
                const formData = new FormData(modalForm);
                const payload = Object.fromEntries(formData.entries());
                fetch(achievementEndpoint, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": getCsrfToken(),
                        "X-Requested-With": "XMLHttpRequest",
                    },
                    body: JSON.stringify(payload),
                })
                    .then((response) => response.json())
                    .then((data) => {
                        if (!data.success) {
                            throw new Error("Unable to create achievement");
                        }
                        const achievement = data.achievement;
                        achievement.delete_url =
                            achievement.delete_url || `${achievementEndpoint}${achievement.id}/`;
                        const card = renderAchievementCard(achievement);
                        if (grid.querySelector("p")) {
                            grid.innerHTML = "";
                        }
                        grid.appendChild(card);
                        attachAchievementDeletionHandlers(grid);
                        modalForm.reset();
                        modal.close();
                    })
                    .catch(() => {
                        alert("Unable to save your achievement right now.");
                    });
            });
        }

        if (grid) {
            attachAchievementDeletionHandlers(grid);
        }
    }

    const settingsGrid = document.querySelector(".settings-grid");
    if (settingsGrid) {
        const endpoint = settingsGrid.dataset.achievementEndpoint;
        const form = document.getElementById("achievement-settings-form");
        const list = settingsGrid.querySelector("[data-achievement-list]");

        if (endpoint && list) {
            fetch(endpoint, { headers: { "X-Requested-With": "XMLHttpRequest" } })
                .then((response) => response.json())
                .then((data) => {
                    if (!Array.isArray(data.results) || !data.results.length) {
                        return;
                    }
                    list.innerHTML = "";
                    data.results.forEach((achievement) => {
                        achievement.delete_url = achievement.delete_url || `${endpoint}${achievement.id}/`;
                        const item = renderAchievementListItem(achievement);
                        list.appendChild(item);
                    });
                    attachAchievementDeletionHandlers(list);
                })
                .catch(() => {
                    // Keep server-rendered fallback
                });
        }

        if (form && endpoint && list) {
            form.addEventListener("submit", (event) => {
                event.preventDefault();
                const formData = new FormData(form);
                const payload = Object.fromEntries(formData.entries());
                fetch(endpoint, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": getCsrfToken(),
                        "X-Requested-With": "XMLHttpRequest",
                    },
                    body: JSON.stringify(payload),
                })
                    .then((response) => response.json())
                    .then((data) => {
                        if (!data.success) {
                            throw new Error("Unable to create achievement");
                        }
                        const achievement = data.achievement;
                        achievement.delete_url = achievement.delete_url || `${endpoint}${achievement.id}/`;
                        if (list.querySelector("li")?.textContent.includes("No achievements")) {
                            list.innerHTML = "";
                        }
                        list.appendChild(renderAchievementListItem(achievement));
                        attachAchievementDeletionHandlers(list);
                        form.reset();
                    })
                    .catch(() => {
                        alert("Unable to save your achievement at the moment.");
                    });
            });
        }

        if (list) {
            attachAchievementDeletionHandlers(list);
        }
    }
});
