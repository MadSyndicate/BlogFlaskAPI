from datetime import datetime, timezone, timedelta
from flask import Flask, jsonify,request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_swagger_ui import get_swaggerui_blueprint

import json_db_operations

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes
limiter = Limiter(app=app, key_func=get_remote_address)

SWAGGER_URL="/api/docs"
API_URL="/static/masterblog.json"

swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': 'Masterblog API'
    }
)
app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)


MANDATORY_POST_KEYS = [("title", str), ("content", str), ("author", str)]
OPTIONAL_POST_KEYS = [("tags", list)]
UPDATABLE_KEYS = MANDATORY_POST_KEYS + OPTIONAL_POST_KEYS
ALLOWED_SORT_KEYS = ["id", "title", "content", "author", "created_at", "updated_at", "tags"]
ALLOWED_SEARCH_KEYS = ["title", "content", "author", "created_at", "updated_at", "tags"]


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


def serialize_post(post):
    return {
        **post,
        "created_at": datetime.fromisoformat(post['created_at']).strftime("%Y-%m-%d"),
        "updated_at": datetime.fromisoformat(post['updated_at']).strftime("%Y-%m-%d")
    }


def filter_date_range(posts, field, date_str):
    start = datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
    end = start + timedelta(days=1)

    return [
        p for p in posts
        if start <= datetime.fromisoformat(p[field]).replace(tzinfo=timezone.utc) < end
    ]


@app.route('/api/posts', methods=['POST'])
@limiter.limit("10/minute")
def add_post():
    new_post = request.get_json()
    bad_req_collect = []

    for key, value_type in MANDATORY_POST_KEYS:
        if key not in new_post:
            bad_req_collect.append(key)
        else:
            if not isinstance(new_post[key], value_type):
                return jsonify({"error": f"property '{key}' must be <{value_type}>"}), 400
    if bad_req_collect:
        return jsonify({"error": "One or more properties are missing", "missing": bad_req_collect}), 400

    db_data = json_db_operations.get_posts()

    if db_data:
        new_post['id'] = max(post['id'] for post in db_data) + 1
    else:
        new_post['id'] = 1

    new_post['created_at'] = datetime.now(timezone.utc).isoformat()
    new_post['updated_at'] = datetime.now(timezone.utc).isoformat()

    json_db_operations.save_new_post(new_post)

    return jsonify(serialize_post(new_post)), 201


@app.route('/api/posts', methods=['GET'])
@limiter.limit("10/minute")
def get_posts():
    post_list = json_db_operations.get_posts()

    post_list = sort_list(post_list, request)
    post_list = apply_pagination(post_list, request)

    return jsonify([serialize_post(p) for p in post_list]), 200


@app.route('/api/posts/<int:post_id>', methods=['PUT'])
@limiter.limit("10/minute")
def update_post_by_id(post_id):
    existing_post = json_db_operations.get_post_by_id(post_id)

    if existing_post:
        new_data = request.get_json()
        validation_dict = dict(UPDATABLE_KEYS)
        for key, value in new_data.items():
            if key in validation_dict:    # only update keys when allowed
                    if isinstance(value, validation_dict[key]): # only if type for key is correct
                        existing_post[key] = value
                        existing_post['updated_at'] = datetime.now(timezone.utc).isoformat()
                    else:
                        return jsonify(
                            {"error": f"Key '{key}' must be of type <{validation_dict[key]}>."
                                      " No changes made."}
                        ), 400

        json_db_operations.update_post(post_id, existing_post)
        return jsonify(serialize_post(existing_post)), 200

    return jsonify({"error": f"No post with id '{post_id}' found."}), 404


@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
@limiter.limit("10/minute")
def delete_post_by_id(post_id):
    existing_post = json_db_operations.get_post_by_id(post_id)
    if existing_post:
        json_db_operations.delete_post(post_id)
        return jsonify(
            {"message": f"Post with id '{post_id}' has been deleted successfully."}
        ), 200
    return jsonify({"error": f"No post with id '{post_id}' found."}), 404


@app.route('/api/posts/search')
@limiter.limit("10/minute")
def search_posts():

    contents = json_db_operations.get_posts()
    found_posts = []
    for key in ALLOWED_SEARCH_KEYS:
        search_param = request.args.get(key, None)
        if search_param:
            if key == 'created_at' or key == 'updated_at':
                matches = filter_date_range(contents, key, search_param)
                for match in matches:
                    found_posts.append(match)
            elif key == "tags":
                tag_terms = [t.strip() for t in search_param.split(',')]
                # if all(...) => AND-Matching, right-now OR-Matching
                matches = [
                    post for post in contents
                    if any(tag in post.get("tags", []) for tag in tag_terms)
                ]
                for match in matches:
                    found_posts.append(match)
            else:
                matches = [
                    post for post in contents if search_param in post[key]
                ]
                for match in matches:
                    found_posts.append(match)

    found_posts = sort_list(found_posts, request)
    found_posts = apply_pagination(found_posts, request)

    return jsonify([serialize_post(p) for p in found_posts]), 200


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
