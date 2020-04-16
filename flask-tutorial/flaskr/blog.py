from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('blog', __name__)

@bp.route('/')
def index():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, p.title, p.body, p.created, p.author_id, u.username, r.count reaction_count, c.count comment_count'
        ' FROM post p'
        ' JOIN user u ON p.author_id = u.id'
        ' LEFT JOIN (SELECT post_id, COUNT(user_id) count FROM reaction GROUP BY post_id) r ON r.post_id = p.id'
        ' LEFT JOIN (select post_id, COUNT(id) count FROM comment GROUP BY post_id) c ON c.post_id = p.id'
        ' GROUP BY p.id, p.title, p.body, p.created, p.author_id, u.username'
        ' ORDER BY p.created DESC'
    ).fetchall()
    return render_template('blog/index.html', posts=posts)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if (request.method == 'POST'):
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'
        
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post (title, body, author_id)'
                ' VALUES (?, ?, ?)',
                (title, body, g.user['id'])
            )
            db.commit()
            return redirect(url_for('blog.index'))
    
    return render_template('blog/create.html')

def get_post(id, check_author=True):
    db = get_db()
    post = db.execute(
        'SELECT p.id, p.title, p.body, p.created, p.author_id, u.username'
        ' FROM post p'
        ' JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        ( id,)
    ).fetchone()

    if post is None:
        abort(404, "Post id {0} doesn't exist.".format(id)) #Not Found

    if check_author and post['author_id'] != g.user['id']:
        abort(403) #Forbidden

    #401 Unauthorized is redirected to index
    return post

def get_reactions(post_id):
    return get_db().execute(
        'SELECT u.username'
        ' FROM reaction r JOIN user u ON r.user_id = u.id and r.post_id = ?1'
        ' WHERE r.post_id = ?1',
        (post_id,)
    ).fetchall()

def get_comments(post_id):
    return get_db().execute(
        'SELECT c.id, c.body, c.created, c.user_id, u.username'
        ' FROM comment c JOIN user u ON c.user_id = u.id'
        ' WHERE c.post_id = ?'
        ' ORDER BY created DESC',
        (post_id,)
    ).fetchall()

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):

    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?'
                ' WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('blog.index'))
    
    return render_template('blog/update.html', post=post)

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    post = get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (post['id'],))
    db.commit()
    return redirect(url_for('blog.index'))

@bp.route('/<int:id>')
def detail(id):
    post = get_post(id, check_author=False)
    comments = get_comments(post['id'])
    reactions = get_reactions(post['id'])
    reacted = False
    if (g.user is not None):
        for reaction in reactions:
            if reaction['username'] == g.user['username']:
                reacted = True
                break
    return render_template('blog/detail.html', post=post, comments=comments, reactions=reactions, reacted=reacted)

@bp.route('/<int:id>/react', methods=['POST'])
@login_required
def react(id):
    post = get_post(id, check_author=False)
    post_id = post['id']
    user_id = g.user['id']

    db = get_db()
    reacted = db.execute(
        'SELECT 1 FROM reaction WHERE post_id = ? AND user_id = ?',
        (post_id, user_id)
    ).fetchone() != None

    if (reacted):
        db.execute('DELETE FROM reaction WHERE user_id = ? and post_id = ?', (user_id, post_id,))
    else:
        db.execute('INSERT INTO reaction (user_id, post_id) VALUES (?, ?)', (user_id, post_id,))
    db.commit()

    return redirect(url_for('blog.index'))


@bp.route('/<int:id>/create_comment', methods=['POST'])
@login_required
def create_comment(id):
    
    comment = request.form['comment']
    post = get_post(id, check_author=False)
    post_id = post['id']
    user_id = g.user['id']

    if not comment:
        abort(400, "Comment can't be null")
    
    db = get_db()
    db.execute(
        'INSERT INTO comment (post_id, user_id, body) VALUES (?, ?, ?)',
        (post_id, user_id, comment,)
    )
    db.commit()
    return redirect(url_for('blog.index'))
    
@bp.route('/<int:id>/delete_comment', methods=['POST'])
@login_required
def delete_comment(id):
    
    db = get_db()
    comment = db.execute(
        'SELECT * FROM comment WHERE id = ?',
        (id,)
    ).fetchone()

    if comment is None:
        abort(404, "Comment id {} doesn't exist.".format(id))
    if comment['user_id'] != g.user['id']:
        abort(403)

    db.execute('DELETE FROM comment WHERE id = ?', (id,))
    db.commit()

    return redirect(url_for('blog.index'))
        
        
