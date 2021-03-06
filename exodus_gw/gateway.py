from fastapi import Depends
from fastapi.exception_handlers import http_exception_handler
from starlette.exceptions import HTTPException as StarletteHTTPException

from .app import app
from .publish import create_publish_id
from .auth import call_context, CallContext
from .s3.util import xml_response


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request, exc):
    # Override HTTPException to produce XML error responses for the
    # given endpoints.

    path = request.scope.get("path")

    if path.startswith("/upload"):
        return xml_response(
            "Error", Code=exc.status_code, Message=exc.detail, Endpoint=path
        )

    return await http_exception_handler(request, exc)


@app.get("/healthcheck", tags=["service"])
def healthcheck():
    """Returns a successful response if the service is running."""
    return {"detail": "exodus-gw is running"}


@app.post("/{env}/publish")
def publish(env: str):
    """WIP: Returns a new, empty publish id"""
    if env not in ["dev", "qa", "stage", "prod"]:
        return {"error": "environment {0} not found".format(env)}
    create_publish_id()
    return {"detail": "Created Publish Id"}


@app.get(
    "/whoami",
    response_model=CallContext,
    tags=["service"],
    responses={
        200: {
            "description": "returns caller's auth context",
            "content": {
                "application/json": {
                    "example": {
                        "client": {
                            "roles": ["someRole", "anotherRole"],
                            "authenticated": True,
                            "serviceAccountId": "clientappname",
                        },
                        "user": {
                            "roles": ["viewer"],
                            "authenticated": True,
                            "internalUsername": "someuser",
                        },
                    }
                }
            },
        }
    },
)
def whoami(context: CallContext = Depends(call_context)):
    """Return basic information on the caller's authentication & authorization context.

    This endpoint may be used to determine whether the caller is authenticated to
    the exodus-gw service, and if so, which set of role(s) are held by the caller.

    It is a read-only endpoint intended for diagnosing authentication issues.
    """
    return context
