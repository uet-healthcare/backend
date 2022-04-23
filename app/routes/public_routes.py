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
def get_posts(offset: Optional[str] = None, limit: Optional[str] = None, id: Optional[str] = None, username: Optional[str] = None):
    conn = None
    posts = []
    try:
        conn = get_db_connection()

        cur = conn.cursor()

        conditions = []
        if id is not None:
            conditions.append("post_id={}".format(id))
        if username is not None:
            conditions.append(
                "users.raw_user_meta_data->>'username'='{}'".format(username))

        condition = " and ".join(conditions)
        if len(condition) > 0:
            condition = "where " + condition

        if id is not None:
            cur.execute(
                """select post_id, title, content, created_time, users.raw_user_meta_data->>'full_name' as full_name, users.raw_user_meta_data->>'username' as username, users.raw_user_meta_data->>'avatar_url' as avatar_url from posts inner join auth.users on posts.user_id = users.id {};""".format(condition))
        else:
            cur.execute(
                """select posts.post_id, posts.title, substring(posts.content, 1, 210) as content, posts.created_time, users.raw_user_meta_data->>'full_name' as full_name, users.raw_user_meta_data->>'username' as username, users.raw_user_meta_data->>'avatar_url' as avatar_url from posts inner join auth.users on posts.user_id = users.id {} {} {};""".format(
                    condition,
                    "offset {}".format(offset) if offset is not None else "",
                    "limit {}".format(limit) if limit is not None else ""))

        rows = cur.fetchall()
        for row in rows:
            posts.append({
                "post_id": row[0],
                "title": row[1],
                "content": row[2],
                "created_time": row[3],
                "author": {
                    "full_name": row[4],
                    "username": row[5],
                    "avatar_url": row[6]
                }
            })

        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()

    return posts


@publicRoutes.get("/users/metadata")
def get_user_metadata(username: str):
    conn = None
    try:
        conn = get_db_connection()

        cur = conn.cursor()
        cur.execute(
            """select raw_user_meta_data from auth.users where raw_user_meta_data->>'username' = %s""", [username])
        row = cur.fetchone()
        cur.close()

        if len(row) > 0:
            return row[0]
        else:
            return None

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return {"error": "database error"}
    finally:
        if conn is not None:
            conn.close()
