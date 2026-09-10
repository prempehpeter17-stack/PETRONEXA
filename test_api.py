import os
os.environ.setdefault('DATABASE_URL', 'sqlite+aiosqlite:///./test_petronexa.db')
os.environ.setdefault('ENVIRONMENT', 'test')

from fastapi.testclient import TestClient
from main import app


def test_health():
    with TestClient(app) as client:
        response = client.get('/health')
        assert response.status_code == 200
        assert response.json()['status'] == 'ok'


def test_register_login_me():
    with TestClient(app) as client:
        email = 'api-test@example.com'
        client.post('/api/v1/auth/register', json={
            'email': email,
            'password': 'StrongPass123',
            'username': 'api_test_user',
            'company_name': 'Test Company',
        })
        response = client.post('/api/v1/auth/login', data={'username': email, 'password': 'StrongPass123'})
        assert response.status_code == 200
        token = response.json()['access_token']
        me = client.get('/api/v1/me', headers={'Authorization': f'Bearer {token}'})
        assert me.status_code == 200
        assert me.json()['email'] == email
