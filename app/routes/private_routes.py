from typing import Optional
from fastapi import APIRouter, Request
import psycopg2
from app.db import get_db_connection
from app.models.request import IDRequest, UpdatePostRequest, UpdateUserMetadataRequest, UsernameCheckRequest, Comment


privateRoutes = APIRouter(
    prefix="/private",
    tags=["private"],
)


@privateRoutes.get("/posts")
def get_posts(request: Request, offset: Optional[int] = None, limit: Optional[int] = None, status: Optional[str] = None, id: Optional[int] = None):
    user_id = request.state.x_user_id

    conn = None
    posts = []
    try:
        conn = get_db_connection()

        cur = conn.cursor()

        condition_names = ["posts.user_id=%s"]
        condition_values = [user_id]
        if id is not None:
            condition_names.append("posts.post_id=%s")
            condition_values.append(id)
        if status is not None:
            condition_names.append("posts.status=%s")
            condition_values.append(status)
        conditions = ("where " + " and ".join(condition_names)
                      ) if len(condition_names) > 0 else ""

        other_property_names = []
        other_property_values = []
        if offset is not None:
            other_property_names.append("offset %s")
            other_property_values.append(offset)
        if limit is not None:
            other_property_names.append("limit %s")
            other_property_values.append(limit)
        other_properties = " ".join(other_property_names)

        sql = None
        params = None
        if id is not None:
            sql = """select
    posts.post_id,
    posts.status,
    posts.title,
    posts.content,
    posts.created_at,
    posts.updated_at,
    profiles.full_name,
    profiles.username,
    profiles.avatar_url
from posts inner join profiles on posts.user_id = profiles.user_id
{}
order by posts.updated_at desc;""".format(conditions)
            params = tuple(condition_values)
        else:
            sql = """select
    posts.post_id,
    posts.status,
    posts.title,
    substring(posts.content, 1, 210) as content,
    posts.created_at,
    posts.updated_at,
    profiles.full_name,
    profiles.username,
    profiles.avatar_url
from posts inner join profiles on posts.user_id = profiles.user_id
{}
{}
order by posts.updated_at desc;""".format(conditions, other_properties)
            params = tuple(condition_values) + tuple(other_property_values)

        cur.execute(sql, params)
        rows = cur.fetchall()
        for row in rows:
            posts.append({
                "post_id": row[0],
                "status": row[1],
                "title": row[2],
                "content": row[3],
                "created_at": row[4],
                "updated_at": row[5],
                "author": {
                    "full_name": row[6],
                    "username": row[7],
                    "avatar_url": row[8]
                }
            })

        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()

    return {
        "success": True,
        "data": posts
    }


@privateRoutes.post("/posts")
def create_draft_post(request: Request):
    user_id = request.state.x_user_id
    conn = None
    post_id = None
    try:
        conn = get_db_connection()

        cur = conn.cursor()
        sql = """insert into posts (user_id, title, content, status) values ('{}', '', '', 'draft') returning post_id;""".format(
            user_id)
        cur.execute(sql, (user_id))
        post_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return {
            "success": False,
            "error": {
                "message": "database error"
            }
        }
    finally:
        if conn is not None:
            conn.close()

    return {
        "success": True,
        "data": {
            "post_id": post_id
        }
    }


@privateRoutes.put("/posts")
def create_post(request: Request, post: UpdatePostRequest):
    user_id = request.state.x_user_id

    conn = None
    rows_count = None
    try:
        conn = get_db_connection()

        cur = conn.cursor()

        sql = """update posts set (title, content, status) = (%s, %s, %s) where user_id=%s and post_id=%s;"""

        cur.execute(sql, (post.title, post.content,
                    post.status, user_id, post.id))
        rows_count = cur.rowcount
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return {
            "success": False,
            "error": {
                "message": "database error"
            }
        }
    finally:
        if conn is not None:
            conn.close()

    if rows_count > 0:
        return {
            "success": True,
            "data": {
                "post_id": post.id
            }
        }
    else:
        return {
            "success": False,
            "error": {
                "message": "cannot update post."
            }
        }


@privateRoutes.delete("/posts")
def create_post(request: Request, post: IDRequest):
    user_id = request.state.x_user_id

    conn = None
    rows_deleted = 0
    try:
        conn = get_db_connection()

        cur = conn.cursor()
        cur.execute("""update posts set status='removed' where user_id=%s and post_id=%s;""",
                    (user_id, post.id))
        rows_deleted = cur.rowcount
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return {
            "success": False,
            "error": {
                "message": "database error"
            }
        }
    finally:
        if conn is not None:
            conn.close()

    return {
        "success": True,
        "data": {
            "rows_deleted": rows_deleted
        }
    }


@privateRoutes.post("/settings/username_check")
def check_username(params: UsernameCheckRequest):
    reserved_keywords = ["x", "me", "bai-viet", "dang-nhap", "dang-ky", "dang-xuat", "doi-mat-khau",
                         "cap-nhat-thong-tin", "viet-bai", "quan-ly", "cai-dat", "thiet-lap",
                         "chinh-sach", "dieu-khoan", "tai-khoan", "ca-nhan",
                         "admin", "settings", "config", "posts", "post", "login", "logout",
                         "signin", "signup", "signout", "sign-in", "sign-up", "sign-out", "dashboard"]

    if params.username in reserved_keywords:
        return {
            "success": True,
            "data": {
                "is_available": False
            }
        }

    try:
        conn = get_db_connection()

        cur = conn.cursor()
        sql = """select username from profiles WHERE username = '{}'""".format(
            params.username)
        cur.execute(sql)
        is_available = cur.rowcount == 0
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return {
            "success": False,
            "error": {
                "message": "database error"
            }
        }
    finally:
        if conn is not None:
            conn.close()

    return {
        "success": True,
        "data": {
            "is_available": is_available
        }
    }


@privateRoutes.put("/users/metadata")
def update_user_metadata(request: Request, metadata: UpdateUserMetadataRequest):
    user_id = request.state.x_user_id

    update_names = []
    update_values = []

    if metadata.username:
        update_names.append("username=%s")
        update_values.append(metadata.username)

    if metadata.full_name:
        update_names.append("full_name=%s")
        update_values.append(metadata.full_name)

    if metadata.avatar_url:
        update_names.append("avatar_url=%s")
        update_values.append(metadata.avatar_url)

    if metadata.bio:
        update_names.append("bio=%s")
        update_values.append(metadata.bio)

    if metadata.about:
        update_names.append("about=%s")
        update_values.append(metadata.about)

    pairs = ",".join(update_names)
    if len(pairs) == 0:
        return {
            "success": False,
            "error": {
                "message": "Nothing to update"
            }
        }

    conn = None
    rows_count = None
    try:
        conn = get_db_connection()

        cur = conn.cursor()
        cur.execute(
            """update profiles set {} where user_id = %s""".format(pairs), tuple(update_values) + (user_id,))
        rows_count = cur.rowcount
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return {
            "success": False,
            "error": {
                "message": "database error"
            }
        }
    finally:
        if conn is not None:
            conn.close()

    if rows_count > 0:
        return {
            "success": True,
            "data": {
                "rows_count": rows_count
            }
        }
    else:
        return {
            "success": False,
            "error": {
                "message": "cannot update user metadata."
            }
        }


@privateRoutes.post("/comments")
def create_comment(request: Request, comment: Comment):
    user_id = request.state.x_user_id
    conn = None
    comment_id = None
    try:
        conn = get_db_connection()

        cur = conn.cursor()
        sql = """insert into comments (post_id, parent_comment_id, user_id, content) values (%s, %s, %s, %s) returning comment_id;"""
        cur.execute(
            sql, (comment.post_id, comment.parent_comment_id, user_id, comment.content))
        comment_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return {
            "success": False,
            "error": {
                "message": "database error"
            }
        }
    finally:
        if conn is not None:
            conn.close()

    return {
        "success": True,
        "data": {
            "comment_id": comment_id
        }
    }
