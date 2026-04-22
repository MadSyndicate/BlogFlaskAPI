from flask import Flask, jsonify,request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes
limiter = Limiter(app=app, key_func=get_remote_address)

POSTS = [
    {"id": 1, "title": "First post", "content": "This is the first post."},
    {"id": 2, "title": "Second post", "content": "This is the second post."},
]

ALLOWED_SORT_KEYS = ["title", "content"]


def find_post_by_id(post_id):
    fetched_post = [p for p in POSTS if p.get('id') == post_id]
    return fetched_post[0] if len(fetched_post) == 1 else None  #only if exact 1 match found


def sort_list(post_list, provided_request):
    request_sort_key = provided_request.args.get('sort', None)
    # only sorting for known keys (no error with 'invalid' key here)
    if request_sort_key in ALLOWED_SORT_KEYS:
        request_direction = provided_request.args.get('direction', None)
        # default sort direction of none is provided
        if request_direction is None or request_direction == 'asc':
            post_list = sorted(
                post_list,
                key=lambda p: p[request_sort_key]
            )
        elif request_direction == 'desc':
            post_list = sorted(
                post_list,
                key=lambda p: p[request_sort_key],
                reverse=True
            )
        else:
            return jsonify(
                {"error": f"Invalid sort direction '{request_direction}'"}
            ), 400
    return post_list


def apply_pagination(post_list, provided_request):
    page = int(provided_request.args.get('page', 1))
    limit = int(provided_request.args.get('limit', 10))

    start_index = (page - 1) * limit
    end_index = start_index + limit

    return post_list[start_index:end_index]

@app.route('/api/posts', methods=['POST'])
@limiter.limit("10/minute")
def add_post():
    new_post = request.get_json()
    if "title" not in new_post and "content" not in new_post:
        return jsonify({"error": "'title' and 'content' missing"}), 400
    elif "title" not in new_post:
        return jsonify({"error": "'title' missing"}), 400
    elif "content" not in new_post:
        return jsonify({"error": "'content' missing"}), 400
    else:
        new_post['id'] = max(post['id'] for post in POSTS) + 1 or 1
        POSTS.append(new_post)
        return jsonify(new_post), 201


@app.route('/api/posts', methods=['GET'])
@limiter.limit("10/minute")
def get_posts():
    post_list = POSTS.copy()

    post_list = sort_list(post_list, request)
    post_list = apply_pagination(post_list, request)

    return jsonify(post_list), 200


@app.route('/api/posts/<int:post_id>', methods=['PUT'])
@limiter.limit("10/minute")
def update_post_by_id(post_id):
    existing_post = find_post_by_id(post_id)
    if existing_post:
        new_data = request.get_json()
        for key, value in new_data.items():
            if key in existing_post:    # only update keys existing
                existing_post[key] = value

        return jsonify(existing_post), 200
    return jsonify({"error": f"No post with id '{post_id}' found."}), 404


@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
@limiter.limit("10/minute")
def delete_post_by_id(post_id):
    existing_post = find_post_by_id(post_id)
    if existing_post:
        POSTS.remove(existing_post)
        return jsonify(
            {"message": f"Post with id '{post_id}' has been deleted successfully."}
        ), 200
    return jsonify({"error": f"No post with id '{post_id}' found."}), 404


@app.route('/api/posts/search')
@limiter.limit("10/minute")
def search_posts():
    search_title = request.args.get('title', None)
    search_content = request.args.get('content', None)

    found_posts = []
    # if both query params provided, will search for every match in the titles AND contents
    # without duplicates
    if search_title:
        for post in POSTS:
            if search_title.lower() in post['title'].lower():
                found_posts.append(post)
    if search_content:
        for post in POSTS:
            if search_content.lower() in post['content'].lower():
                if post not in found_posts: # in case it was added already by title query
                    found_posts.append(post)

    found_posts = sort_list(found_posts, request)
    found_posts = apply_pagination(found_posts, request)

    return jsonify(found_posts), 200


@app.errorhandler(404)
def not_found_error(error):
    print(error)
    return jsonify({"error": "Not Found"}), 404


@app.errorhandler(405)
def method_not_allowed_error(error):
    return jsonify({"error": "Method Not Allowed"}), 405


@app.errorhandler(429)
def too_many_requests(error):
    return jsonify({"error": "Too many request within time limit"}), 429


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)
