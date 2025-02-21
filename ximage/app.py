import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash
from PIL import Image
import tweepy

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key
UPLOAD_FOLDER = os.path.join('static', 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

from dotenv import load_dotenv
import os

load_dotenv()  # Loads the .env file

TWITTER_API_KEY = os.environ.get('TWITTER_API_KEY')
TWITTER_API_SECRET = os.environ.get('TWITTER_API_SECRET')
TWITTER_ACCESS_TOKEN = os.environ.get('TWITTER_ACCESS_TOKEN')
TWITTER_ACCESS_SECRET = os.environ.get('TWITTER_ACCESS_SECRET')

if not TWITTER_API_KEY:
    raise Exception("TWITTER_API_KEY not set!")

# Initialize Tweepy (the Twitter API client)
auth = tweepy.OAuth1UserHandler(
    TWITTER_API_KEY, TWITTER_API_SECRET,
    TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET
)
twitter_api = tweepy.API(auth)

# --- Predefined image sizes ---
SIZES = [
    (300, 250),
    (728, 90),
    (160, 600),
    (300, 600)
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['image']
    if file.filename == '':
        flash('No file selected')
        return redirect(request.url)
    
    if file:
        # Save the original image with a unique name
        file_ext = os.path.splitext(file.filename)[1]
        original_filename = f"{uuid.uuid4()}{file_ext}"
        original_filepath = os.path.join(UPLOAD_FOLDER, original_filename)
        file.save(original_filepath)
        
        # Resize the image to each of the specified dimensions
        resized_paths = []
        try:
            original_image = Image.open(original_filepath)
        except Exception as e:
            flash(f"Error opening image: {str(e)}")
            return redirect(url_for('index'))
        
        for size in SIZES:
            # Resize image using high-quality downsampling filter
            resized_image = original_image.resize(size, Image.Resampling.LANCZOS)
            resized_filename = f"{uuid.uuid4()}_{size[0]}x{size[1]}{file_ext}"
            resized_filepath = os.path.join(UPLOAD_FOLDER, resized_filename)
            try:
                resized_image.save(resized_filepath)
                resized_paths.append(resized_filepath)
            except Exception as e:
                flash(f"Error saving resized image: {str(e)}")
        
        # Publish each resized image to the user's X account
        for img_path in resized_paths:
            try:
                # Upload media to Twitter
                media = twitter_api.media_upload(img_path)
                # Post a tweet with the uploaded image (adjust the status text as needed)
                twitter_api.update_status(status="Here is your resized image!", media_ids=[media.media_id])
            except Exception as e:
                flash(f"Error posting to Twitter: {str(e)}")
                continue

        flash('Image uploaded, processed, and posted successfully!')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
