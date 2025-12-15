from flask import Flask, Response

app = Flask(__name__)

@app.route('/api/spotify')
def index():
    svg = """<?xml version="1.0" encoding="UTF-8"?>
    <svg width="350" height="100" viewBox="0 0 350 100" xmlns="http://www.w3.org/2000/svg">
        <rect width="350" height="100" fill="#00ff00"/>
        <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-size="20" fill="black">PRUEBA DE CONEXIÓN</text>
    </svg>
    """
    headers = {'Content-Type': 'image/svg+xml', 'Cache-Control': 'no-cache'}
    return Response(svg, headers=headers)
