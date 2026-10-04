from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.errors import APIError


class BodyLimitMiddleware:
    """Bound bytes before JSON parsing, including chunked requests."""

    def __init__(self, app: ASGIApp, upload_limit: int) -> None:
        self.app, self.upload_limit = app, upload_limit

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        limit = (
            self.upload_limit if scope["path"].endswith("/source/zip") else 16 * 1024
        )
        size = 0

        async def bounded_receive() -> Message:
            nonlocal size
            message = await receive()
            size += len(message.get("body", b""))
            if size > limit:
                raise APIError(
                    413, "UPLOAD_TOO_LARGE", "The request exceeds its size limit."
                )
            return message

        async def no_store(message: Message) -> None:
            if message["type"] == "http.response.start" and scope["path"].startswith(
                "/api/v1/"
            ):
                message["headers"] = [
                    (key, value)
                    for key, value in message.get("headers", [])
                    if key.lower() != b"cache-control"
                ] + [(b"cache-control", b"no-store")]
            await send(message)

        await self.app(scope, bounded_receive, no_store)
