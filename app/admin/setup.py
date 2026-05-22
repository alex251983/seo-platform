from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from app.core.db import engine
from app.models.user import User
from fastapi import FastAPI
import os


class AdminAuth(AuthenticationBackend):
    async def login(self, request):
        form = await request.form()
        username = form.get("username", "")
        password = form.get("password", "")
        admin_email = os.getenv("ADMIN_EMAIL", "")
        admin_password = os.getenv("ADMIN_PASSWORD", "")
        if not admin_password:
            return False
        if username == admin_email and password == admin_password:
            request.session.update({"token": "admin-authenticated"})
            return True
        return False

    async def logout(self, request):
        request.session.clear()
        return True

    async def authenticate(self, request):
        return request.session.get("token") == "admin-authenticated"


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.email, User.full_name, User.is_active, User.created_at]
    column_searchable_list = [User.email, User.full_name]
    column_sortable_list = [User.id, User.created_at]
    can_delete = False


def setup_admin(app: FastAPI):
    secret_key = os.getenv("SECRET_KEY", "")
    if not secret_key:
        raise RuntimeError("SECRET_KEY env variable is required for admin panel")
    admin = Admin(app, engine, authentication_backend=AdminAuth(secret_key=secret_key))
    admin.add_view(UserAdmin)
