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
        # Timeout muy corto para no perder tiempo
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

def get_image_base64(url):
    try:
        # EL TRUCO: Si la imagen tarda más de 1 segundo, la abortamos para que GitHub no rompa el widget.
        response = requests.get(url, timeout=1.5) 
        return base64.b64encode(response.content).decode('utf-8').replace("\n", "")
    except:
        # Si falla o tarda, devolvemos vacío y el código principal pondrá un cuadro gris.
        return ""

@app.route('/api/spotify')
def index():
    # Headers para desactivar caché agresivamente
    headers = {
        'Content-Type': 'image/svg+xml; charset=utf-8',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
    }
    xml_header = '<?xml version="1.0" encoding="UTF-8"?>'

    try:
        data = get_now_playing()
        
        bg_color = request.args.get('background_color', '18181b')
        text_color = "ffffff"
        bar_color = request.args.get('bar_color', '1db954')

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
        track_name = html.escape(item['name'])
        artist_name = html.escape(item['artists'][0]['name'])
        
        # Intentamos obtener imagen
        images = item['album']['images']
        cover_b64 = ""
        if len(images) > 0:
            cover_url = images[-1]['url'] 
            cover_b64 = get_image_base64(cover_url)
        
        # Usamos xlink:href que es más compatible con GitHub antiguo
        if cover_b64:
            image_tag = f'<image x="10" y="10" width="80" height="80" xlink:href="data:image/jpeg;base64,{cover_b64}" rx="5"/>'
        else:
            # Fallback: Cuadro gris si la imagen falló o tardó mucho
            image_tag = '<rect x="10" y="10" width="80" height="80" fill="#2a2a2a" rx="5"/><text x="50" y="50" font-size="20" text-anchor="middle" fill="#555">🎵</text>'
            
        progress_ms = data['progress_ms']
        duration_ms = item['duration_ms']
        progress_pct = min((progress_ms / duration_ms) * 100, 100)
        progress_width = 220 * (progress_pct / 100)

        svg = f"""<svg width="350" height="100" viewBox="0 0 350 100" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
            <rect x="0" y="0" width="350" height="100" rx="10" fill="#{bg_color}" stroke="rgba(255,255,255,0.1)" stroke-width="1"/>
            {image_tag}
            <text x="105" y="35" fill="#{text_color}" font-family="sans-serif" font-size="16" font-weight="bold">{track_name}</text>
            <text x="105" y="55" fill="#b3b3b3" font-family="sans-serif" font-size="14">{artist_name}</text>
            <rect x="105" y="75" width="220" height="4" rx="2" fill="#404040"/>
            <rect x="105" y="75" width="{progress_width}" height="4" rx="2" fill="#{bar_color}"/>
        </svg>"""

        return Response(xml_header + svg, headers=headers)

    except Exception as e:
        # Si explota, devuelve SVG de error en vez de romper la imagen
        err_msg = html.escape(str(e))
        return Response(f'<svg width="350" height="50" xmlns="http://www.w3.org/2000/svg"><text x="10" y="30" fill="red">Err: {err_msg}</text></svg>', headers=headers)
