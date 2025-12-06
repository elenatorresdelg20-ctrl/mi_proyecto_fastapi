class APIKeyHeader:
    def __init__(self, name: str, auto_error: bool = True):
        self.name = name
        self.auto_error = auto_error

    def __call__(self, request):
        return request.headers.get(self.name)

class OAuth2PasswordBearer:
    def __init__(self, tokenUrl: str):
        self.tokenUrl = tokenUrl

class OAuth2PasswordRequestForm:
    def __init__(self):
        self.username = ""
        self.password = ""
        self.scopes = []
