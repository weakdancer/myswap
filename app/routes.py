from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, g
from app.db import get_db
from datetime import datetime
import hashlib
import hmac
import re
import urllib.request
import ssl
from werkzeug.security import check_password_hash, generate_password_hash

bp = Blueprint('main', __name__)

def sha1(s):
    """计算字符串的 SHA1 哈希"""
    return hashlib.sha1(s.encode()).hexdigest()

def valid_email(email):
    """验证邮箱格式"""
    if re.match(r'^\S+@[\w\d.\-]{2,}\.[\w]{2,6}$', email, re.IGNORECASE):
        return "valid"
    return "invalid email address"

def valid_username(username):
    """验证用户名（只能包含字母和数字）"""
    if not re.match(r'^[a-zA-Z0-9]+$', username):
        return "The username should contain only letters, numbers."
    
    db = get_db()
    user = db.execute('SELECT * FROM think_user WHERE LOWER(username) = LOWER(?)', (username,)).fetchone()
    if user:
        return "username have been taken"
    return "valid"

def valid_alias(user_id, alias):
    """验证别名（只能包含字母和数字）"""
    if not alias:
        return "valid"
    if not re.match(r'^[a-zA-Z0-9\-]+$', alias):
        return "The alias should contain only letters, numbers."
    
    db = get_db()
    swap = db.execute('SELECT * FROM think_swap WHERE LOWER(alias) = LOWER(?) AND user_id = ?', (alias, user_id)).fetchone()
    if swap:
        return "alias have been taken"
    return "valid"

def get_user_by_username(username):
    """通过用户名获取用户"""
    db = get_db()
    if username.isdigit():
        user = db.execute('SELECT * FROM think_user WHERE user_id = ?', (int(username),)).fetchone()
    else:
        user = db.execute('SELECT * FROM think_user WHERE LOWER(username) = LOWER(?)', (username,)).fetchone()
    return user

def get_user_by_id(user_id):
    """通过ID获取用户"""
    db = get_db()
    return db.execute('SELECT * FROM think_user WHERE user_id = ?', (user_id,)).fetchone()

def get_swap_by_id(swap_id):
    """通过ID获取swap"""
    db = get_db()
    return db.execute('SELECT * FROM think_swap WHERE swap_id = ?', (swap_id,)).fetchone()

def get_swap_by_alias(user_id, alias):
    """通过别名获取swap"""
    db = get_db()
    return db.execute('SELECT * FROM think_swap WHERE LOWER(alias) = LOWER(?) AND user_id = ?', (alias, user_id)).fetchone()

def auth_with_password(user, password):
    """验证密码"""
    if not user or not password:
        return False

    stored_hash = user['password']
    if re.fullmatch(r'[0-9a-f]{40}', stored_hash):
        # Upgrade existing local accounts only after their own password matches.
        if not hmac.compare_digest(sha1(password), stored_hash):
            return False
        db = get_db()
        db.execute('UPDATE think_user SET password = ? WHERE user_id = ?',
                   (generate_password_hash(password), user['user_id']))
        db.commit()
        return True
    try:
        return check_password_hash(stored_hash, password)
    except ValueError:
        return False

def get_friends(user):
    """获取朋友列表"""
    if not user or not user['friends']:
        return []
    return [f.strip() for f in user['friends'].split(' ') if f.strip()]

def get_aliases(user):
    """获取别名列表"""
    if not user or not user['userAliases']:
        return []
    return [a.strip() for a in user['userAliases'].split(' ') if a.strip()]

def get_d_c_date(user):
    """计算 D_C_date（从生日到今天的日期差 + 当天时间比例）"""
    if not user or not user['birthday']:
        return 0
    
    try:
        birthday = datetime.strptime(user['birthday'], '%Y-%m-%d')
        today = datetime.now()
        days = (today.date() - birthday.date()).days
        
        now_hour = today.hour
        now_minute = today.minute
        now_ratio = ((now_hour * 60) + now_minute) / (24 * 60)
        
        return days + now_ratio
    except:
        return 0

def tranform_url(text):
    """转换文本中的URL为链接"""
    if not text:
        return ''
    # 将URL转换为链接
    url_pattern = r'((https?|file)://([-\w.]+)+(:\d+)?(/[^\s^\n]*)?)'
    return re.sub(url_pattern, r'<a target="_blank" class="myswap-link" href="\1">\1</a>', text)

@bp.route('/')
def index():
    """首页"""
    db = get_db()
    users = db.execute('SELECT * FROM think_user').fetchall()
    return render_template('index.html', users=users)

@bp.route('/Signup', methods=['GET', 'POST'])
def signup():
    """注册页面"""
    msg_error = ''
    msg_success = ''
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        email = request.form.get('email', '')
        username = request.form.get('username', '')
        friends = request.form.get('friends', '')
        
        if not password:
            msg_error = "password cannot be empty"
        elif password != confirm_password:
            msg_error = "password did not match"
        elif valid_email(email) != "valid":
            msg_error = valid_email(email)
        elif valid_username(username) != "valid":
            msg_error = valid_username(username)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO think_user (username, email, password, friends, userAliases) VALUES (?, ?, ?, ?, ?)',
                (username.lower(), email, generate_password_hash(password), friends, '')
            )
            db.commit()
            msg_success = "signed up"
            return redirect(f'/{username}/')
    
    return render_template('signup.html', msg_error=msg_error, msg_success=msg_success)

@bp.route('/<username>')
@bp.route('/<username>/')
def user_index(username):
    """用户主页"""
    user = get_user_by_username(username)
    
    if not user:
        return render_template('404.html'), 404
    
    offset = max(0, request.args.get('offset', 0, type=int))
    limit = max(1, min(100, request.args.get('limit', 100, type=int)))
    all_mode = request.args.get('all', '')
    display_content = request.args.get('display_content', 'true')
    
    if display_content == 'false':
        limit = 100
    elif all_mode == 'true':
        limit = 100
    
    db = get_db()
    swaps = db.execute(
        '''SELECT * FROM think_swap 
           WHERE user_id = ? AND alias NOT LIKE 's-%' 
           ORDER BY swap_id DESC LIMIT ? OFFSET ?''',
        (user['user_id'], limit, offset)
    ).fetchall()
    
    friends = get_friends(user)
    aliases = get_aliases(user)
    d_c_date = get_d_c_date(user)
    
    return render_template('swap.html', 
                          settings=user,
                          username=username,
                          swaps=swaps,
                          friends=friends,
                          aliases=aliases,
                          d_c_date=d_c_date,
                          display_content=display_content)

@bp.route('/<username>/<alias>')
@bp.route('/<username>/<alias>/')
def single_swap(username, alias):
    """单个swap页面"""
    user = get_user_by_username(username)
    
    if not user:
        return render_template('404.html'), 404
    
    # 判断alias是数字ID还是字符串别名
    if alias.isdigit():
        swap = get_swap_by_id(int(alias))
        if swap and swap['user_id'] != user['user_id']:
            return render_template('404.html'), 404
    else:
        swap = get_swap_by_alias(user['user_id'], alias)
    
    about_to_create_alias = ''
    msg_error = ''
    
    if not swap:
        about_to_create_alias = alias
        msg_error = "have't create yet"
    
    d_c_date = get_d_c_date(user)
    strip = request.args.get('strip', '')
    
    if strip:
        # 纯文本模式，直接返回内容
        from flask import Response
        if swap:
            return Response(swap['content'], mimetype='text/plain')
        else:
            return Response('', mimetype='text/plain')
    
    return render_template('single_swap.html',
                          settings=user,
                          username=username,
                          alias=alias,
                          swap=swap,
                          about_to_create_alias=about_to_create_alias,
                          msg_error=msg_error,
                          d_c_date=d_c_date)

@bp.route('/<username>/setting', methods=['GET', 'POST'])
@bp.route('/<username>/setting/', methods=['GET', 'POST'])
def setting(username):
    """设置页面"""
    user = get_user_by_username(username)
    
    if not user:
        return render_template('404.html'), 404
    
    msg_error = ''
    msg_success = ''
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        
        if auth_with_password(user, password):
            new_data = {}
            
            birthday = request.form.get('birthday', '')
            if birthday:
                new_data['birthday'] = birthday.strip()
            
            user_aliases = request.form.get('userAliases', '')
            if user_aliases:
                new_data['userAliases'] = user_aliases.strip()
            
            friends = request.form.get('friends', '')
            if friends:
                new_data['friends'] = friends.strip()
            
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')
            if new_password:
                if new_password == confirm_password:
                    new_data['password'] = generate_password_hash(new_password)
                else:
                    msg_error = "password did not match"
            
            new_username = request.form.get('username', '')
            if new_username and new_username.lower() != username.lower():
                if valid_username(new_username) == "valid":
                    new_data['username'] = new_username
                else:
                    msg_error = valid_username(new_username)
            
            if not msg_error:
                db = get_db()
                if new_data:
                    fields = []
                    values = []
                    for key, value in new_data.items():
                        fields.append(f"{key} = ?")
                        values.append(value)
                    values.append(user['user_id'])
                    db.execute(f"UPDATE think_user SET {', '.join(fields)} WHERE user_id = ?", values)
                    db.commit()
                
                msg_success = "saved"
                # 如果修改了用户名，重新获取用户
                if 'username' in new_data:
                    user = get_user_by_username(new_username)
                else:
                    user = get_user_by_username(username)
        else:
            msg_error = "wrong password"
    
    return render_template('setting.html', 
                          settings=user,
                          msg_error=msg_error,
                          msg_success=msg_success)

@bp.route('/<username>/auth', methods=['GET', 'POST'])
@bp.route('/<username>/auth/', methods=['GET', 'POST'])
def auth(username):
    """验证页面"""
    user = get_user_by_username(username)
    
    if not user:
        return render_template('404.html'), 404
    
    msg_error = ''
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        if auth_with_password(user, password):
            return redirect(f'/{username}/')
        else:
            msg_error = "wrong password"
    
    return render_template('auth.html', 
                          settings=user,
                          msg_error=msg_error)

@bp.route('/<username>/addSwap', methods=['POST'])
@bp.route('/<username>/addSwap/', methods=['POST'])
def add_swap(username):
    """添加swap"""
    user = get_user_by_username(username)
    
    if not user:
        return render_template('404.html'), 404
    
    msg_error = ''
    password = request.form.get('password', '')
    
    if auth_with_password(user, password):
        alias = request.form.get('alias', '')
        content = request.form.get('content', '')
        
        if valid_alias(user['user_id'], alias) == "valid" or not alias:
            if content:
                db = get_db()
                cursor = db.execute(
                    'INSERT INTO think_swap (user_id, content, alias) VALUES (?, ?, ?)',
                    (user['user_id'], content, alias)
                )
                db.commit()
                swap_id = cursor.lastrowid
                
                # 如果没有alias，使用swap_id作为redirect目标
                redirect_alias = alias if alias else str(swap_id)
                return redirect(f'/{username.lower()}/{redirect_alias}')
            else:
                msg_error = "content cannot be empty"
        else:
            msg_error = valid_alias(user['user_id'], alias)
    else:
        msg_error = "wrong password"
    
    if msg_error:
        swaps = get_db().execute(
            'SELECT * FROM think_swap WHERE user_id = ? ORDER BY swap_id DESC LIMIT 2',
            (user['user_id'],)
        ).fetchall()
        return render_template('swap.html',
                              settings=user,
                              username=username,
                              swaps=swaps,
                              friends=get_friends(user),
                              aliases=get_aliases(user),
                              d_c_date=get_d_c_date(user),
                              display_content='true',
                              msg_error=msg_error)

@bp.route('/<username>/updateSwap', methods=['POST'])
@bp.route('/<username>/updateSwap/', methods=['POST'])
def update_swap(username):
    """更新swap"""
    user = get_user_by_username(username)
    
    if not user:
        return render_template('404.html'), 404

    swap_id = request.form.get('swap_id', type=int)
    swap = get_swap_by_id(swap_id) if swap_id is not None else None
    if not swap or swap['user_id'] != user['user_id']:
        return render_template('404.html'), 404
    
    msg_error = ''
    password = request.form.get('password', '')
    
    if auth_with_password(user, password):
        content = request.form.get('content', '')
        alias = request.form.get('alias', '')
        last_alias = swap['alias']
        
        new_data = {}
        if content:
            new_data['content'] = content
        
        if alias != last_alias:
            if valid_alias(user['user_id'], alias) == "valid":
                new_data['alias'] = alias
            else:
                msg_error = valid_alias(user['user_id'], alias)
        
        if not msg_error:
            db = get_db()
            if new_data:
                fields = []
                values = []
                for key, value in new_data.items():
                    fields.append(f"{key} = ?")
                    values.append(value)
                values.extend((swap_id, user['user_id']))
                db.execute(f"UPDATE think_swap SET {', '.join(fields)} WHERE swap_id = ? AND user_id = ?", values)
                db.commit()
            
            redirect_alias = alias if alias else str(swap_id)
            return redirect(f'/{username.lower()}/{redirect_alias}')
    else:
        msg_error = "wrong password"
    
    if msg_error:
        return render_template('single_swap.html',
                              settings=user,
                              username=username,
                              swap=swap,
                              d_c_date=get_d_c_date(user),
                              msg_error=msg_error)

@bp.route('/Scraper/Scrap', methods=['POST'])
def scraper():
    """抓取网页标题"""
    url = request.form.get('url', '')
    
    if not url:
        return jsonify({'title': ''})
    
    try:
        # 创建SSL上下文，忽略证书验证
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, context=ctx, timeout=5) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
        # 提取title
        match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        if match:
            title = match.group(1).strip()
            # 清理HTML实体
            title = re.sub(r'<[^>]+>', '', title)
            return f'"{title}"'
    except Exception as e:
        pass
    
    return f'"{url}"'

@bp.route('/<username>/RANDOM')
@bp.route('/<username>/RANDOM/')
def random_page(username):
    """RANDOM 页面（黑色背景的特殊页面）"""
    user = get_user_by_username(username)
    
    if not user:
        return render_template('404.html'), 404
    
    d_c_date = get_d_c_date(user)
    week_days = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"]
    week_day = week_days[datetime.now().weekday() + 1] if datetime.now().weekday() < 6 else week_days[0]
    
    return f'''<html><head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
</head><body style="background-color:black"><div style="height:20px;width:200px">
<h1 style="color:white">{username}{d_c_date}{datetime.now().strftime("|%Y/%m/%d|")}{week_day}</h1></div></body></html>'''

@bp.route('/<username>/WDDC')
@bp.route('/<username>/WDDC/')
def wddc_page(username):
    """WDDC 页面（带时间的黑色背景页面）"""
    user = get_user_by_username(username)
    
    if not user:
        return render_template('404.html'), 404
    
    d_c_date = get_d_c_date(user)
    week_days = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"]
    week_day = week_days[datetime.now().weekday()]
    
    return f'''<html><head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
</head><body style="background-color:black"><div style="height:20px;width:200px">
<h1 style="color:white">{username}{d_c_date}{datetime.now().strftime("|%Y/%m/%d %H:%M|")}{week_day}</h1></div></body></html>'''

@bp.route('/myswap/<path:page>')
def about_pages(page):
    """关于/FAQ等静态页面"""
    if 'about' in page.lower():
        return render_template('about.html')
    elif 'faq' in page.lower():
        return render_template('faq.html')
    elif 'howto' in page.lower():
        return render_template('howto.html')
    elif 'why' in page.lower():
        return render_template('why.html')
    return render_template('404.html'), 404

@bp.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404
