import re

def transform_url(text):
    """转换文本中的URL为链接"""
    if not text:
        return ''
    # 将URL转换为链接
    url_pattern = r'((https?|file)://([-\w.]+)+(:\d+)?(/[^\s^\n]*)?)'
    return re.sub(url_pattern, r'<a target="_blank" class="myswap-link" href="\1">\1</a>', text)

def init_filters(app):
    app.jinja_env.filters['transform_url'] = transform_url
