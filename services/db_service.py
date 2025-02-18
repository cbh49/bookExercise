import boto3

class DynamoDBService:
    def __init__(self, region_name='us-east-2', table_name='bookTest'):
        self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
        self.table = self.dynamodb.Table(table_name)

    def get_item(self, id, timestamp):
        return self.table.get_item(Key={'id': id, 'timestamp': timestamp})

    def put_item(self, item):
        return self.table.put_item(Item=item)

    def update_item(self, id, timestamp, book_data):
        return self.table.update_item(
            Key={'id': id, 'timestamp': timestamp},
            UpdateExpression="SET book = :book",
            ExpressionAttributeValues={':book': book_data}
        )

    def delete_item(self, id, timestamp):
        return self.table.delete_item(Key={'id': id, 'timestamp': timestamp})

db = DynamoDBService()