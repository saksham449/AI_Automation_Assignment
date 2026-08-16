from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    send_from_directory
)

import sqlite3
import os
import uuid
import subprocess
import math
import wave
import struct

import imageio_ffmpeg


app = Flask(__name__)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

APP_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

UPLOAD_DIR = os.path.join(
    APP_DIR,
    "uploads"
)

PROCESSED_DIR = os.path.join(
    APP_DIR,
    "processed"
)

DATABASE = os.path.join(
    BASE_DIR,
    "consultbae.db"
)


# Create required folders
os.makedirs(
    UPLOAD_DIR,
    exist_ok=True
)

os.makedirs(
    PROCESSED_DIR,
    exist_ok=True
)


# ============================================================
# DATABASE
# ============================================================

def init_database():

    connection = sqlite3.connect(
        DATABASE
    )

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audio_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            filename TEXT NOT NULL,
            duration_seconds REAL,
            sample_rate_khz REAL,
            bitrate_kbps REAL,
            loudness_db REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()

    connection.close()


# ============================================================
# AUDIO PROCESSING
# ============================================================

def process_audio(input_file):

    unique_id = str(
        uuid.uuid4()
    )

    wav_file = os.path.join(
        PROCESSED_DIR,
        f"{unique_id}.wav"
    )

    # --------------------------------------------------------
    # Get FFmpeg executable
    # --------------------------------------------------------

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()


    # --------------------------------------------------------
    # Convert uploaded audio to:
    #   Mono
    #   16 kHz
    #   16-bit PCM WAV
    # --------------------------------------------------------

    command = [
        ffmpeg,
        "-y",
        "-i",
        input_file,
        "-ac",
        "1",
        "-ar",
        "16000",
        "-sample_fmt",
        "s16",
        wav_file
    ]

    subprocess.run(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True
    )


    # --------------------------------------------------------
    # Read WAV properties
    # --------------------------------------------------------

    with wave.open(
        wav_file,
        "rb"
    ) as audio:

        sample_width = (
            audio.getsampwidth()
        )

        sample_rate = (
            audio.getframerate()
        )

        frame_count = (
            audio.getnframes()
        )

        duration = (
            frame_count / sample_rate
        )

        raw_audio = (
            audio.readframes(
                frame_count
            )
        )


    # --------------------------------------------------------
    # Calculate RMS loudness
    # --------------------------------------------------------

    loudness_db = -99.0

    if raw_audio:

        # We explicitly created a 16-bit WAV above.
        # Therefore each sample is a signed 16-bit integer.

        sample_count = (
            len(raw_audio) // sample_width
        )

        if sample_count > 0:

            samples = struct.unpack(
                "<" + ("h" * sample_count),
                raw_audio
            )

            square_sum = sum(
                sample * sample
                for sample in samples
            )

            rms = math.sqrt(
                square_sum / sample_count
            )

            if rms > 0:

                loudness_db = (
                    20 *
                    math.log10(
                        rms / 32768.0
                    )
                )


    # --------------------------------------------------------
    # Estimate bitrate
    # --------------------------------------------------------

    file_size = os.path.getsize(
        input_file
    )

    if duration > 0:

        bitrate_kbps = (
            file_size * 8
            / duration
            / 1000
        )

    else:

        bitrate_kbps = 0


    # --------------------------------------------------------
    # Return metadata
    # --------------------------------------------------------

    return {

        "processed_file": wav_file,

        "duration_seconds": round(
            duration,
            2
        ),

        "sample_rate_khz": round(
            sample_rate / 1000,
            2
        ),

        "bitrate_kbps": round(
            bitrate_kbps,
            2
        ),

        "loudness_db": round(
            loudness_db,
            2
        )

    }


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def index():

    connection = sqlite3.connect(
        DATABASE
    )

    connection.row_factory = (
        sqlite3.Row
    )

    submissions = connection.execute(
        """
        SELECT *
        FROM audio_submissions
        ORDER BY created_at DESC
        """
    ).fetchall()

    connection.close()


    return render_template(
        "index.html",
        submissions=submissions
    )


# ============================================================
# UPLOAD AUDIO
# ============================================================

@app.route(
    "/upload",
    methods=["POST"]
)
def upload():

    name = request.form.get(
        "name",
        ""
    ).strip()

    phone = request.form.get(
        "phone",
        ""
    ).strip()

    audio = request.files.get(
        "audio"
    )


    # --------------------------------------------------------
    # Validate input
    # --------------------------------------------------------

    if (
        not name
        or not phone
        or not audio
        or not audio.filename
    ):

        return (
            "Name, phone and audio are required.",
            400
        )


    # --------------------------------------------------------
    # Save original audio
    # --------------------------------------------------------

    extension = os.path.splitext(
        audio.filename
    )[1].lower()

    if not extension:

        extension = ".audio"


    filename = (
        f"{uuid.uuid4()}"
        f"{extension}"
    )

    input_path = os.path.join(
        UPLOAD_DIR,
        filename
    )


    audio.save(
        input_path
    )


    # --------------------------------------------------------
    # Process audio
    # --------------------------------------------------------

    try:

        result = process_audio(
            input_path
        )

    except Exception as error:

        print(
            "Audio processing error:",
            error
        )

        return (
            f"Could not process audio file: {error}",
            400
        )


    # --------------------------------------------------------
    # Save metadata to SQLite
    # --------------------------------------------------------

    connection = sqlite3.connect(
        DATABASE
    )

    connection.execute(
        """
        INSERT INTO audio_submissions (
            name,
            phone,
            filename,
            duration_seconds,
            sample_rate_khz,
            bitrate_kbps,
            loudness_db
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            name,
            phone,
            filename,
            result["duration_seconds"],
            result["sample_rate_khz"],
            result["bitrate_kbps"],
            result["loudness_db"]
        )
    )

    connection.commit()

    connection.close()


    return redirect(
        url_for("index")
    )


# ============================================================
# SERVE AUDIO FILE
# ============================================================

@app.route(
    "/audio/<filename>"
)
def audio(filename):

    return send_from_directory(
        UPLOAD_DIR,
        filename
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health")
def health():

    return {
        "status": "ok",
        "service": "ConsultBae Audio Collection"
    }


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    init_database()

    print()
    print("=" * 50)
    print("ConsultBae Audio Collection App")
    print("=" * 50)

    print()
    print(
        "Database:",
        DATABASE
    )

    print(
        "Uploads:",
        UPLOAD_DIR
    )

    print()
    print(
        "Application:",
        "http://127.0.0.1:8000"
    )

    print()

    app.run(
        host="127.0.0.1",
        port=8000,
        debug=True
    )