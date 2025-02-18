from flask import request, jsonify
import redis
import boto3
from models.book import Book
from services.cache_service import cache
from services.db_service import db

def register_put_routes(app):
    @app.route('/books/<id>/<timestamp>', methods=['PUT'])
    def update_book(id, timestamp):
        try:
            data = request.json
            if not data or not timestamp or 'book' not in data:
                return jsonify({"error": "Invalid request"}), 400

            updated_book = Book(id=id, timestamp=timestamp, book=data['book'])

            # Check if book exists
            try:
                cached_book = cache.get(id)
                if not cached_book:
                    try:
                        response = db.get_item(id, timestamp)
                        if 'Item' not in response:
                            return jsonify({"error": "Book not found"}), 404
                    except boto3.exceptions.Boto3Error as e:
                        return jsonify({"error": f"DynamoDB lookup failed: {str(e)}"}), 500
            except redis.RedisError as e:
                print(f"Redis lookup failed: {str(e)}")
                try:
                    response = db.get_item(id, timestamp)
                    if 'Item' not in response:
                        return jsonify({"error": "Book not found"}), 404
                except boto3.exceptions.Boto3Error as e:
                    return jsonify({"error": f"DynamoDB lookup failed: {str(e)}"}), 500

            # Update cache and DB
            try:
                cache.set(id, updated_book.to_cache(), ex=3600)
            except redis.RedisError as e:
                print(f"Redis cache update failed: {str(e)}")

            try:
                db.update_item(id, timestamp, updated_book.book)
            except boto3.exceptions.Boto3Error as e:
                return jsonify({"error": f"DynamoDB update failed: {str(e)}"}), 500

            return jsonify({
                "message": "Book updated successfully",
                "data": updated_book.to_json()
            }), 200

        except Exception as e:
            return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500