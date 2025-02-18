import redis

class CacheService:
    def __init__(self, host='localhost', port=6379, db=0):
        self.cache = redis.Redis(
            host=host, 
            port=port, 
            db=db, 
            decode_responses=True
        )

    def get(self, key):
        return self.cache.get(key)

    def set(self, key, value, ex=None):
        return self.cache.set(key, value, ex=ex)

    def delete(self, key):
        return self.cache.delete(key)

    def setex(self, key, time, value):
        return self.cache.setex(key, time, value)

    def incr(self, key):
        return self.cache.incr(key)

    def expire(self, key, time):
        return self.cache.expire(key, time)

cache = CacheService()