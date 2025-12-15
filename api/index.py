import os
import base64
import requests
import html
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
        headers = {"Authorization": f"Basic {auth_header}", "Content-Type": "application/x-www-form-urlencoded"}
        data = {"grant_type": "refresh_token", "refresh_token": SPOTIFY_REFRESH_TOKEN}
        response = requests.post(SPOTIFY_TOKEN_URL, headers=headers, data=data, timeout=2)
        return response.json().get("access_token")
    except:
        return None

def get_now_playing():
    try:
        token = get_access_token()
        if not token:
            return None
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(SPOTIFY_NOW_PLAYING_URL, headers=headers, timeout=2)
        if response.status_code == 204 or response.status_code > 400:
            return None
        return response.json()
    except:
        return None

@app.route('/api/spotify')
def index():
    # Headers optimizados
    headers = {
        'Content-Type': 'image/svg+xml; charset=utf-8',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
    }
    
    # SVG del Logo de Spotify (Dibujado en código, carga instantánea)
    spotify_logo = """
    <g transform="translate(10, 10)">
        <rect width="80" height="80" rx="5" fill="#1db954"/>
        <path d="M58.6 57.5c-.6.9-1.8 1.2-2.7.6-7.5-4.6-16.9-5.6-28-3.1-1 .2-2.1-.4-2.3-1.4-.2-1 .4-2.1 1.4-2.3 12.1-2.8 22.5-1.6 31 3.5.9.6 1.2 1.8.6 2.7zm3.7-8.3c-.8 1.2-2.4 1.6-3.6.8-9-5.5-22.6-7.1-33.2-3.9-1.4.4-2.8-.4-3.2-1.8-.4-1.4.4-2.8 1.8-3.2 12.1-3.6 27.2-1.8 37.4 4.5 1.2.7 1.5 2.3.8 3.6zm.5-8.5c-10.8-6.4-28.6-7-38.9-3.8-1.6.5-3.3-.4-3.8-2-.5-1.6.4-3.3 2-3.8 11.9-3.6 31.3-2.9 43.6 4.5 1.5.9 2 2.8 1.1 4.3-.9 1.5-2.8 2-4.3 1.1z" fill="#ffffff"/>
    </g>
    """

    try:
        bg_color = request.args.get('background_color', '18181b')
        text_color = "ffffff"
        bar_color = request.args.get('bar_color', '1db954')
        
        data = get_now_playing()

        # Si no hay datos (Pausa o Error de conexión rápida), mostramos el estado "Pausa"
        if not data or not data.get('item'):
            xml_content = f"""<svg width="350" height="100" viewBox="0 0 350 100" xmlns="http://www.w3.org/2000/svg">
                <rect x="0" y="0" width="350" height="100" rx="10" fill="#{bg_color}" stroke="rgba(255,255,255,0.1)" stroke-width="1"/>
                <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="#{text_color}" font-family="sans-serif" font-size="14">
                    💤 Spotify en pausa
                </text>
            </svg>"""
            return Response('<?xml version="1.0" encoding="UTF-8"?>' + xml_content, headers=headers)

        # REPRODUCIENDO (Versión Ligera)
        item = data['item']
        track_name = html.escape(item['name'])
        artist_name = html.escape(item['artists'][0]['name'])
        
        progress_ms = data['progress_ms']
        duration_ms = item['duration_ms']
        progress_pct = min((progress_ms / duration_ms) * 100, 100)
        progress_width = 220 * (progress_pct / 100)

        svg_content = f"""<svg width="350" height="100" viewBox="0 0 350 100" xmlns="http://www.w3.org/2000/svg">
            <rect x="0" y="0" width="350" height="100" rx="10" fill="#{bg_color}" stroke="rgba(255,255,255,0.1)" stroke-width="1"/>
            
            {spotify_logo}
            
            <text x="105" y="35" fill="#{text_color}" font-family="sans-serif" font-size="16" font-weight="bold">{track_name}</text>
            <text x="105" y="55" fill="#b3b3b3" font-family="sans-serif" font-size="14">{artist_name}</text>
            
            <rect x="105" y="75" width="220" height="4" rx="2" fill="#404040"/>
            <rect x="105" y="75" width="{progress_width}" height="4" rx="2" fill="#{bar_color}"/>
        </svg>"""

        return Response('<?xml version="1.0" encoding="UTF-8"?>' + svg_content, headers=headers)

    except Exception as e:
        # SVG de Error ligero
        return Response(f'<svg width="350" height="50" xmlns="http://www.w3.org/2000/svg"><text x="10" y="30" fill="red">Error</text></svg>', headers=headers)
