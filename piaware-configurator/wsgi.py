from app.main import app, setup_production_logger, socketio

setup_production_logger()

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', debug=True)
