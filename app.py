import os
import json
from urllib.parse import urlencode

from aiohttp import web
from aiohttp import ClientSession

OAUTH2_CLIENT_ID = os.environ['OAUTH2_CLIENT_ID']
OAUTH2_CLIENT_SECRET = os.environ['OAUTH2_CLIENT_SECRET']
OAUTH2_REDIRECT_URI = 'http://localhost:5000/callback'

API_BASE_URL = os.environ.get('API_BASE_URL', 'https://discordapp.com/api')
AUTHORIZATION_BASE_URL = API_BASE_URL + '/oauth2/authorize'
TOKEN_URL = API_BASE_URL + '/oauth2/token'

session = ClientSession()


class OAuthPage(web.Application):
    def __init__(self):
        super().__init__()

        self.add_routes([
            web.get('/', self.index),
            web.get('/callback', self.callback),
            web.get('/me', self.me),
        ])

    async def fetch_token(self, code):
        data = {
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": OAUTH2_REDIRECT_URI,
            "client_id": OAUTH2_CLIENT_ID,
            "client_secret": OAUTH2_CLIENT_SECRET
        }

        response = await session.post(
            f"{TOKEN_URL}?{urlencode(data)}",
        )

        js = await response.json()
        return js["token"]

    async def index(self, request: web.Request):
        data = {
            "scope": "identify email connections guilds guilds.join",
            "client_id": OAUTH2_CLIENT_ID,
            "response_type": "code"
        }
        raise web.HTTPFound(f"{AUTHORIZATION_BASE_URL}?{urlencode(data)}")

    async def callback(self, request: web.Request):
        code = request.query["code"]
        token = await self.fetch_token(code)
        raise web.HTTPFound(f'/me?token={token}')
    
    async def me(self, request: web.Request):
        token = request.query["token"]
        headers = {"Authorization": f"Bearer {token}"}
        user = session.get(f"{API_BASE_URL}/users/@me", headers=headers)
        guilds = session.get(f"{API_BASE_URL}/users/@me/guilds", headers=headers)
        connections = session.get(f"{API_BASE_URL}/users/@me/connections", headers=headers)

        response = web.Response(body=json.dumps(dict(user=user, guilds=guilds, connections=connections)))
        response.headers['content-type'] = 'text/json'
        return response
