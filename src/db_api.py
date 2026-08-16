from flask import Flask, request, jsonify
import sqlite3
import os


app = Flask(__name__)


# ============================================================
# DATABASE PATH
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATABASE_FILE = os.path.join(
    BASE_DIR,
    "consultbae.db"
)


# ============================================================
# DUPLICATE CHECK API
# ============================================================

@app.post("/check-duplicate")
def check_duplicate():

    data = request.get_json()

    email = str(
        data.get("email", "")
    ).strip().lower()

    phone = str(
        data.get("phone", "")
    ).strip()


    connection = sqlite3.connect(
        DATABASE_FILE
    )

    cursor = connection.cursor()


    query = """
        SELECT
            name,
            email,
            phone,
            city,
            source
        FROM master_contacts
        WHERE
            (
                email IS NOT NULL
                AND email != ''
                AND email = ?
            )
            OR
            (
                phone IS NOT NULL
                AND phone != ''
                AND phone = ?
            )
        LIMIT 1
    """


    cursor.execute(
        query,
        (
            email,
            phone
        )
    )


    row = cursor.fetchone()

    connection.close()


    # ========================================================
    # DUPLICATE FOUND
    # ========================================================

    if row:

        return jsonify({

            "duplicate": True,

            "matched_contact": {

                "name": row[0],

                "email": row[1],

                "phone": row[2],

                "city": row[3],

                "source": row[4]

            }

        })


    # ========================================================
    # NO DUPLICATE
    # ========================================================

    return jsonify({

        "duplicate": False,

        "matched_contact": None

    })


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    return jsonify({

        "status": "ok",

        "database": DATABASE_FILE

    })


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 50)
    print("ConsultBae SQLite API")
    print("=" * 50)

    print()
    print(
        "Database:",
        DATABASE_FILE
    )

    print()
    print(
        "API running at:"
    )

    print(
        "http://127.0.0.1:5000"
    )

    print()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )