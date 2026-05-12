from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from app.core.db import engine
from app.models.user import User
from fastapi import FastAPI

class AdminAuth(AuthenticationBackend):
    async def login(self, request):
        form = await request.form()
        username, password = form["username"], form["password"]
        if username == "admin" and password == "admin":
            request.session.update({"token": "admin-token"})
            return True
        return False

    async def logout(self, request):
        request.session.clear()
        return True

    async def authenticate(self, request):
        token = request.session.get("token")
        if not token:
            return False
        return True

class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.email, User.full_name, User.is_active, User.created_at]

def setup_admin(app: FastAPI):
    admin = Admin(
        app,
        engine,
        authentication_backend=AdminAuth(secret_key="change-me"),
    )
    admin.add_view(UserAdmin)