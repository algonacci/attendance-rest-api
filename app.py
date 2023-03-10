import os
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import mysql.connector
import module as md
import datetime


app = Flask(__name__)
app.config['ALLOWED_EXTENSIONS'] = set(['png', 'jpg', 'jpeg'])
app.config['UPLOAD_FOLDER'] = 'static/uploads/'

db = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="",
    database="db_attendanceai",
)

cursor = db.cursor()


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']


@app.route("/")
def index():
    return jsonify({
        "status_code": 200,
        "message": "Success!"
    })


@app.route("/predict", methods=["POST"])
def predict():
    if request.method == "POST":
        file = request.files["image"]
        user_id = request.form["user_id"]
        time = request.form["time"]
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            predicted_class, confidence = md.predict(image_path)

            cursor.execute(
                """
                INSERT INTO `attendances`
                (`user_id`, `clock_in`, `image_file`, `created_at`, `updated_at`)
                VALUES
                ('{}', '{}', 'http://127.0.0.1:5000/static/uploads/{}', '{}', '{}')
                """.format(user_id, time, filename, time, time)
            )

            db.commit()

            return jsonify({
                "status_code": 200,
                "message": "Success",
                "image_path": "http://localhost:5000/"+image_path,
                "prediction": predicted_class,
                "confidence": confidence,
            })
        else:
            return jsonify({
                "status_code": 400,
                "message": "Image not found! Upload image in JPG format"
            })
    else:
        return jsonify({
            "status_code": 403,
            "message": "Method not allowed!"
        }), 403


@app.route("/clockout", methods=["POST"])
def clock_out():
    file = request.files["image"]
    user_id = request.form["user_id"]
    time = request.form["time"]

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        predicted_class, confidence = md.predict(image_path)

        cursor.execute("""
        UPDATE attendances
        SET clock_out='{}', updated_at='{}'
        WHERE user_id='{}'
        """.format(time, time, user_id))
        db.commit()

        return jsonify({
            "status_code": 200,
            "message": "Success clocking out",
            "time": time,
            "image_path": "http://localhost:5000/"+image_path,
            "prediction": predicted_class,
            "confidence": confidence,
        })


@app.route("/request", methods=["POST"])
def request_attendance():
    user_id = request.form["user_id"]
    request_attendance_date = request.form["request_attendance_date"]
    request_type_id = request.form["request_type_id"]
    # attachment = request.files["attachment"]
    notes = request.form["notes"]

    cursor.execute(
        """
        INSERT INTO `request_attendances`
        (`user_id`, `request_attendance_date`, `request_type_id`, `notes`, `created_at`, `updated_at`)
        VALUES
        ('{}', '{}', '{}', '{}', '{}', '{}')
        """.format(user_id, request_attendance_date, request_type_id, notes, datetime.datetime.now(), datetime.datetime.now())
    )

    db.commit()

    return jsonify({
        "status_code": 200
    })


@app.errorhandler(400)
def bad_request(error):
    return {
        "status_code": 400,
        "message": "Client side error!"
    }, 400


@app.errorhandler(404)
def not_found(error):
    return {
        "status_code": 404,
        "message": "URL not found"
    }, 404


@app.errorhandler(405)
def method_not_allowed(error):
    return {
        "status_code": 405,
        "message": "Request method not allowed!"
    }, 405


@app.errorhandler(500)
def internal_server_error(error):
    return {
        "status_code": 500,
        "message": "Server error"
    }, 500


if __name__ == "__main__":
    app.run(debug=True,
            host="0.0.0.0",
            port=int(os.environ.get("PORT", 8080)))
