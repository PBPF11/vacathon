document.addEventListener("DOMContentLoaded", () => {
    const container = document.querySelector(".event-overview");
    if (!container) {
        return;
    }

    const detailEndpoint = container.dataset.detailEndpoint;
    const availabilityEndpoint = container.dataset.availabilityEndpoint;
    const routeContainer = container.querySelector("[data-route-container]");
    const aidContainer = container.querySelector("[data-aid-container]");
    const scheduleContainer = container.querySelector("[data-schedule-container]");
    const capacityRemaining = container.querySelector("[data-capacity-remaining]");
    const capacityRatio = container.querySelector("[data-capacity-ratio]");
    const availabilityLabel = container.querySelector("[data-availability-label]");
    const progressBar = container.querySelector(".progress-bar");
    const progressFill = container.querySelector(".progress-fill");

    const formatDate = (isoString, options = {}) => {
        if (!isoString) {
            return "";
        }
        const date = new Date(isoString);
        return date.toLocaleString(undefined, { ...options });
    };

    const renderSegments = (segments) => {
        if (!routeContainer) {
            return;
        }
        if (!segments.length) {
            routeContainer.innerHTML = "<p>No route segments recorded yet.</p>";
            return;
        }
        routeContainer.innerHTML = segments
            .map(
                (segment) => `
                <article>
                    <div class="segment-order">${segment.order}</div>
                    <div>
                        <h3>${segment.title}</h3>
                        <p class="distance">${segment.distance_km} KM &middot; ${segment.elevation_gain} m elevation</p>
                        <p>${segment.description}</p>
                    </div>
                </article>
            `
            )
            .join("");
    };

    const renderAidStations = (stations) => {
        if (!aidContainer) {
            return;
        }
        if (!stations.length) {
            aidContainer.innerHTML = "<p>No aid stations posted yet.</p>";
            return;
        }
        aidContainer.innerHTML = stations
            .map(
                (station) => `
                <article class="station">
                    <h3>${station.name}</h3>
                    <p class="marker">${station.kilometer_marker} KM</p>
                    <p>${station.supplies}</p>
                    ${station.is_medical ? '<span class="badge accent">Medical</span>' : ""}
                </article>
            `
            )
            .join("");
    };

    const renderSchedule = (items) => {
        if (!scheduleContainer) {
            return;
        }
        if (!items.length) {
            scheduleContainer.innerHTML = "<li>No schedule details available yet.</li>";
            return;
        }
        scheduleContainer.innerHTML = items
            .map(
                (item) => `
                <li>
                    <div class="time">${formatDate(item.start_time, {
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                    })}</div>
                    <div>
                        <h3>${item.title}</h3>
                        ${
                            item.end_time
                                ? `<p class="time-range">${formatDate(item.end_time, { hour: "2-digit", minute: "2-digit" })}</p>`
                                : ""
                        }
                        <p>${item.description || ""}</p>
                    </div>
                </li>
            `
            )
            .join("");
    };

    const fetchDetail = () => {
        if (!detailEndpoint) {
            return;
        }
        fetch(detailEndpoint, { headers: { "X-Requested-With": "XMLHttpRequest" } })
            .then((response) => {
                if (!response.ok) {
                    throw new Error(`Detail request failed with status ${response.status}`);
                }
                return response.json();
            })
            .then((data) => {
                renderSegments(data.route_segments || []);
                renderAidStations(data.aid_stations || []);
                renderSchedule(data.schedules || []);
            })
            .catch(() => {
                if (routeContainer) {
                    routeContainer.innerHTML = "<p>Unable to load detailed route information at the moment.</p>";
                }
            });
    };

    const updateAvailability = () => {
        if (!availabilityEndpoint) {
            return;
        }
        fetch(availabilityEndpoint, { headers: { "X-Requested-With": "XMLHttpRequest" } })
            .then((response) => {
                if (!response.ok) {
                    throw new Error(`Availability request failed with status ${response.status}`);
                }
                return response.json();
            })
            .then((data) => {
                if (capacityRemaining) {
                    capacityRemaining.textContent =
                        data.remaining === null ? "Unlimited slots" : `${data.remaining} slots remaining`;
                }
                if (capacityRatio) {
                    capacityRatio.textContent = `${data.capacity_ratio}% capacity`;
                }
                if (progressBar && progressFill) {
                    progressBar.setAttribute("aria-valuenow", data.capacity_ratio);
                    progressFill.style.width = `${data.capacity_ratio}%`;
                }
                if (availabilityLabel) {
                    availabilityLabel.textContent = data.is_registration_open
                        ? "Registration is open. Secure your bib today!"
                        : "Registration is currently closed.";
                }
            })
            .catch(() => {
                if (availabilityLabel) {
                    availabilityLabel.textContent = "Unable to refresh registration status at the moment.";
                }
            });
    };

    fetchDetail();
    updateAvailability();

    // Refresh availability every 60 seconds to keep data accurate.
    setInterval(updateAvailability, 60000);
});
