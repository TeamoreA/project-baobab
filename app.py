from src import app
import os

if __name__ == "__main__":
    app.logger.info(f"Starting server on port {os.environ.get('PORT')}")
    app.run(
        host= os.environ.get('HOST'),
        port= os.environ.get('PORT'),
        debug= os.environ.get('DEBUG')
    )
