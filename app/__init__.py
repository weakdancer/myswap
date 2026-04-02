from flask import Flask
import os

def create_app():
    app = Flask(__name__, 
                static_folder='static',
                template_folder='templates')
    
    app.config['SECRET_KEY'] = 'myswap-secret-key-for-local-use'
    app.config['DATABASE'] = os.path.join(os.path.dirname(__file__), '..', 'myswap.db')
    
    # 注册数据库初始化
    from app import db
    db.init_app(app)
    
    # 注册模板过滤器
    from app import template_filters
    template_filters.init_filters(app)
    
    # 注册蓝图
    from app import routes
    app.register_blueprint(routes.bp)
    
    return app
