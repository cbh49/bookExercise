<<<<<<< HEAD
import boto3
import redis
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

#Redis Cache
cache = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
table = dynamodb.Table('bookTest')

# POST
@app.route('/books', methods=['POST'])
def add_book():
    """
    Add a new book to the database and cache.
    ---
    tags:
      - books
    parameters:
      - in: body
        name: book
        required: true
        schema:
          type: object
          required:
            - id
            - timestamp
          properties:
            id:
              type: string
              description: The book's unique identifier
            book:
              type: object
              description: The book's details
            timestamp:
              type: string
              description: Year of book
    responses:
      201:
        description: Book successfully added
        schema:
          type: object
          properties:
            message:
              type: string
            cached_data:
              type: object
      400:
        description: Invalid request
      500:
        description: Server error
    """
    try:
        data = request.json
        if not data or 'id' not in data:
            return jsonify({"error": "Invalid request"}), 400
        book_id = data['id']

        #Store in redis first
        try:
            cache.set(book_id, json.dumps(data))
        except redis.RedisError as e:
            print(f"Reids error: {str(e)}")
        
        # Post to dynamo even if cache fails
        try:
            table.put_item(Item=data)
        except boto3.exceptions.Boto3Error as e:
            cache.delete(book_id) # Delete from cache if dynamoDB fails
            return jsonify({"error": f"Failed to store in DynamoDB: {str(e)}"}), 500
        
        # Successful
        try:
            cached_data = cache.get(book_id)
            return jsonify({
                "message": "Book added successfully",
                "cached_data": json.loads(cached_data) if cached_data else None
                }), 201
        except(redis.RedisError, json.JSONDecodeError) as e:
            # If data is not cached but saved to dynamo, give warning
            return jsonify({
                "message": "Book added successfully",
                "Warning": "Cached data unavailable",
                "cached_data": None
            }), 201
    except Exception as e:
        return jsonify({"error": f"An un expeted error occured: {str(e)}"}), 500

# GET
@app.route('/books/<id>', methods=['GET'])
def get_book(id):
    """
    Retrieve a book by its ID from cache or database.
    ---
    tags:
      - books
    parameters:
      - name: id
        in: path
        type: string
        required: true
        description: The book's unique identifier
    responses:
      200:
        description: Book found and returned
        schema:
          type: object
          properties:
            id:
              type: string
            book:
              type: object
            timestamp:
              type: string
      404:
        description: Book not found
      500:
        description: Server error
    """
    try:
        # Getting data from cache
        try:
            cached_data = cache.get(id)
            if cached_data:
                print("Cache hit!: returning from Redis")
                return jsonify(json.loads(cached_data)), 200
        except redis.RedisError as e:
            print(f"Redis error while fetching{str(e)}")
        except json.JSONDecodeError as e:
            print(f"Error decoding cached data: {str(e)}")

        #Fetch from Dynamo
        try:
            response = table.get_item(Key={'id': id, 'timestamp': '2023'})
            item = response.get('Item')
            if item:
                try:
                    cache.set(id, json.dumps(item),ex=3600) #Cache expires after hour
                except redis.RedisError as e:
                    print(f"Redis error while setting: {str(e)}")
                return jsonify(item), 200
            return jsonify({"error": "Book not found"}), 404
        except boto3.exceptions.Boto3Error as e:
            return jsonify({"error": f"DynamoDB error: {str(e)}"}), 500
            
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500
        
# PUT
@app.route('/books/<id>', methods=['PUT'])
def update_book(id):
    """
    Update an existing book's information.
    ---
    tags:
      - books
    parameters:
      - name: id
        in: path
        type: string
        required: true
        description: The book's unique identifier
      - in: body
        name: book
        required: true
        schema:
          type: object
          required:
            - book
            - id
          properties:
            book:
              type: object
              description: The updated book details
            id: 
              type: string
              description: book's unique identifier
    responses:
      200:
        description: Book successfully updated
        schema:
          type: object
          properties:
            message:
              type: string
            cached_data:
              type: object
            cache_status:
              type: string
      400:
        description: Invalid request
      500:
        description: Server error
    """
    try:
        # Validate input data
        data = request.json
        if not data or 'book' not in data:
            return jsonify({"error": "Invalid request. 'book' field is required"}), 400

        # Update DynamoDB
        try:
            table.update_item(
                Key={'id': id, 'timestamp': '2023'},
                UpdateExpression="SET book = :book",
                ExpressionAttributeValues={
                    ':book': data['book']
                }
            )
        except boto3.exceptions.Boto3Error as e:
            return jsonify({"error": f"DynamoDB update failed: {str(e)}"}), 500

        # Update Redis cache
        updated_data = {"id": id, "timestamp": "2023", "book": data["book"]}
        try:
            cache.set(id, json.dumps(updated_data), ex=3600)
        except redis.RedisError as e:
            print(f"Redis cache update failed: {str(e)}")
            # Continue execution as DynamoDB update was successful

        # Retrieve from Redis to confirm update
        try:
            cached_data = cache.get(id)
            return jsonify({
                "message": "Book updated successfully",
                "cached_data": json.loads(cached_data) if cached_data else None,
                "cache_status": "updated" if cached_data else "update_failed"
            }), 200
        except (redis.RedisError, json.JSONDecodeError) as e:
            return jsonify({
                "message": "Book updated successfully in database",
                "warning": f"Cache retrieval failed: {str(e)}",
                "cached_data": None
            }), 200

    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


@app.route('/books/<id>', methods=["DELETE"])
def delete_book(id):
    """
    Delete a book by its ID from both database and cache.
    ---
    tags:
      - books
    parameters:
      - name: id
        in: path
        type: string
        required: true
        description: The book's unique identifier
    responses:
      200:
        description: Book successfully deleted
        schema:
          type: object
          properties:
            message:
              type: string
            cache_status:
              type: string
              enum: [deleted, delete_failed]
      500:
        description: Server error
    """
    try:
        # Delete from DynamoDB
        try:
            table.delete_item(Key={'id': id, 'timestamp': '2023'})
        except boto3.exceptions.Boto3Error as e:
            return jsonify({
                "error": f"Failed to delete from DynamoDB: {str(e)}"
            }), 500

        # Remove from Redis
        try:
            cache.delete(id)
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

if __name__ == '__main__':
=======
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
>>>>>>> 59b1349 (Modularizing)
    app.run(debug=True)