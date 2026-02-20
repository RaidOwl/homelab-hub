from app import create_app

app = create_app()

if __name__ == "__main__":
    enable_debug = os.getenv("FLASK_DEBUG", "false").lower() in ["true", "t", "yes", "y", "1"]
    port = int(os.getenv("FLASK_PORT", 5001))
    app.run(debug=enable_debug, port=port)
