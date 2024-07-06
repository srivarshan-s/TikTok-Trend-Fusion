from flask import Flask, render_template, request, jsonify, url_for, session
from flask_bootstrap import Bootstrap
from music_gen.api import gen_api
from summariser.llama_api import llama_api
from tiktok_to_text.api import t4_api
from tiktok_videos.download import download_videos
import json
import os
import secrets

secret_key = secrets.token_hex(16)

app = Flask(__name__)
app.secret_key = secret_key
Bootstrap(app)


@app.route('/')
def home():
    trending_tags = ["Love", "Drama", "Comedy", "New", "fyp", "foryoupage", "viral", "tiktokchallenge", "duet",
                     "tiktoktravel", "fitness", "foodtok", "beauty", "makeup",
                     "fashion", "dance", "health", "wellness", "love",
                     "motivation", "sports", "music", "comedy"]

    return render_template('index.html', trending_tags=trending_tags)


def extract_value_from_json(json_string):
    try:
        data = json.loads(json_string)
        if isinstance(data, list) and len(data) > 0 and "value" in data[0]:
            return data[0]["value"]
        else:
            return None
    except json.JSONDecodeError:
        return None


@app.route('/search', methods=['POST'])
def search():
    search_tags = extract_value_from_json(request.form.get('search_tags'))
    output_dir = os.path.join('static', 'video', search_tags)

    # Download videos for the given tags
    video_files = download_videos(search_tags, output_dir)

    video_urls = [url_for('static', filename=os.path.join(
        'video', search_tags, os.path.basename(video))) for video in video_files]
    print(video_urls)

    # Convert video URLs to absolute paths
    base_dir = os.path.abspath(os.path.dirname(__file__))
    absolute_video_paths = [os.path.join(
        base_dir, url.lstrip('/')) for url in video_files]
    print(absolute_video_paths)

    session['video_urls'] = absolute_video_paths
    return render_template('video.html', video_urls=video_urls)


@ app.route('/generate_audio', methods=['POST'])
def generate_audio():
    video_urls = session.get('video_urls', [])
    print(video_urls)

    text_summary = t4_api(video_urls)

    # Get the idea and song descriptions from the Llama API
    idea_description, song_description = llama_api(text_summary["summary"])
    # idea_description, song_description = llama_api(text_summary["tags"])
    print("Idea Description:", idea_description)
    print("Song Description:", song_description)

    # Generate the audio using the song description
    output_file_path = gen_api(song_description, 'new_audio', 2)
    output_file_path = "static/audio/new_audio.wav"
    print("Output File Path:", output_file_path)

    audio_url = url_for(
        'static', filename=f'audio/{os.path.basename(output_file_path)}')
    return jsonify(audio_url=audio_url, idea_description=idea_description)


if __name__ == '__main__':
    app.run(debug=True)