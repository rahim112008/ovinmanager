import bcrypt
import jwt
import datetime

# Hash a password
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

# Verify a password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

# Create a JWT token
def create_jwt_token(data: dict, secret_key: str, expiration_minutes: int = 30) -> str:
    expiration = datetime.datetime.utcnow() + datetime.timedelta(minutes=expiration_minutes)
    token = jwt.encode({'exp': expiration, **data}, secret_key, algorithm='HS256')
    return token

# Decode a JWT token
def decode_jwt_token(token: str, secret_key: str) -> dict:
    try:
        decoded = jwt.decode(token, secret_key, algorithms=['HS256'])
        return decoded
    except jwt.ExpiredSignatureError:
        return {'error': 'Token has expired'}
    except jwt.InvalidTokenError:
        return {'error': 'Invalid token'}