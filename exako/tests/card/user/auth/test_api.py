import pytest
from django.urls import reverse_lazy
from freezegun import freeze_time

from exako.tests.factories.user import UserFactory

token_url = reverse_lazy('api-1.0.0:create_access_token')
refresh_token_url = reverse_lazy('api-1.0.0:refresh_access_token')

pytestmark = pytest.mark.django_db


def test_get_token(client, user):
    response = client.post(
        token_url,
        data={'email': user.email, 'password': user.clean_password},
    )
    token = response.json()

    assert response.status_code == 200
    assert 'access_token' in token
    assert 'token_type' in token


def test_token_inexistent_user(client):
    response = client.post(
        token_url,
        data={'email': 'no_user@no_domain.com', 'password': 'testtest'},
    )
    assert response.status_code == 401
    assert response.json() == {'detail': 'could not validate credentials.'}


def test_token_wrong_password(client):
    user = UserFactory()
    response = client.post(
        token_url,
        data={'email': user.email, 'password': 'wrong_password'},
    )
    assert response.status_code == 401
    assert response.json() == {'detail': 'could not validate credentials.'}


def test_refresh_token(client, token_header):
    response = client.post(refresh_token_url, headers=token_header)

    data = response.json()

    assert response.status_code == 200
    assert 'access_token' in data
    assert 'token_type' in data
    assert response.json()['token_type'] == 'Bearer'


def test_token_expiry(client, user):
    with freeze_time('2023-07-14 12:00:00'):
        response = client.post(
            token_url,
            data={'email': user.email, 'password': user.clean_password},
        )
        assert response.status_code == 200
        token = response.json()['access_token']

    with freeze_time('2023-07-30 21:00:00'):
        response = client.post(
            refresh_token_url,
            headers={'Authorization': f'Bearer {token}'},
        )
        assert response.status_code == 401
        assert response.json() == {'detail': 'could not validate credentials.'}
