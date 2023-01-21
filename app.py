import spotipy #Python library for the spotify API
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, url_for, session, request, redirect, render_template
import json
import time
import pandas as pd


# App config
app = Flask(
__name__, #Keeping name undeclared for future purposes
template_folder='templates', #directs flask on where to grab HTML files
static_folder='static' #directs flask to CSS files
)

app.secret_key = 'DFNGDFNUGNUS' 
app.config['SESSION_COOKIE_NAME'] = 'spotify-login-session' #cookie for tracking users login

@app.route('/')
def home():
 return render_template('index.html')

@app.route('/login') #Where I send the user to begin the auth process
def login():
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    print(auth_url)
    return redirect(auth_url)

@app.route('/authorize') #Where we confirm with spotify everythings fine then send the user off
def authorize():
    sp_oauth = create_spotify_oauth()
    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session["token_info"] = token_info
    return redirect("/getMusic")

@app.route('/logout')
def logout():
    for key in list(session.keys()):
        session.pop(key)
    return redirect('/')

@app.route('/getMusic')
def get_all_music():
    session['token_info'], authorized = get_token()
    session.modified = True
    if not authorized: #makes sure no one can access without being logged in
        return redirect('/')
    sp = spotipy.Spotify(auth=session.get('token_info').get('access_token'))
    results = []
    iter = 0
    while True:
        offset = iter * 50
        iter += 1
        curGroup = sp.current_user_saved_tracks(limit=50, offset=offset)['items']
        for idx, item in enumerate(curGroup):
            track = item['track']
            val = track['name'] + " - " + track['artists'][0]['name']
            results += [val]
        if (len(curGroup) < 50):
            break
    
    df = pd.DataFrame(results, columns=["song names"]) 
    df.to_csv('songs.csv', index=False)
    return "done"


# Checks to see if token is valid and gets a new token if not
def get_token():
    token_valid = False
    token_info = session.get("token_info", {})

    # Checking if the session already has a token stored
    if not (session.get('token_info', False)):
        token_valid = False
        return token_info, token_valid

    # Checking if token has expired
    now = int(time.time())
    is_token_expired = session.get('token_info').get('expires_at') - now < 60

    # Refreshing token if it has expired
    if (is_token_expired):
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.refresh_access_token(session.get('token_info').get('refresh_token'))

    token_valid = True
    return token_info, token_valid


def create_spotify_oauth():
    return SpotifyOAuth(
            client_id="22a19ef0094246f084f2f115e3ca70e5",
            client_secret="84b8bbf6f849474cb47212cc5d7911e6",
            redirect_uri=url_for('authorize', _external=True), #url_for allows me to not have to hardcode the website(If I were to deploy to main at a company for example)
            scope="user-library-read, user-read-recently-played")

app.run(host='0.0.0.0', port=81,debug=True)