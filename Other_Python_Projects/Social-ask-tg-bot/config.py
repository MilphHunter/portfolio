import redis.asyncio as redis

TOKEN = ''

redis_client = redis.from_url("redis://127.0.0.1:6379")
