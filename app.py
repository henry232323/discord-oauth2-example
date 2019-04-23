import os
import json
import asyncio
from urllib.parse import urlencode

from aiohttp import web
from aiohttp import ClientSession

OAUTH2_CLIENT_ID = os.environ['OAUTH2_CLIENT_ID']
OAUTH2_CLIENT_SECRET = os.environ['OAUTH2_CLIENT_SECRET']
OAUTH2_REDIRECT_URI = 'http://localhost:5000/callback'

API_BASE_URL = os.environ.get('API_BASE_URL', 'https://discordapp.com/api')
AUTHORIZATION_BASE_URL = API_BASE_URL + '/oauth2/authorize'
TOKEN_URL = API_BASE_URL + '/oauth2/token'


class OAuthPage(web.Application):
    def __init__(self):
        super().__init__()

        self.add_routes([
            web.get('/', self.index),
            web.get('/callback', self.callback),
            web.get('/me', self.me),
        ])

        self.session = ClientSession(loop=asyncio.get_event_loop())

    async def host(self):
        """Begin hosting the site"""
        runner = web.AppRunner(self)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 5556)
        await site.start()

    async def fetch_token(self, code):
        """Fetch the user's token using the temporary code"""
        data = {
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": OAUTH2_REDIRECT_URI,
            "client_id": OAUTH2_CLIENT_ID,
            "client_secret": OAUTH2_CLIENT_SECRET
        }

        response = await self.session.post(
            f"{TOKEN_URL}?{urlencode(data)}",
        )

        js = await response.json()
        return js["token"]

    async def index(self, request: web.Request):
        """The index of the site, which just redirects to the authorization page on Discord"""
        data = {
            "scope": "identify email connections guilds guilds.join",
            "client_id": OAUTH2_CLIENT_ID,
            "response_type": "code"
        }
        raise web.HTTPFound(f"{AUTHORIZATION_BASE_URL}?{urlencode(data)}")

    async def callback(self, request: web.Request):
        """After authorizing, we are sent back to the callpack page, which retrieves the user's token"""
        code = request.query["code"]
        token = await self.fetch_token(code)
        raise web.HTTPFound(f'/me?token={token}')

    async def me(self, request: web.Request):
        """We can then see our user's data as a JSON response with the /me endpoint"""
        token = request.query["token"]
        headers = {"Authorization": f"Bearer {token}"}
        user = self.session.get(f"{API_BASE_URL}/users/@me", headers=headers)
        guilds = self.session.get(f"{API_BASE_URL}/users/@me/guilds", headers=headers)
        connections = self.session.get(f"{API_BASE_URL}/users/@me/connections", headers=headers)

        response = web.Response(body=json.dumps(dict(user=user, guilds=guilds, connections=connections)))
        response.headers['content-type'] = 'text/json'
        return response
