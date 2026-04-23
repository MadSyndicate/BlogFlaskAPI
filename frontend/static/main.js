// Function that runs once the window is fully loaded
window.onload = function() {
    // Attempt to retrieve the API base URL from the local storage
    var savedBaseUrl = localStorage.getItem('apiBaseUrl');
    // If a base URL is found in local storage, load the posts
    if (savedBaseUrl) {
        document.getElementById('api-base-url').value = savedBaseUrl;
        loadPosts();
    }
}

// Function to fetch all the posts from the API and display them on the page
function loadPosts() {
    var baseUrl = document.getElementById('api-base-url').value;
    localStorage.setItem('apiBaseUrl', baseUrl);

    const searchValue = document.getElementById('search-value').value;
    const searchField = document.getElementById('search-field').value;
    const sortKey = document.getElementById('sort-key').value;
    const sortOrder = document.getElementById('sort-order').value;
    const page = document.getElementById('page').value;
    const pageSize = document.getElementById('page-size').value;

    const params = new URLSearchParams();

    let endpoint = '/posts';

    // 🔍 SEARCH (eigener Endpoint)
    if (searchValue) {
        endpoint = '/posts/search';
        params.append(searchField, searchValue);
    }

    // 🔽 SORT
    if (sortKey) {
        params.append('sort', sortKey);
        if (sortOrder === 'desc') {
            params.append('direction', 'desc');
        }
    }

    // 📄 PAGINATION
    if (page) params.append('page', page);
    if (pageSize) params.append('limit', pageSize);

    const url = baseUrl + endpoint + '?' + params.toString();

    console.log("Request URL:", url); // 🔥 super hilfreich zum Debuggen

    fetch(url)
        .then(response => response.json())
        .then(data => {
            const postContainer = document.getElementById('post-container');
            postContainer.innerHTML = '';

            data.forEach(post => {
                const postDiv = document.createElement('div');
                postDiv.className = 'post';
                postDiv.innerHTML = `
                    <h2>${post.title}</h2>
                    <p>Content: ${post.content}</p>
                    <p>Author: ${post.author}</p>
                    <p>Created at: ${post.created_at}</p>
                    <p>Updated at: ${post.updated_at}</p>
                    <button onclick="deletePost(${post.id})">Delete</button>
                `;
                postContainer.appendChild(postDiv);
            });
        })
        .catch(error => console.error('Error:', error));
}

// Function to send a POST request to the API to add a new post
function addPost() {
    // Retrieve the values from the input fields
    var baseUrl = document.getElementById('api-base-url').value;
    var postTitle = document.getElementById('post-title').value;
    var postContent = document.getElementById('post-content').value;
    var postAuthor = document.getElementById('post-author').value;

    // Use the Fetch API to send a POST request to the /posts endpoint
    fetch(baseUrl + '/posts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: postTitle, content: postContent, author: postAuthor })
    })
    .then(response => response.json())  // Parse the JSON data from the response
    .then(post => {
        console.log('Post added:', post);
        loadPosts(); // Reload the posts after adding a new one
    })
    .catch(error => console.error('Error:', error));  // If an error occurs, log it to the console
}

// Function to send a DELETE request to the API to delete a post
function deletePost(postId) {
    var baseUrl = document.getElementById('api-base-url').value;

    // Use the Fetch API to send a DELETE request to the specific post's endpoint
    fetch(baseUrl + '/posts/' + postId, {
        method: 'DELETE'
    })
    .then(response => {
        console.log('Post deleted:', postId);
        loadPosts(); // Reload the posts after deleting one
    })
    .catch(error => console.error('Error:', error));  // If an error occurs, log it to the console
}
