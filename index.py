import os
import base64
import requests
from flask import Flask, Response, request

app = Flask(__name__)

# --- CONFIGURACIÓN ---
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REFRESH_TOKEN = os.getenv("SPOTIFY_REFRESH_TOKEN")

SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_NOW_PLAYING_URL = "https://api.spotify.com/v1/me/player/currently-playing"

def get_access_token():
    try:
        auth_header = base64.b64encode(f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode()).decode()
        headers = {"Authorization": f"Basic {auth_header}"}
        data = {"grant_type": "refresh_token", "refresh_token": SPOTIFY_REFRESH_TOKEN}
        response = requests.post(SPOTIFY_TOKEN_URL, headers=headers, data=data)
        return response.json().get("access_token")
    except:
        return None

def get_now_playing():
    token = get_access_token()
    if not token:
        return None
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(SPOTIFY_NOW_PLAYING_URL, headers=headers)
    if response.status_code == 204 or response.status_code > 400:
        return None
    return response.json()

def get_image_base64(url):
    try:
        return base64.b64encode(requests.get(url).content).decode('utf-8')
    except:
        return ""

@app.route('/api/spotify')
def index():
    try:
        data = get_now_playing()
        
        bg_color = request.args.get('background_color', '18181b')
        text_color = "ffffff"
        bar_color = request.args.get('bar_color', '1db954')
        
        xml_header = '<?xml version="1.0" encoding="UTF-8"?>'
        headers = {
            'Content-Type': 'image/svg+xml; charset=utf-8',
            'Cache-Control': 'no-cache, no-store, must-revalidate'
        }

        if not data or not data.get('item'):
            # PAUSA
            svg = f"""<svg width="350" height="100" viewBox="0 0 350 100" xmlns="http://www.w3.org/2000/svg">
                <rect x="0" y="0" width="350" height="100" rx="10" fill="#{bg_color}" stroke="rgba(255,255,255,0.1)" stroke-width="1"/>
                <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="#{text_color}" font-family="sans-serif" font-size="14">
                    💤 Spotify en pausa
                </text>
            </svg>"""
            return Response(xml_header + svg, headers=headers)

        # REPRODUCIENDO
        item = data['item']
        track_name = item['name'].replace("&", "&").replace("<", "<").replace(">", ">")
        artist_name = item['artists'][0]['name'].replace("&", "&").replace("<", "<").replace(">", ">")
        
        # IMAGEN PEQUEÑA (FIX PARA GITHUB)
        images = item['album']['images']
        if len(images) > 0:
            cover_url = images[-1]['url'] 
            cover_b64 = get_image_base64(cover_url)
        else:
            cover_b64 = ""
            
        progress_ms = data['progress_ms']
        duration_ms = item['duration_ms']
        progress_pct = min((progress_ms / duration_ms) * 100, 100)
        progress_width = 220 * (progress_pct / 100)

        svg = f"""<svg width="350" height="100" viewBox="0 0 350 100" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
            <rect x="0" y="0" width="350" height="100" rx="10" fill="#{bg_color}" stroke="rgba(255,255,255,0.1)" stroke-width="1"/>
            <image x="10" y="10" width="80" height="80" xlink:href="data:image/jpeg;base64,{cover_b64}" rx="5"/>
            <text x="105" y="35" fill="#{text_color}" font-family="sans-serif" font-size="16" font-weight="bold">{track_name}</text>
            <text x="105" y="55" fill="#b3b3b3" font-family="sans-serif" font-size="14">{artist_name}</text>
            <rect x="105" y="75" width="220" height="4" rx="2" fill="#404040"/>
            <rect x="105" y="75" width="{progress_width}" height="4" rx="2" fill="#{bar_color}"/>
        </svg>"""

        return Response(xml_header + svg, headers=headers)

    except Exception as e:
        return Response(str(e), status=500)
