from flask import request, jsonify
import redis
import boto3
from models.book import Book
from services.cache_service import cache
from services.db_service import db
from middleware.replay_prevention import prevent_replay

def register_post_routes(app, user_id):
    @app.route('/books', methods=['POST'])
    @prevent_replay(user_id)
    def add_book():
        try:
            data = request.json
            if not data or 'id' not in data:
                return jsonify({"error": "Invalid request"}), 400
            
            book = Book.from_json(data)

            # Check cache
            try:
                cached_book = cache.get(book.id)
                if cached_book:
                    return jsonify({"error": "Book with this ID already exists"}), 409
            except redis.RedisError as e:
                print(f"Redis error: {str(e)}")

            # Check DynamoDB
            try:
                response = db.get_item(book.id, book.timestamp)
                if 'Item' in response:
                    return jsonify({"error": "Book with this ID already exists"}), 409
            except boto3.exceptions.Boto3Error as e:
                return jsonify({"error": f"DynamoDB error: {str(e)}"}), 500

            # Store in DynamoDB and cache
            try:
                db.put_item(book.to_json())
                cache.set(book.id, book.to_cache())
                return jsonify({"message": "Book added successfully"}), 201
            except (boto3.exceptions.Boto3Error, redis.RedisError) as e:
                return jsonify({"error": f"Storage error: {str(e)}"}), 500

        except Exception as e:
            return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500