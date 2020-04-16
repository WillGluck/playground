import pytest

from flaskr.db import get_db

def test_index(client, auth):
    response = client.get('/')
    assert b'Log In' in response.data
    assert b'Register' in response.data

    auth.login()
    response = client.get('/')
    assert b'Log Out' in response.data
    assert b'by test on 2020-01-01' in response.data
    assert b'test\nbody' in response.data
    assert b'href="/1/update"' in response.data

def test_detail(client, auth): 

    response = client.get('/1')
    assert b'by test on 2020-01-01' in response.data
    assert b'test\nbody' in response.data
    assert b'href="/1/update"' not in response.data
    assert b'href="/1/update"' not in response.data
    assert b'id="send_comment"'  not in response.data
    assert b'id="react_to_post"' not in response.data

    auth.login()
    response = client.get('/1')
    assert b'href="/1/update"' in response.data
    assert b'id="send_comment"'  in response.data
    assert b'id="react_to_post"' in response.data



@pytest.mark.parametrize('path', (
    '/create',
    '/1/update',
    '/1/delete',
    '/1/react',
    '/1/create_comment',
    '/1/delete_comment'
))
def test_login_required(client, path):
    response = client.post(path)
    assert response.headers['Location'] == 'http://localhost/auth/login'

def test_author_required(app, client, auth):
    with app.app_context():
        db = get_db()
        db.execute('UPDATE post SET author_id = 2 WHERE id = 1')
        db.commit()

    auth.login()
    assert client.post('/1/update').status_code == 403
    assert client.post('/1/delete').status_code == 403
    assert b'href="/1/update"' not in client.get('/').data

@pytest.mark.parametrize('path', (
    '/2/update',
    '/2/delete',
    '/2'
))
def test_exists_required(client, auth, path):
    auth.login()
    client.post(path).status_code == 404

def test_create(app, client, auth):
    auth.login()
    assert client.get('/create').status_code == 200
    client.post('/create', data={'title':'created', 'body':'body'})

    with app.app_context():
        db = get_db()
        count = db.execute('SELECT COUNT(id) FROM post').fetchone()[0]
        assert count == 2

def test_update(app, client, auth):
    auth.login()
    assert client.get('/1/update').status_code == 200
    client.post('/1/update', data={'title':'updated', 'body':''})
    
    with app.app_context():
        db = get_db()
        post = db.execute('SELECT * FROM post WHERE id = 1').fetchone()
        assert post['title'] == 'updated'


@pytest.mark.parametrize('path', (
    '/create',
    '/1/update'
))
def test_create_update_validate(client, auth, path):
    auth.login()
    response = client.post(path, data={'title':'', 'body':''})
    assert b'Title is required.' in response.data


def test_delete(client, auth, app):
    auth.login()
    response = client.post('/1/delete')
    assert response.headers['Location'] == 'http://localhost/'

    with app.app_context():
        db = get_db()
        post = db.execute('SELECT * FROM post WHERE id = 1').fetchone()
        assert post is None


def test_react(client, auth, app):
    auth.login()
    with app.app_context():
        db = get_db()
        reaction = db.execute('SELECT * FROM reaction WHERE post_id = 1').fetchone()
        assert reaction is not None

    client.post('/1/react')
    with app.app_context():
        db = get_db()
        reaction = db.execute('SELECT * FROM reaction WHERE post_id = 1').fetchone()
        assert reaction is None

def test_create_comment_validation(client, auth, app):
    auth.login()
    response = client.post('/1/create_comment', data={'comment': ''})
    assert response.status_code == 400

def test_comment(client, auth, app):
    auth.login()
    client.get('/1/detail')
    response = client.post('/1/create_comment', data={'comment': 'Test comment'})
    assert response.headers['Location'] == 'http://localhost/'

    with app.app_context():
        db = get_db()
        commentCount = db.execute('SELECT COUNT(*) FROM comment WHERE post_id = 1').fetchone()[0]
        assert commentCount is 2

def test_delete_comment_author_required(client, auth, app):
    auth.login()    
    with app.app_context():
        db = get_db()
        db.execute('UPDATE comment SET user_id = 2 WHERE id = 1')
        db.commit()
    assert client.post('/1/delete_comment').status_code == 403

def test_delete_comment(client, auth, app):
    auth.login()
    with app.app_context():
        db = get_db()
        db.execute('UPDATE comment SET user_id = 1 WHERE id = 1')
        db.commit()
    assert client.post('/1/delete_comment').headers['Location'] == 'http://localhost/'
    
    with app.app_context():
        assert get_db().execute('SELECT COUNT(*) FROM comment WHERE post_id = 1').fetchone()[0] == 0
