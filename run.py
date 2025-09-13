from app import create_app

app = create_app()

if __name__ == "__main__":
    # Debug mode for development; change host/port if needed
    app.run(debug=True, port=5000)
