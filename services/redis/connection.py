import redis

POOL = redis.ConnectionPool(host='localhost', port=6379, db=0)

# redis connection
r = redis.Redis(connection_pool=POOL)
