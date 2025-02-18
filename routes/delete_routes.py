from flask import jsonify
import redis
import boto3
from models.book import Book
from services.cache_service import cache
from services.db_service import db

def register_delete_routes(app):
    @app.route('/books/<id>/<timestamp>', methods=["DELETE"])
    def delete_book(id, timestamp):
        try:
            # Check if book exists
            try:
                response = db.get_item(id, timestamp)
                if 'Item' not in response:
                    return jsonify({"error": "Book not found"}), 404
                existing_book = Book.from_json(response['Item'])
            except boto3.exceptions.Boto3Error as e:
                return jsonify({
                    "error": f"Failed to check DynamoDB: {str(e)}"
                }), 500

            # Delete from DB and cache
            try:
                db.delete_item(existing_book.id, existing_book.timestamp)
            except boto3.exceptions.Boto3Error as e:
                return jsonify({
                    "error": f"Failed to delete from DynamoDB: {str(e)}"
                }), 500

            try:
                cache.delete(existing_book.id)
                cache_status = "deleted"
            except redis.RedisError as e:
                print(f"Redis deletion failed: {str(e)}")
                cache_status = "delete_failed"

            return jsonify({
                "message": "Book deleted successfully",
                "cache_status": cache_status
            }), 200

        except Exception as e:
            return jsonify({
                "error": f"An unexpected error occurred: {str(e)}"
            }), 500