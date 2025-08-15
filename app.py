from flask import Flask, render_template, request, send_from_directory
import google.generativeai as genai
from PIL import Image
import os
import uuid
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "static/uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Navbar items for base.html
NAVBAR_ITEMS = [
    {"name": "Home", "url": "/"},
    {"name": "Tools", "url": "/tools"},
    {"name": "Pricing", "url": "/pricing"},
    {"name": "About", "url": "/about"},
    {"name": "Contact Us", "url": "/contact"}
]

# Gemini API Key
GEMINI_API_KEY = "AIzaSyDRV8RMiZ0tp-zVu3QqrIdLCnBoVQXDJZo"
genai.configure(api_key=GEMINI_API_KEY)

# Spotify API Setup
SPOTIFY_CLIENT_ID = "232ac0a1accf480e948af2c4d2c99e73"
SPOTIFY_CLIENT_SECRET = "c7824833aa684d8e841d88a6929a081c"

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
))

# Model
model = genai.GenerativeModel("gemini-1.5-flash")


# ---------------- Helper Functions ---------------- #
def detect_mood(caption_text):
    caption_lower = caption_text.lower()
    if any(word in caption_lower for word in ["happy", "smile", "joy", "laugh", "cheerful", "😊", "😁", "😂", "😍", "🥰"]):
        return "happy"
    elif any(word in caption_lower for word in ["sad", "blue", "cry", "tear", "downcast", "😢", "😭", "☹️", "😞"]):
        return "sad"
    elif any(word in caption_lower for word in ["angry", "mad", "furious", "rage", "😡", "🤬"]):
        return "angry"
    else:
        return "neutral"


def get_gemini_caption(image_path):
    image = Image.open(image_path)
    prompt = (
        "Analyze the person's facial expression in this image, detect their mood or emotion "
        "(such as happy, sad, surprised, angry, neutral, etc.), and generate a short, fun, creative caption. "
        "Add matching emojis for the detected mood. Give me short caption with two lines only."
    )
    response = model.generate_content([prompt, image])
    return response.text.strip()


def get_spotify_recommendations(mood, language="tamil", limit=8):
    query = f"{mood} {language}"
    results = sp.search(q=query, type="track", limit=limit)
    songs = []
    for track in results['tracks']['items']:
        songs.append({
            "title": track['name'],
            "artist": track['artists'][0]['name'],
            "url": track['external_urls']['spotify'],
            "id": track['id']
        })
    return songs


# ---------------- Routes ---------------- #
@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html", navbar_items=NAVBAR_ITEMS)


@app.route("/ai-caption", methods=["GET", "POST"])
def ai_caption():
    caption = None
    mood = None
    songs = None
    image_filename = None

    if request.method == "POST":
        if "image" in request.files:
            file = request.files["image"]
            if file and file.filename != "":
                image_filename = f"{uuid.uuid4().hex}.jpg"
                file_path = os.path.join(app.config["UPLOAD_FOLDER"], image_filename)
                file.save(file_path)

                caption = get_gemini_caption(file_path)
                mood = detect_mood(caption)

        elif "recommend_song" in request.form:
            image_filename = request.form["image_filename"]
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], image_filename)
            caption = request.form.get("caption", "")
            mood = request.form.get("mood", detect_mood(caption))
            language = request.form.get("language", "tamil")
            songs = get_spotify_recommendations(mood, language, limit=8)

    return render_template(
        "ai_caption.html",
        navbar_items=NAVBAR_ITEMS,
        caption=caption,
        mood=mood,
        songs=songs,
        image_filename=image_filename
    )


@app.route("/tools")
def tools():
    return render_template("tools.html", navbar_items=NAVBAR_ITEMS)


@app.route("/pricing")
def pricing():
    return render_template("pricing.html", navbar_items=NAVBAR_ITEMS)


@app.route("/about")
def about():
    return render_template("about.html", navbar_items=NAVBAR_ITEMS)


@app.route("/contact")
def contact():
    return render_template("contact.html", navbar_items=NAVBAR_ITEMS)


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
