import json
from textwrap import dedent

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse


class OpenAPI(BaseHTTPMiddleware):
    async def dispatch(
            self,
            request: Request,
            call_next: RequestResponseEndpoint
    ) -> Response:
        response: StreamingResponse = await call_next(request)
        if request.url.path.endswith('/openapi.json'):
            body = [section async for section in response.body_iterator]
            original_content = b"".join(body)
            original_text = original_content.decode("U8")

            obj = json.loads(response.render(original_text))

            docker_host_url = str(request.url.replace(hostname='host.docker.internal'))
            obj['servers'] = [
                {"url": f'{request.url.scheme}://{request.url.netloc}'},
                {"url": f'/'},
            ]

            obj['info']['description'] += dedent(
                f"""
                
            for normal url [{str(request.url)}]({str(request.url)})
            
            for docker host [{docker_host_url}]({docker_host_url})
            """
            )
            new_body = json.dumps(obj)
            new_content = new_body.encode('U8')
            headers = dict(response.headers)
            headers.pop('content-length', None)

            new_response = Response(
                content=new_content,
                status_code=response.status_code,
                headers=headers,
                media_type=response.media_type
            )

            return new_response
        else:
            return response
