from flask import jsonify
import redis
import boto3
from models.book import Book
from services.cache_service import cache
from services.db_service import db

def register_get_routes(app):
    @app.route('/books/<id>/<timestamp>', methods=['GET'])
    def get_book(id, timestamp):
        try:
            # Try cache first
            try:
                cached_data = cache.get(id)
                if cached_data:
                    print("Cache hit!: returning from Redis")
                    book = Book.from_cache(cached_data)
                    return jsonify(book.to_json()), 200
                print("Cache miss: fetching from DynamoDB")
            except redis.RedisError as e:
                print(f"Redis error: {str(e)}")

            # Fetch from DynamoDB
            try:
                response = db.get_item(id, timestamp)
                item = response.get('Item')
                if item:
                    book = Book.from_json(item)
                    try:
                        cache.set(id, book.to_cache(), ex=3600)
                        print("Successfully reloaded cache")
                    except redis.RedisError as e:
                        print(f"Failed to reload cache: {str(e)}")
                    return jsonify(item), 200
                return jsonify({"error": "Book not found"}), 404
            except boto3.exceptions.Boto3Error as e:
                return jsonify({"error": f"DynamoDB error: {str(e)}"}), 500

        except Exception as e:
            return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500