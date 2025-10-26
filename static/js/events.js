/* global URLSearchParams */
function debounce(fn, delay = 300) {
    let timeout;
    return (...args) => {
        clearTimeout(timeout);
        timeout = setTimeout(() => fn(...args), delay);
    };
}

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("event-filter-form");
    const container = document.getElementById("events-container");

    if (!form || !container) {
        return;
    }

    const endpoint = container.dataset.endpoint;
    const detailTemplate = container.dataset.detailUrlTemplate || "#";
    const detailPlaceholder = container.dataset.detailSlugPlaceholder || "__slug__";
    const resetButton = document.getElementById("reset-filters");

    const buildDetailUrl = (slug, fallback) => {
        if (!slug) {
            return fallback || "#";
        }
        if (fallback && fallback !== "#") {
            return fallback;
        }
        return detailTemplate.replace(detailPlaceholder, slug);
    };

    const renderEvents = (payload) => {
        const { results, pagination } = payload;
        let markup = "";

        if (!results.length) {
            markup = `
                <div class="empty-state">
                    <h3>No events match your filters yet</h3>
                    <p>Try adjusting the filters or clear them to see more events.</p>
                </div>
            `;
        } else {
            markup += `<div class="events-grid">`;
            results.forEach((event) => {
                const detailUrl = event.url ? event.url : buildDetailUrl(event.slug, event.url);
                const categories = event.categories
                    .map((category) => `<li>${category.display_name}</li>`)
                    .join("") || "<li>No categories listed</li>";

                markup += `
                    <article class="event-card" data-event-id="${event.id}">
                        <header>
                            <div class="status ${event.status}">${event.status_display}</div>
                            <h3>${event.title}</h3>
                            <p class="location">${event.city}, ${event.country}</p>
                        </header>
                        <dl class="meta">
                            <div>
                                <dt>Start</dt>
                                <dd>${new Date(event.start_date).toLocaleDateString()}</dd>
                            </div>
                            <div>
                                <dt>Register by</dt>
                                <dd>${new Date(event.registration_deadline).toLocaleDateString()}</dd>
                            </div>
                            <div>
                                <dt>Popularity</dt>
                                <dd>${event.popularity_score}</dd>
                            </div>
                        </dl>
                        <ul class="categories">${categories}</ul>
                        <a class="btn primary" href="${detailUrl}">View details</a>
                    </article>
                `;
            });
            markup += `</div>`;
        }

        if (pagination.pages > 1) {
            markup += `
                <nav class="pagination">
                    ${pagination.has_previous ? `<button class="page-link" data-page="${pagination.page - 1}">Previous</button>` : ""}
                    <span class="page-info">Page ${pagination.page} of ${pagination.pages}</span>
                    ${pagination.has_next ? `<button class="page-link" data-page="${pagination.page + 1}">Next</button>` : ""}
                </nav>
            `;
        }

        container.innerHTML = markup;
        attachPaginationHandlers();
    };

    const attachPaginationHandlers = () => {
        container.querySelectorAll(".pagination .page-link").forEach((button) => {
            button.addEventListener("click", () => {
                const targetPage = Number(button.dataset.page || 1);
                fetchEvents(targetPage);
            });
        });
    };

    const fetchEvents = (page = 1) => {
        const formData = new FormData(form);
        if (page > 1) {
            formData.set("page", String(page));
        } else {
            formData.delete("page");
        }
        const params = new URLSearchParams(formData);
        const url = `${endpoint}?${params.toString()}`;

        container.classList.add("loading");
        fetch(url, {
            headers: {
                "X-Requested-With": "XMLHttpRequest",
            },
        })
            .then((response) => {
                if (!response.ok) {
                    throw new Error(`Request failed with status ${response.status}`);
                }
                return response.json();
            })
            .then(renderEvents)
            .catch(() => {
                container.innerHTML = `
                    <div class="empty-state">
                        <h3>Unable to load events</h3>
                        <p>Please refresh the page or try again in a moment.</p>
                    </div>
                `;
            })
            .finally(() => {
                container.classList.remove("loading");
            });
    };

    const debouncedFetch = debounce(() => fetchEvents(1), 300);

    form.querySelectorAll("input, select").forEach((field) => {
        const eventName = field.tagName.toLowerCase() === "select" ? "change" : "input";
        const handler = field.name === "q" ? debouncedFetch : () => fetchEvents(1);
        field.addEventListener(eventName, handler);
    });

    if (resetButton) {
        resetButton.addEventListener("click", () => {
            form.reset();
            fetchEvents(1);
        });
    }

    attachPaginationHandlers();
});
