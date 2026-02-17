from backend.services.auth_service import create_access_token, decode_access_token
import uuid


def test_jwt_token():
    user_id = uuid.uuid4()
    token = create_access_token(user_id)
    decoded_id = decode_access_token(token)
    assert decoded_id == user_id


def test_invalid_token():
    result = decode_access_token("invalid.token.here")
    assert result is None
