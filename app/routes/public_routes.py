import json
from fastapi import APIRouter
import psycopg2
from typing import Optional

from app.db import get_db_connection


publicRoutes = APIRouter(
    prefix="/public",
    tags=["public"]
)


@publicRoutes.get("/posts")
def get_posts(offset: Optional[int] = None, limit: Optional[int] = None, id: Optional[int] = None, username: Optional[str] = None):
    conn = None
    posts = []
    try:
        conn = get_db_connection()

        cur = conn.cursor()

        condition_names = []
        condition_values = []
        if id is not None:
            condition_names.append("posts.post_id=%s")
            condition_values.append(id)
        if username is not None:
            condition_names.append(
                "profiles.username=%s")
            condition_values.append(username)
        conditions = (" and " + " and ".join(condition_names)
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
where status='public' {}
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
where status='public' {}
order by posts.updated_at desc
{}""".format(conditions, other_properties)
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


@publicRoutes.get("/users/metadata")
def get_user_metadata(user_id: Optional[str] = None, username: Optional[str] = None):
    conn = None
    condition = None
    condition_value = None
    if user_id is not None:
        condition = "user_id=%s"
        condition_value = user_id
    if username is not None:
        condition = "username=%s"
        condition_value = username

    try:
        conn = get_db_connection()

        cur = conn.cursor()
        cur.execute(
            """select user_id, username, full_name, avatar_url, bio, about
from profiles
where {}""".format(condition), (condition_value,))
        row = cur.fetchone()
        cur.close()

        if len(row) > 0:
            return {
                "success": True,
                "data": {
                    "user_id": row[0],
                    "username": row[1],
                    "full_name": row[2],
                    "avatar_url": row[3],
                    "bio": row[4],
                    "about": row[5],
                }
            }
        else:
            return {
                "success": False,
                "error": "User not found",
            }

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


@publicRoutes.get("/comments")
def get_posts(post_id: Optional[int] = None, parent_comment_id: Optional[int] = None):
    conn = None
    posts = []
    try:
        conn = get_db_connection()

        cur = conn.cursor()

        conditions = []
        conditionsValues = []

        if post_id is not None:
            conditions.append("post_id=%s")
            conditionsValues.append(post_id)
        if parent_comment_id is not None:
            conditions.append("parent_comment_id=%s")
            conditionsValues.append(parent_comment_id)

        sql = """select
    comments.comment_id,
    comments.parent_comment_id,
    comments.post_id,
    comments.content,
    comments.created_at,
    comments.updated_at,
    profiles.full_name,
    profiles.username,
    profiles.avatar_url
from comments inner join profiles on comments.user_id = profiles.user_id
where {}
order by comments.updated_at desc;""".format(" and ".join(conditions))
        cur.execute(sql, tuple(conditionsValues))
        rows = cur.fetchall()
        for row in rows:
            posts.append({
                "comment_id": row[0],
                "parent_comment_id": row[1],
                "post_id": row[2],
                "content": row[3],
                "created_at": row[4],
                "updated_at": row[5],
                "author": {
                    "full_name": row[6],
                    "username": row[7],
                    "avatar_url": row[8]
                }
            })

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
