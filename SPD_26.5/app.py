"""
电商后台管理系统 — Flask Web 应用
支持角色权限控制（RBAC），登录后按角色显示不同菜单
"""
import pymysql
from flask import Flask, render_template, request, redirect, session, url_for
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '8632216hb?',
    'database': 'SPD_26.5',
    'charset': 'utf8mb4',
}

# ---------- 工具函数 ----------

def get_db():
    """获取数据库连接"""
    return pymysql.connect(**DB_CONFIG)


def get_staff_permissions(staff_id):
    """查询某个工作人员的权限列表（通过角色查）"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        SELECT DISTINCT p.permission_name
        FROM role_permissions rp
        JOIN permissions p ON rp.permission_id = p.permission_id
        JOIN staff s ON s.role_id = rp.role_id
        WHERE s.staff_id = %s
    ''', (staff_id,))
    perms = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return perms


def login_required(f):
    """装饰器：要求登录才能访问"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'staff_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def require_permission(perm_name):
    """装饰器：要求拥有特定权限才能访问"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'staff_id' not in session:
                return redirect(url_for('login'))
            perms = get_staff_permissions(session['staff_id'])
            if perm_name not in perms:
                return '没有权限访问', 403
            return f(*args, **kwargs)
        return decorated
    return decorator


# ---------- 登录 ----------

@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录页：GET 显示表单，POST 验证用户名密码"""
    error = None
    if request.method == 'POST':
        staff_name = request.form['user_name']
        password = request.form['password']
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            'SELECT staff_id, role_id FROM staff WHERE staff_name = %s AND login_password = %s',
            (staff_name, password)
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            session['staff_id'] = row[0]
            session['role_id'] = row[1]
            session['user_name'] = staff_name
            return redirect(url_for('dashboard'))
        else:
            error = '用户名或密码错误'
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    """退出登录"""
    session.clear()
    return redirect(url_for('login'))


# ---------- 首页看板 ----------

@app.route('/')
@login_required
def dashboard():
    conn = get_db()
    cur = conn.cursor()
    # 统计数据
    cur.execute('SELECT COUNT(*) FROM users')
    user_count = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM products')
    product_count = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM orders')
    order_count = cur.fetchone()[0]
    cur.execute('SELECT COALESCE(SUM(total_amount),0) FROM orders WHERE order_status != %s', ('已取消',))
    total_sales = cur.fetchone()[0]
    cur.close()
    conn.close()
    perms = get_staff_permissions(session['staff_id'])
    return render_template('dashboard.html',
                           user_name=session['user_name'],
                           perms=perms,
                           user_count=user_count,
                           product_count=product_count,
                           order_count=order_count,
                           total_sales=total_sales)


# ---------- 用户管理 ----------

@app.route('/users')
@login_required
@require_permission('view_users')
def user_list():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        SELECT u.user_id, u.user_name, u.phone_num, u.address,
               u.user_level, u.created_at
        FROM users u
        ORDER BY u.user_id
    ''')
    users = cur.fetchall()
    cur.close()
    conn.close()
    perms = get_staff_permissions(session['staff_id'])
    return render_template('users.html', users=users, perms=perms,
                           user_name=session['user_name'],
                           can_edit='edit_users' in perms)


# ---------- 商品管理 ----------

@app.route('/products')
@login_required
@require_permission('view_products')
def product_list():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM products ORDER BY product_id')
    products = cur.fetchall()
    cur.close()
    conn.close()
    perms = get_staff_permissions(session['staff_id'])
    return render_template('products.html', products=products, perms=perms,
                           user_name=session['user_name'],
                           can_edit='edit_products' in perms,
                           can_edit_inventory='edit_inventory' in perms)


@app.route('/products/update', methods=['POST'])
@login_required
@require_permission('edit_products')
def product_update():
    """修改商品信息（名称、品类、价格、描述）"""
    pid = request.form['product_id']
    name = request.form['product_name']
    cat = request.form['category']
    price = request.form['price']
    desc = request.form['description']
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        'UPDATE products SET product_name=%s, category=%s, price=%s, description=%s WHERE product_id=%s',
        (name, cat, price, desc, pid)
    )
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('product_list'))


@app.route('/products/inventory', methods=['POST'])
@login_required
@require_permission('edit_inventory')
def inventory_update():
    """修改商品库存"""
    pid = request.form['product_id']
    inv = request.form['inventory']
    conn = get_db()
    cur = conn.cursor()
    cur.execute('UPDATE products SET inventory=%s WHERE product_id=%s', (inv, pid))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('product_list'))


# ---------- 订单管理 ----------

@app.route('/orders')
@login_required
@require_permission('view_orders')
def order_list():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        SELECT o.order_id, u.user_name, o.order_date, o.order_status,
               o.total_amount
        FROM orders o
        JOIN users u ON o.user_id = u.user_id
        ORDER BY o.order_date DESC
    ''')
    orders = cur.fetchall()
    cur.close()
    conn.close()
    perms = get_staff_permissions(session['staff_id'])
    return render_template('orders.html', orders=orders, perms=perms,
                           user_name=session['user_name'],
                           can_edit='edit_orders' in perms)


@app.route('/orders/status', methods=['POST'])
@login_required
@require_permission('edit_orders')
def order_status_update():
    """修改订单状态"""
    oid = request.form['order_id']
    status = request.form['order_status']
    conn = get_db()
    cur = conn.cursor()
    cur.execute('UPDATE orders SET order_status=%s WHERE order_id=%s', (status, oid))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('order_list'))


# ---------- 销售分析 ----------

@app.route('/analytics')
@login_required
@require_permission('view_analytics')
def analytics():
    perms = get_staff_permissions(session['staff_id'])
    return render_template('analytics.html',
                           user_name=session['user_name'],
                           perms=perms)


@app.route('/api/sales-trend')
@login_required
@require_permission('view_analytics')
def api_sales_trend():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        SELECT
            DATE_FORMAT(o.order_date, '%Y-%m') AS month,
            SUM(o.total_amount) AS monthly_sales,
            LAG(SUM(o.total_amount)) OVER (ORDER BY DATE_FORMAT(o.order_date, '%Y-%m')) AS prev_sales
        FROM orders o
        WHERE o.order_status != '已取消'
        GROUP BY DATE_FORMAT(o.order_date, '%Y-%m')
        ORDER BY month
    ''')
    rows = cur.fetchall()
    cur.close()
    conn.close()

    months, sales, growth = [], [], []
    for row in rows:
        months.append(row[0])
        sales.append(float(row[1]))
        if row[2] is not None and row[2] != 0:
            growth.append(round((row[1] - row[2]) / row[2] * 100, 1))
        else:
            growth.append(None)

    return {'months': months, 'sales': sales, 'growth': growth}


@app.route('/api/category-analysis')
@login_required
@require_permission('view_analytics')
def api_category_analysis():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        SELECT
            p.category,
            SUM(oi.quantity * oi.unit_price) AS total_sales
        FROM order_items oi
        JOIN products p ON oi.product_id = p.product_id
        JOIN orders o ON oi.order_id = o.order_id
        WHERE o.order_status != '已取消'
        GROUP BY p.category
        ORDER BY total_sales DESC
    ''')
    rows = cur.fetchall()
    cur.close()
    conn.close()

    total = float(sum(r[1] for r in rows))
    categories = [r[0] for r in rows]
    sales = [float(r[1]) for r in rows]
    proportions = [round(float(r[1]) / total * 100, 1) for r in rows]

    return {'categories': categories, 'sales': sales, 'proportions': proportions}


@app.route('/api/user-segmentation')
@login_required
@require_permission('view_analytics')
def api_user_segmentation():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        SELECT
            CASE
                WHEN total_spent < 500 THEN '0-500元'
                WHEN total_spent < 2000 THEN '500-2000元'
                WHEN total_spent < 5000 THEN '2000-5000元'
                WHEN total_spent < 10000 THEN '5000-10000元'
                ELSE '10000元以上'
            END AS segment,
            COUNT(*) AS user_count,
            ROUND(AVG(total_spent), 2) AS avg_consume
        FROM (
            SELECT u.user_id, COALESCE(SUM(o.total_amount), 0) AS total_spent
            FROM users u
            LEFT JOIN orders o ON u.user_id = o.user_id AND o.order_status != '已取消'
            GROUP BY u.user_id
        ) t
        GROUP BY segment
        ORDER BY MIN(total_spent)
    ''')
    rows = cur.fetchall()
    cur.close()
    conn.close()

    segments = [r[0] for r in rows]
    counts = [r[1] for r in rows]
    avg_consume = [float(r[2]) for r in rows]

    return {'segments': segments, 'counts': counts, 'avg_consume': avg_consume}


@app.route('/api/attribution')
@login_required
@require_permission('view_analytics')
def api_attribution():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        SELECT
            DATE_FORMAT(o.order_date, '%Y-%m') AS month,
            SUM(oi.quantity) AS total_qty,
            ROUND(SUM(oi.quantity * oi.unit_price) / SUM(oi.quantity), 2) AS avg_price
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.order_id
        WHERE o.order_status != '已取消'
        GROUP BY DATE_FORMAT(o.order_date, '%Y-%m')
        ORDER BY month
    ''')
    rows = cur.fetchall()
    cur.close()
    conn.close()

    periods = [r[0] for r in rows]
    qtys = [float(r[1]) for r in rows]
    prices = [float(r[2]) for r in rows]

    volume_effect, price_effect, mix_effect = [], [], []
    for i in range(len(rows)):
        if i == 0:
            volume_effect.append(0)
            price_effect.append(0)
            mix_effect.append(0)
        else:
            dq = qtys[i] - qtys[i-1]
            dp = prices[i] - prices[i-1]
            vol = round(dq * prices[i-1], 2)
            prc = round(qtys[i] * dp, 2)
            mix = round(dq * dp, 2)
            volume_effect.append(vol)
            price_effect.append(prc)
            mix_effect.append(mix)

    return {
        'periods': periods,
        'volume': volume_effect,
        'price': price_effect,
        'mix': mix_effect
    }


# ---------- 报表查询 ----------

@app.route('/api/categories')
@login_required
def api_categories():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT DISTINCT category FROM products ORDER BY category')
    categories = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return {'categories': categories}


REPORTS = [
    {'id': 1,  'name': '钻石会员列表',       'desc': '运营需导出钻石会员名单，用于双十一定向营销短信', 'type': 'table'},
    {'id': 2,  'name': '库存预警商品',       'desc': '仓库需盘点库存不足 100 件的商品，及时补货',     'type': 'table'},
    {'id': 3,  'name': '已取消订单查询',     'desc': '客服需查看所有已取消订单，分析取消原因',         'type': 'table'},
    {'id': 4,  'name': '品类商品统计',       'desc': '采购需了解各品类商品数量和均价分布',             'type': 'table'},
    {'id': 5,  'name': '用户下单排名',       'desc': '运营需按订单数排名用户，识别活跃用户',           'type': 'table'},
    {'id': 6,  'name': '每日销售额统计',     'desc': '财务需按日查看订单笔数和销售总额',               'type': 'table'},
    {'id': 7,  'name': '订单明细占比分析',   'desc': '运营需查看每个订单内各商品的金额占比',           'type': 'table'},
    {'id': 8,  'name': '用户客单价',         'desc': '运营需计算每位用户的平均每单消费金额',           'type': 'table'},
    {'id': 9,  'name': '交叉品类用户',       'desc': '运营想找同时买过两个品类的用户做捆绑营销（可选品类）', 'type': 'table', 'interactive': True},
    {'id': 10, 'name': '品类销量冠军',       'desc': '运营需查看每个品类中销量最高的明星商品',         'type': 'table'},
    {'id': 11, 'name': '动销率',             'desc': '运营需了解有销量的商品占比，评估库存健康度',     'type': 'card'},
    {'id': 12, 'name': '高价值用户 Top 20%',  'desc': '运营需识别消费总额前 20% 的 VIP 用户',          'type': 'table'},
    {'id': 13, 'name': '月度环比增长率',     'desc': '财务需按月查看销售额环比变化，监控业务趋势',     'type': 'table'},
    {'id': 14, 'name': '复购率',             'desc': '运营需了解下过 2 单及以上的用户占比，评估用户粘性', 'type': 'card'},
    {'id': 15, 'name': '用户消费全景视图',   'desc': '运营需查看每位用户的完整消费画像',               'type': 'table'},
]


@app.route('/reports')
@login_required
@require_permission('view_analytics')
def reports():
    perms = get_staff_permissions(session['staff_id'])
    return render_template('reports.html',
                           reports=REPORTS,
                           perms=perms,
                           user_name=session['user_name'])


@app.route('/api/report/<int:report_id>')
@login_required
@require_permission('view_analytics')
def api_report(report_id):
    conn = get_db()
    cur = conn.cursor()

    if report_id == 1:
        cur.execute("SELECT user_name, phone_num FROM users WHERE user_level = 3 ORDER BY user_id")
    elif report_id == 2:
        cur.execute("SELECT product_name, inventory FROM products WHERE inventory < 100 ORDER BY product_id")
    elif report_id == 3:
        cur.execute('''
            SELECT o.order_id, u.user_name, o.order_date
            FROM users u
            JOIN orders o ON o.user_id = u.user_id
            WHERE o.order_status = '已取消'
            ORDER BY o.order_date DESC
        ''')
    elif report_id == 4:
        cur.execute('''
            SELECT category, COUNT(*) AS product_count, ROUND(AVG(price), 2) AS avg_price
            FROM products
            GROUP BY category
            ORDER BY product_count DESC
        ''')
    elif report_id == 5:
        cur.execute('''
            SELECT u.user_id, u.user_name, COUNT(o.order_id) AS order_count,
                   RANK() OVER (ORDER BY COUNT(o.order_id) DESC) AS rank_num
            FROM users u
            LEFT JOIN orders o ON u.user_id = o.user_id
            GROUP BY u.user_id, u.user_name
        ''')
    elif report_id == 6:
        cur.execute('''
            SELECT order_date, COUNT(*) AS day_orders, SUM(total_amount) AS day_sales
            FROM orders
            WHERE order_status != '已取消'
            GROUP BY order_date
            ORDER BY order_date
        ''')
    elif report_id == 7:
        cur.execute('''
            SELECT order_id, product_id, quantity, unit_price,
                   ROUND(quantity * unit_price, 2) AS item_total,
                   ROUND(quantity * unit_price / SUM(quantity * unit_price) OVER(PARTITION BY order_id) * 100, 2) AS pct
            FROM order_items
            ORDER BY order_id, product_id
        ''')
    elif report_id == 8:
        cur.execute('''
            SELECT u.user_id, u.user_name,
                   SUM(o.total_amount) AS total_spent,
                   COUNT(*) AS order_count,
                   ROUND(SUM(o.total_amount) / COUNT(*), 2) AS avg_order_value
            FROM orders o
            JOIN users u ON o.user_id = u.user_id
            WHERE o.order_status != '已取消'
            GROUP BY u.user_id, u.user_name
            ORDER BY avg_order_value DESC
        ''')
    elif report_id == 9:
        cat1 = request.args.get('cat1', '手机数码')
        cat2 = request.args.get('cat2', '影音娱乐')
        cur.execute('''
            SELECT u.user_id, u.user_name
            FROM users u
            WHERE EXISTS (
                SELECT 1 FROM orders o
                JOIN order_items oi ON o.order_id = oi.order_id
                JOIN products p ON oi.product_id = p.product_id
                WHERE o.user_id = u.user_id AND p.category = %s AND o.order_status != '已取消'
            )
            AND EXISTS (
                SELECT 1 FROM orders o
                JOIN order_items oi ON o.order_id = oi.order_id
                JOIN products p ON oi.product_id = p.product_id
                WHERE o.user_id = u.user_id AND p.category = %s AND o.order_status != '已取消'
            )
            ORDER BY u.user_id
        ''', (cat1, cat2))
    elif report_id == 10:
        cur.execute('''
            SELECT product_id, product_name, category, sales
            FROM (
                SELECT p.product_id, p.product_name, p.category,
                       SUM(oi.quantity) AS sales,
                       RANK() OVER (PARTITION BY p.category ORDER BY SUM(oi.quantity) DESC) AS rk
                FROM order_items oi
                JOIN products p ON p.product_id = oi.product_id
                GROUP BY p.product_id, p.product_name, p.category
            ) t
            WHERE rk = 1
            ORDER BY category
        ''')
    elif report_id == 11:
        cur.execute('''
            SELECT
                (SELECT COUNT(DISTINCT product_id) FROM order_items) AS active_products,
                (SELECT COUNT(*) FROM products) AS total_products,
                ROUND((SELECT COUNT(DISTINCT product_id) FROM order_items) / (SELECT COUNT(*) FROM products) * 100, 2) AS sell_through_rate
        ''')
    elif report_id == 12:
        cur.execute('''
            SELECT user_id, user_name, user_total_amount
            FROM (
                SELECT u.user_id, u.user_name,
                       SUM(o.total_amount) AS user_total_amount,
                       NTILE(5) OVER (ORDER BY SUM(o.total_amount) DESC) AS per
                FROM users u
                JOIN orders o ON u.user_id = o.user_id
                WHERE o.order_status != '已取消'
                GROUP BY u.user_id, u.user_name
            ) t
            WHERE per = 1
            ORDER BY user_total_amount DESC
        ''')
    elif report_id == 13:
        cur.execute('''
            SELECT month, month_amount AS monthly_sales,
                   ROUND((month_amount - lats_month_amount) / lats_month_amount * 100, 2) AS mom_growth
            FROM (
                SELECT DATE_FORMAT(order_date, '%Y-%m') AS month,
                       SUM(total_amount) AS month_amount,
                       LAG(SUM(total_amount)) OVER (ORDER BY DATE_FORMAT(order_date, '%Y-%m')) AS lats_month_amount
                FROM orders
                WHERE order_status != '已取消'
                GROUP BY DATE_FORMAT(order_date, '%Y-%m')
                ORDER BY DATE_FORMAT(order_date, '%Y-%m')
            ) t
        ''')
    elif report_id == 14:
        cur.execute('''
            SELECT
                (SELECT COUNT(*) FROM (
                    SELECT user_id FROM orders
                    WHERE order_status != '已取消'
                    GROUP BY user_id
                    HAVING COUNT(*) >= 2
                ) t) AS repeat_users,
                (SELECT COUNT(DISTINCT user_id) FROM orders WHERE order_status != '已取消') AS total_users,
                ROUND(
                    (SELECT COUNT(*) FROM (
                        SELECT user_id FROM orders
                        WHERE order_status != '已取消'
                        GROUP BY user_id
                        HAVING COUNT(*) >= 2
                    ) t) / (SELECT COUNT(DISTINCT user_id) FROM orders WHERE order_status != '已取消') * 100, 2
                ) AS repurchase_rate
        ''')
    elif report_id == 15:
        cur.execute('SELECT user_name, created_at, first_order_time, user_total_amount, total_orders_count, kedanjia AS avg_order_value, last_order_time FROM user_consumption_view ORDER BY user_total_amount DESC')
    else:
        cur.close()
        conn.close()
        return {'error': '报表不存在'}, 404

    columns = [desc[0] for desc in cur.description] if cur.description else []
    rows = cur.fetchall()

    def convert(val):
        from decimal import Decimal
        if isinstance(val, Decimal):
            return float(val)
        if isinstance(val, bytes):
            return val.decode()
        return val

    data = [[convert(v) for v in row] for row in rows]

    cur.close()
    conn.close()
    return {'columns': columns, 'rows': data, 'type': REPORTS[report_id - 1]['type']}


# ---------- 启动 ----------

if __name__ == '__main__':
    app.run(debug=True)
