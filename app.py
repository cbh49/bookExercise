from flask import Flask
import uuid
from routes.post_routes import register_post_routes
from routes.get_routes import register_get_routes
from routes.put_routes import register_put_routes
from routes.delete_routes import register_delete_routes

def create_app():
    app = Flask(__name__)
    user_id = str(uuid.uuid4())

    # Register all routes
    register_post_routes(app, user_id)
    register_get_routes(app)
    register_put_routes(app)
    register_delete_routes(app)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)