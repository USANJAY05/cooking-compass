from functools import wraps

def user_exist(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        current_user = kwargs.get("current_user")

        if not current_user or not current_user.get("email"):
            return {"message": "User does not exist"}

        return func(*args, **kwargs)

    return wrapper