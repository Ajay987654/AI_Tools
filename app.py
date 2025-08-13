from flask import Flask, render_template, request, send_from_directory
import google.generativeai as genai
from PIL import Image
import os
import uuid

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "static/uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Navbar data defined in Python
NAVBAR_ITEMS = [
    {"name": "Home", "url": "/"},
    {"name": "Tools", "url": "/tools"},
    {"name": "Pricing", "url": "/pricing"},
    {"name": "About", "url": "/about"},
    {"name": "Contact Us", "url": "/contact"}
]

# Your Gemini API Key
GEMINI_API_KEY = "AIzaSyDRV8RMiZ0tp-zVu3QqrIdLCnBoVQXDJZo"
genai.configure(api_key=GEMINI_API_KEY)

# Model 
model = genai.GenerativeModel("gemini-1.5-flash")  # Adjust model name if needed

def detect_mood(caption_text):
    """
    Detect mood based on keywords or emojis in the generated caption.
    """
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

def get_gemini_song(image_path, mood):
    image = Image.open(image_path)

    prompt = (
        f"Based on the detected mood '{mood}' from the person's facial expression in this image, "
        "recommend one suitable song title and artist that matches the emotion. "
        "For example, if happy, suggest an upbeat song; if sad, a melancholic one. "
        "Return the response in the format: 'Song Title by Artist | URL' where URL is a direct link to the song on a platform like YouTube or Spotify."
    )

    response = model.generate_content([prompt, image])
    song_data = response.text.strip().split(" | ")
    if len(song_data) == 2:
        return {"title": song_data[0], "url": song_data[1]}
    else:
        return {"title": song_data[0], "url": "#"}  # Fallback URL if none provided

@app.route("/", methods=["GET", "POST"])
def index():
    caption = None
    mood = None
    song = None
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
            song = get_gemini_song(file_path, mood)

    return render_template("index.html", navbar_items=NAVBAR_ITEMS, caption=caption, mood=mood, song=song, image_filename=image_filename)

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
