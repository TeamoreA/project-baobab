"""Flask app entry point"""
import os
from src import app

if __name__ == "__main__":
    app.logger.info("Starting server on port %s", os.environ.get('PORT'))
    app.run(
        host= os.environ.get('HOST'),
        port= os.environ.get('PORT'),
        debug= os.environ.get('DEBUG')
    )
