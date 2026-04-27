import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
FILE_URL = f'{BASE_DIR}/backend/posts.json'


def get_posts():
    with open(FILE_URL, "r", encoding="utf-8") as f:
        list_of_posts = json.load(f)
    return list_of_posts


def get_post_by_id(post_id):
    contents = get_posts()
    target_post = [p for p in contents if p.get('id') == post_id]
    if len(target_post) == 1:
        return target_post[0]
    return None


def save_new_post(post):
    contents = get_posts()
    contents.append(post)
    json_str = json.dumps(contents, indent=2)
    with open(FILE_URL, "w") as f:
        f.write(json_str)

    return post


def save_posts(posts):
    json_str = json.dumps(posts, indent=2)
    with open(FILE_URL, "w") as f:
        f.write(json_str)

    return posts


def update_post(post_id, update_content):
    contents = get_posts()
    post_to_update = next((p for p in contents if p["id"] == post_id), None)
    if post_to_update:
        post_to_update.update(update_content)
        save_posts(contents)
    return post_to_update


def delete_post(post_id):
    contents = get_posts()
    updated_content = [p for p in contents if p["id"] != post_id]
    save_posts(updated_content)
    return post_id
