function getCsrfToken() {
    const cookieValue = document.cookie
        .split("; ")
        .find((row) => row.startsWith("csrftoken="));
    return cookieValue ? decodeURIComponent(cookieValue.split("=")[1]) : "";
}

document.addEventListener("DOMContentLoaded", () => {
    const filterForm = document.getElementById("thread-filter-form");
    const threadListSection = document.querySelector(".thread-list");
    const resetFiltersButton = document.getElementById("reset-thread-filters");

    const postForm = document.getElementById("post-form");
    const postList = document.getElementById("post-list");
    const cancelReplyButton = document.getElementById("cancel-reply");

    const renderThreads = (threads) => {
        if (!threadListSection) {
            return;
        }
        if (!threads.length) {
            threadListSection.innerHTML = `
                <div class="empty-state">
                    <h3>No threads yet</h3>
                    <p>Be the first to kick off a discussion for this event.</p>
                </div>
            `;
            return;
        }
        const markup = `
            <ul class="threads">
                ${threads
                    .map(
                        (thread) => `
                        <li class="thread-card">
                            <div class="thread-meta">
                                ${thread.is_pinned ? '<span class="badge accent">Pinned</span>' : ""}
                                <h2><a href="${thread.url}">${thread.title}</a></h2>
                                <p class="subtitle">
                                    In <span>${thread.event}</span> &middot; Started by ${thread.author}
                                </p>
                            </div>
                            <dl class="stats">
                                <div>
                                    <dt>Replies</dt>
                                    <dd>${thread.post_count}</dd>
                                </div>
                                <div>
                                    <dt>Views</dt>
                                    <dd>${thread.view_count}</dd>
                                </div>
                                <div>
                                    <dt>Last activity</dt>
                                    <dd>${new Date(thread.last_activity_at).toLocaleString()}</dd>
                                </div>
                            </dl>
                        </li>
                    `
                    )
                    .join("")}
            </ul>
        `;
        threadListSection.innerHTML = markup;
    };

    const fetchThreads = () => {
        if (!filterForm || !threadListSection) {
            return;
        }
        const endpoint = threadListSection.dataset.endpoint;
        if (!endpoint) {
            return;
        }
        const formData = new FormData(filterForm);
        const params = new URLSearchParams(formData);
        fetch(`${endpoint}?${params.toString()}`, {
            headers: { "X-Requested-With": "XMLHttpRequest" },
        })
            .then((response) => {
                if (!response.ok) {
                    throw new Error("Failed to fetch threads");
                }
                return response.json();
            })
            .then((data) => {
                renderThreads(data.results || []);
            })
            .catch(() => {
                threadListSection.innerHTML = `
                    <div class="empty-state">
                        <h3>Unable to load threads</h3>
                        <p>Please refresh the page or try again later.</p>
                    </div>
                `;
            });
    };

    if (filterForm && threadListSection) {
        filterForm.addEventListener("change", fetchThreads);
        filterForm.addEventListener("submit", (event) => {
            event.preventDefault();
            fetchThreads();
        });

        const keywordInput = filterForm.querySelector("input[name='q']");
        if (keywordInput) {
            let timeout;
            keywordInput.addEventListener("input", () => {
                clearTimeout(timeout);
                timeout = setTimeout(fetchThreads, 400);
            });
        }

        if (resetFiltersButton) {
            resetFiltersButton.addEventListener("click", () => {
                filterForm.reset();
                fetchThreads();
            });
        }
    }

    const setReplyTarget = (postId, authorName) => {
        if (!postForm) {
            return;
        }
        const parentInput = document.getElementById("id_parent");
        const contentField = postForm.querySelector("textarea[name='content']");
        if (parentInput) {
            parentInput.value = postId;
        }
        if (contentField) {
            contentField.focus();
        }
        if (cancelReplyButton) {
            cancelReplyButton.classList.remove("hidden");
            cancelReplyButton.dataset.replyingTo = authorName || "";
        }
    };

    const clearReplyTarget = () => {
        if (!postForm) {
            return;
        }
        const parentInput = document.getElementById("id_parent");
        if (parentInput) {
            parentInput.value = "";
        }
        if (cancelReplyButton) {
            cancelReplyButton.classList.add("hidden");
            delete cancelReplyButton.dataset.replyingTo;
        }
    };

    if (cancelReplyButton) {
        cancelReplyButton.addEventListener("click", () => {
            clearReplyTarget();
        });
    }

    const attachPostHandlers = (root) => {
        if (!root) {
            return;
        }

        root.querySelectorAll(".like-button").forEach((button) => {
            button.addEventListener("click", () => {
                const endpoint = button.dataset.likeEndpoint;
                if (!endpoint) {
                    return;
                }
                fetch(endpoint, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": getCsrfToken(),
                        "X-Requested-With": "XMLHttpRequest",
                    },
                })
                    .then((response) => {
                        if (!response.ok) {
                            throw new Error("Failed to toggle like");
                        }
                        return response.json();
                    })
                    .then((data) => {
                        if (!data.success) {
                            return;
                        }
                        button.querySelector(".like-label").textContent = data.liked ? "Unlike" : "Like";
                        button.querySelector(".like-count").textContent = data.like_count;
                    })
                    .catch(() => {
                        button.disabled = true;
                    });
            });
        });

        root.querySelectorAll(".reply-button").forEach((button) => {
            button.addEventListener("click", () => {
                const postId = button.dataset.postId;
                const postElement = button.closest(".post");
                const authorName = postElement
                    ? postElement.querySelector("strong")?.textContent || ""
                    : "";
                setReplyTarget(postId, authorName);
            });
        });

        root.querySelectorAll(".report-button").forEach((button) => {
            button.addEventListener("click", () => {
                const endpoint = button.dataset.reportEndpoint;
                if (!endpoint) {
                    return;
                }
                const reason = prompt("Let us know why this post should be reviewed:");
                if (!reason) {
                    return;
                }
                const formData = new FormData();
                formData.append("reason", reason);
                fetch(endpoint, {
                    method: "POST",
                    headers: { "X-CSRFToken": getCsrfToken(), "X-Requested-With": "XMLHttpRequest" },
                    body: formData,
                })
                    .then((response) => response.json())
                    .then((data) => {
                        alert(data.message || "Report submitted.");
                    })
                    .catch(() => {
                        alert("Unable to submit report at this time.");
                    });
            });
        });
    };

    if (postList) {
        attachPostHandlers(postList);
    }

    if (postForm && postList) {
        postForm.addEventListener("submit", (event) => {
            event.preventDefault();
            const endpoint = postList.parentElement.dataset.postEndpoint;
            if (!endpoint) {
                return;
            }
            const formData = new FormData(postForm);
            fetch(endpoint, {
                method: "POST",
                headers: { "X-CSRFToken": getCsrfToken(), "X-Requested-With": "XMLHttpRequest" },
                body: formData,
            })
                .then((response) => {
                    if (!response.ok) {
                        return response.json().then((data) => Promise.reject(data));
                    }
                    return response.json();
                })
                .then((data) => {
                    if (!data.success) {
                        return;
                    }
                    const temp = document.createElement("div");
                    temp.innerHTML = data.html;
                    const newPost = temp.firstElementChild;
                    if (newPost) {
                        const parentId = data.parent_id;
                        if (parentId) {
                            const parentPost = postList.querySelector(`[data-post-id="${parentId}"]`);
                            const replies = Array.from(
                                postList.querySelectorAll(`[data-parent-id="${parentId}"]`)
                            );
                            if (replies.length) {
                                replies[replies.length - 1].after(newPost);
                            } else if (parentPost) {
                                parentPost.after(newPost);
                            } else {
                                postList.appendChild(newPost);
                            }
                        } else {
                            postList.appendChild(newPost);
                        }
                        attachPostHandlers(newPost);
                    }
                    postForm.reset();
                    clearReplyTarget();
                })
                .catch((error) => {
                    if (error?.errors?.content) {
                        alert(error.errors.content.join("\n"));
                    } else {
                        alert("Unable to post your reply. Please try again later.");
                    }
                });
        });
    }
});
