class PlainTextResponse:
    def __init__(self, content: str = "", status_code: int = 200):
        self.body = content
        self.status_code = status_code

class StreamingResponse:
    def __init__(self, content, media_type: str = "application/octet-stream"):
        self.content = content
        self.media_type = media_type
