from app.main import app, setup_production_logger

setup_production_logger()

if __name__ == "__main__":
    app.run()
