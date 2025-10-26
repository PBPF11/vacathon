function getCsrfToken() {
    const cookieValue = document.cookie
        .split("; ")
        .find((row) => row.startsWith("csrftoken="));
    return cookieValue ? decodeURIComponent(cookieValue.split("=")[1]) : "";
}

document.addEventListener("DOMContentLoaded", () => {
    const registrationLayout = document.querySelector(".registration-layout");
    if (registrationLayout) {
        const availabilityUrl = registrationLayout.dataset.availabilityUrl;
        const remainingSlotsEl = registrationLayout.querySelector("[data-remaining-slots]");

        const refreshAvailability = () => {
            if (!availabilityUrl || !remainingSlotsEl) {
                return;
            }
            fetch(availabilityUrl, { headers: { "X-Requested-With": "XMLHttpRequest" } })
                .then((response) => response.json())
                .then((data) => {
                    if (typeof data.remaining === "number") {
                        remainingSlotsEl.textContent = data.remaining;
                    }
                })
                .catch(() => {
                    // keep existing value if request fails
                });
        };

        refreshAvailability();
        setInterval(refreshAvailability, 45000);
    }

    const registrationListSection = document.querySelector(".registration-listing");
    if (registrationListSection) {
        const endpoint = registrationListSection.dataset.endpoint;
        const list = registrationListSection.querySelector(".registration-list");

        if (endpoint && list) {
            fetch(endpoint, { headers: { "X-Requested-With": "XMLHttpRequest" } })
                .then((response) => response.json())
                .then((data) => {
                    if (!Array.isArray(data.results)) {
                        return;
                    }
                    if (!data.results.length) {
                        registrationListSection.innerHTML = `
                            <div class="empty-state">
                                <h3>No registrations yet</h3>
                                <p>Browse <a href="/events/">events</a> to discover your next run.</p>
                            </div>
                        `;
                        return;
                    }
                    list.innerHTML = "";
                    data.results.forEach((item) => {
                        const li = document.createElement("li");
                        li.innerHTML = `
                            <div>
                                <h2>${item.event}</h2>
                                <p>Status: ${item.status_display}</p>
                                <p>Distance: ${item.category || "-"}</p>
                            </div>
                            <div class="status">
                                <span class="badge ${item.status}">${item.status_display}</span>
                                <a class="btn outline" href="${item.url}">View details</a>
                            </div>
                        `;
                        list.appendChild(li);
                    });
                })
                .catch(() => {
                    // leave server rendered content
                });
        }
    }
});
