from http import HTTPStatus

from jwt import decode

from todo_list.security import ALGORITHM, SECRET_KEY, create_access_token


def test_jwt():
    data = {'sub': 'test@test.com'}
    token = create_access_token(data)
    decoded = decode(token, SECRET_KEY, algorithms=[ALGORITHM])

    assert decoded['sub'] == data['sub']
    assert decoded['exp']


def test_jwt_invalid_token(client, user):
    response = client.delete(f'/users/{user.id}', headers={'Authorization': 'Bearer TOKEN-INVALIDO'})
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Could not validate credentials'}
