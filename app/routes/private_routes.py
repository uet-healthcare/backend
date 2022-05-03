from fastapi import APIRouter, Request
import psycopg2
from app.db import get_db_connection
from app.models.request import IDRequest, Post, UpdatePostRequest, UsernameCheckRequest


privateRoutes = APIRouter(
    prefix="/private",
    tags=["private"],
)


@privateRoutes.post("/posts")
def create_post(request: Request, post: Post):
    user_id = request.state.x_user_id
    conn = None
    post_id = None
    try:
        conn = get_db_connection()

        cur = conn.cursor()
        cur.execute("""insert into posts (user_id, title, content) values(%s, %s, %s) returning post_id;""",
                    (user_id, post.title, post.content))
        post_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return {"error": "database error"}
    finally:
        if conn is not None:
            conn.close()

    return {"post_id": post_id}


@privateRoutes.put("/posts")
def create_post(request: Request, post: UpdatePostRequest):
    user_id = request.state.x_user_id

    conn = None
    post_id = None
    try:
        conn = get_db_connection()

        cur = conn.cursor()
        cur.execute("""update posts set (title, content) = (%s, %s) where user_id=%s and post_id=%s returning post_id;""",
                    (post.title, post.content, user_id, post.id))
        post_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return {"error": "database error"}
    finally:
        if conn is not None:
            conn.close()

    return {"post_id": post_id}


@privateRoutes.delete("/posts")
def create_post(request: Request, post: IDRequest):
    user_id = request.state.x_user_id

    conn = None
    rows_deleted = 0
    try:
        conn = get_db_connection()

        cur = conn.cursor()
        cur.execute("""delete from posts where user_id=%s and post_id=%s;""",
                    (user_id, post.id))
        rows_deleted = cur.rowcount
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return {"error": "database error"}
    finally:
        if conn is not None:
            conn.close()

    return {"rows_deleted": rows_deleted}


@privateRoutes.get("/extra_user_infos")
def get_extra_user_infos(request: Request):
    user_id = request.state.x_user_id
    conn = None
    try:
        conn = get_db_connection()

        cur = conn.cursor()
        cur.execute(
            """select first_name, last_name, username from public.profiles where user_id = %s""", [user_id])
        row = cur.fetchone()
        cur.close()
        if row is not None:
            return {
                "first_name": row[0],
                "last_name": row[1],
                "username": row[2],
            }
        else:
            return None

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return {"error": "database error"}
    finally:
        if conn is not None:
            conn.close()


@privateRoutes.post("/settings/username_check")
def check_username(params: UsernameCheckRequest):
    reserved_keywords = ["bai-viet", "dang-nhap", "dang-ky", "dang-xuat", "doi-mat-khau",
                         "cap-nhat-thong-tin", "viet-bai", "quan-ly", "cai-dat", "thiet-lap",
                         "chinh-sach", "dieu-khoan", "tai-khoan", "ca-nhan",
                         "admin", "settings", "config", "posts", "post", "login", "logout",
                         "signin", "signup", "signout", "sign-in", "sign-up", "sign-out", "dashboard"]

    if params.username in reserved_keywords:
        return {"is_available": False}

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
        return {"error": "database error"}
    finally:
        if conn is not None:
            conn.close()

    return {"is_available": is_available}
