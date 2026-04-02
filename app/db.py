import sqlite3
from flask import current_app, g
from datetime import datetime

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    
    # 创建用户表
    db.execute('''
        CREATE TABLE IF NOT EXISTS think_user (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username CHAR(20) NOT NULL UNIQUE,
            email CHAR(40) NOT NULL,
            password VARCHAR(40) NOT NULL,
            friends TEXT NOT NULL DEFAULT '',
            userAliases TEXT NOT NULL DEFAULT '',
            birthday VARCHAR(40)
        )
    ''')
    
    # 创建swap表
    db.execute('''
        CREATE TABLE IF NOT EXISTS think_swap (
            swap_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            alias CHAR(20) NOT NULL DEFAULT '',
            content TEXT NOT NULL DEFAULT '',
            FOREIGN KEY (user_id) REFERENCES think_user (user_id)
        )
    ''')
    
    db.commit()

def init_app(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        init_db()
