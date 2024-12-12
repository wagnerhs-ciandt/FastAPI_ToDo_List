from http import HTTPStatus

import factory.fuzzy

from todo_list.models import ToDo, ToDoState


class ToDoFactory(factory.Factory):
    class Meta:
        model = ToDo

    title = factory.Faker('text')
    description = factory.Faker('text')
    state = factory.fuzzy.FuzzyChoice(ToDoState)
    user_id = 1


def test_list_todo_should_return_5_todos(session, client, user, token):
    expected_todos = 5
    session.bulk_save_objects(ToDoFactory.create_batch(5, user_id=user.id))
    session.commit()

    response = client.get('/todos', headers={'Authorization': f'Bearer {token}'})
    assert len(response.json()['todos']) == expected_todos


def test_list_todos_pagination_should_return_2_todos(session, user, client, token):
    expected_todos = 2
    session.bulk_save_objects(ToDoFactory.create_batch(5, user_id=user.id))
    session.commit()
    response = client.get(
        '/todos/?offset=1&limit=2',
        headers={'Authorization': f'Bearer {token}'},
    )
    assert len(response.json()['todos']) == expected_todos


def test_list_todos_filter_title_should_return_5_todos(session, user, client, token):
    expected_todos = 5
    session.bulk_save_objects(ToDoFactory.create_batch(5, user_id=user.id, title='Test todo 1'))
    session.commit()
    response = client.get('/todos/?title=Test todo 1', headers={'Authorization': f'Bearer {token}'})
    assert len(response.json()['todos']) == expected_todos


def test_list_todos_filter_description_should_return_5_todos(session, user, client, token):
    expected_todos = 5
    session.bulk_save_objects(ToDoFactory.create_batch(5, user_id=user.id, description='description'))
    session.commit()
    response = client.get('/todos/?description=desc', headers={'Authorization': f'Bearer {token}'})
    assert len(response.json()['todos']) == expected_todos


def test_list_todos_filter_state_should_return_5_todos(session, user, client, token):
    expected_todos = 5
    session.bulk_save_objects(ToDoFactory.create_batch(5, user_id=user.id, state=ToDoState.draft))
    session.commit()
    response = client.get('/todos/?state=draft', headers={'Authorization': f'Bearer {token}'})
    assert len(response.json()['todos']) == expected_todos


def test_list_todos_filter_combined_should_return_5_todos(session, user, client, token):
    expected_todos = 5
    session.bulk_save_objects(
        ToDoFactory.create_batch(
            5,
            user_id=user.id,
            title='Test todo combined',
            description='combined description',
            state=ToDoState.done,
        )
    )

    session.bulk_save_objects(
        ToDoFactory.create_batch(
            3,
            user_id=user.id,
            title='Other title',
            description='other description',
            state=ToDoState.todo,
        )
    )
    session.commit()

    response = client.get(
        '/todos/?title=Test todo combined&description=combined&state=done',
        headers={'Authorization': f'Bearer {token}'},
    )

    assert len(response.json()['todos']) == expected_todos


def test_patch_todo_error(client, token):
    response = client.patch(
        '/todos/10',
        json={},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Task not found.'}


def test_patch_todo(session, client, user, token):
    todo = ToDoFactory(user_id=user.id)

    session.add(todo)
    session.commit()

    response = client.patch(
        f'/todos/{todo.id}',
        json={'title': 'teste!'},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json()['title'] == 'teste!'


def test_delete_todo(session, client, user, token):
    todo = ToDoFactory(user_id=user.id)

    session.add(todo)
    session.commit()

    response = client.delete(f'/todos/{todo.id}', headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'Task has been deleted successfully.'}


def test_delete_todo_error(client, token):
    response = client.delete(f'/todos/{10}', headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {'detail': 'Task not found.'}


def test_create_todo(client, token, mock_db_time):
    with mock_db_time(model=ToDo) as time:
        response = client.post(
            '/todos',
            headers={'Authorization': f'Bearer {token}'},
            json={'title': 'Test ToDo', 'description': 'Test ToDo description', 'state': 'draft'},
        )
    assert response.json() == {
        'id': 1,
        'title': 'Test ToDo',
        'description': 'Test ToDo description',
        'state': 'draft',
        'created_at': time.isoformat(),
        'updated_at': time.isoformat(),
    }


def test_list_todos_shoud_return_all_expected_fields(session, client, user, token, mock_db_time):
    with mock_db_time(model=ToDo) as time:
        todo = ToDoFactory.create(user_id=user.id)
        session.add(todo)
        session.commit()

    session.refresh(todo)
    response = client.get(
        '/todos/',
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.json()['todos'] == [
        {
            'id': todo.id,
            'title': todo.title,
            'description': todo.description,
            'state': todo.state,
            'created_at': time.isoformat(),
            'updated_at': time.isoformat(),
        }
    ]
