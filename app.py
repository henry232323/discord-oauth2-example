import os
from urllib.parse import urlencode

import aiohttp
from kyoukai import Kyoukai
from kyoukai.util import as_json
from kyoukai.asphalt import HTTPRequestContext, Response
from werkzeug.utils import redirect

OAUTH2_CLIENT_ID = os.environ['OAUTH2_CLIENT_ID']
OAUTH2_CLIENT_SECRET = os.environ['OAUTH2_CLIENT_SECRET']
OAUTH2_REDIRECT_URI = 'http://localhost:5000/callback'

API_BASE_URL = os.environ.get('API_BASE_URL', 'https://discordapp.com/api')
AUTHORIZATION_BASE_URL = API_BASE_URL + '/oauth2/authorize'
TOKEN_URL = API_BASE_URL + '/oauth2/token'

app = Kyoukai(__name__)
app.debug = True

session = aiohttp.ClientSession()


async def fetch_token(code):
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


@app.route('/', methods=["GET"])
async def index(ctx: HTTPRequestContext):
    data = {
        "scope": "identify email connections guilds guilds.join",
        "client_id": OAUTH2_CLIENT_ID,
        "response_type": "code"
    }
    return redirect(f"{AUTHORIZATION_BASE_URL}?{urlencode(data)}")


@app.route('/callback', methods=["GET"])
async def callback(ctx: HTTPRequestContext):
    code = ctx.request.args["code"]
    token = await fetch_token(code)
    return redirect(f'/me?token={token}')


@app.route('/me', methods=["GET"])
async def me(ctx: HTTPRequestContext):
    token = ctx.request.args["token"]
    headers = {"Authorization": f"Bearer {token}"}
    user = session.get(f"{API_BASE_URL}/users/@me", headers=headers)
    guilds = session.get(f"{API_BASE_URL}/users/@me/guilds", headers=headers)
    connections = session.get(f"{API_BASE_URL}/users/@me/connections", headers=headers)
    return as_json(dict(user=user, guilds=guilds, connections=connections))
