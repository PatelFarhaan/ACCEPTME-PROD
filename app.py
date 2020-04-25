from project import app, db


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True, use_reloader=True, host='0.0.0.0', threaded=True, port=80)
