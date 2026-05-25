"""
电商数据分析平台 — 测试数据生成脚本
插入顺序：roles → permissions → role_permissions → staff → users(顾客) → products → orders → order_items
数据量：10 工作人员 + 200 顾客 + 52 商品 + ~1000 订单 + ~3000 明细行
"""
import pymysql
import random
from datetime import datetime, timedelta

# ---------- 1. 连接数据库 ----------
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='8632216hb?',
    database='SPD_26.5',
    charset='utf8mb4'
)
cursor = conn.cursor()
print('数据库连接成功')

# ---------- 2. 确保表结构 ----------
cursor.execute('''
    CREATE TABLE IF NOT EXISTS roles(
        role_id int AUTO_INCREMENT primary key,
        role_name varchar(30) not null unique
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS permissions(
        permission_id int AUTO_INCREMENT primary key,
        permission_name varchar(50) not null unique,
        description varchar(100)
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS role_permissions(
        role_id int, permission_id int,
        PRIMARY KEY (role_id, permission_id),
        FOREIGN KEY (role_id) REFERENCES roles(role_id),
        FOREIGN KEY (permission_id) REFERENCES permissions(permission_id)
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS staff(
        staff_id int AUTO_INCREMENT primary key,
        staff_name varchar(50) not null,
        role_id int not null,
        login_password varchar(50) not null default '123456',
        created_at timestamp default current_timestamp,
        FOREIGN KEY (role_id) REFERENCES roles(role_id)
    )
''')
conn.commit()

# 清理旧结构遗留列
try:
    cursor.execute('ALTER TABLE users DROP FOREIGN KEY users_ibfk_1')
except:
    pass
try:
    cursor.execute('ALTER TABLE users DROP COLUMN role_id')
except:
    pass
try:
    cursor.execute('ALTER TABLE users DROP COLUMN login_password')
except:
    pass
conn.commit()
print('表结构已就绪')

# ---------- 3. 随机数据素材 ----------
# 40 个姓 × 40 个名 = 1600 种组合，够 200 人不重名
surnames = ['张','李','王','赵','刘','陈','杨','黄','周','吴','孙','马','朱','胡','林','何',
            '郭','高','罗','郑','梁','宋','谢','韩','唐','冯','于','董','萧','程','曹','袁','邓',
            '许','傅','沈','曾','彭','吕','苏']
given_names = ['伟','芳','娜','敏','静','强','磊','洋','勇','涛','杰','琳','慧','军','鹏','燕',
               '丽','鑫','超','文','宇','雪','婷','浩','明','宁','龙','辉','峰','毅','俊','博',
               '涵','璐','琪','瑶','晨','铭','瑞','然']

product_pool = [
    # 手机数码（7个）
    ('iPhone 16 Pro', '手机数码', 7999.00, '苹果旗舰手机，A18芯片'),
    ('华为 Mate 70', '手机数码', 6999.00, '华为旗舰手机，鸿蒙系统'),
    ('iPad Air M3', '手机数码', 4799.00, '苹果平板电脑'),
    ('小米 14 Ultra', '手机数码', 5999.00, '小米旗舰手机，徕卡影像'),
    ('OPPO Find X7', '手机数码', 4599.00, 'OPPO旗舰手机，哈苏影像'),
    ('vivo X100 Pro', '手机数码', 4999.00, 'vivo旗舰手机，蔡司影像'),
    ('三星 Galaxy S24', '手机数码', 6499.00, '三星AI旗舰手机'),
    # 电脑办公（7个）
    ('MacBook Air M4', '电脑办公', 8999.00, '苹果轻薄笔记本'),
    ('Logitech MX Master 3S', '电脑办公', 599.00, '高端无线鼠标'),
    ('机械革命 蛟龙16 Pro', '电脑办公', 6999.00, '游戏笔记本电脑'),
    ('罗技 K380', '电脑办公', 199.00, '蓝牙无线键盘'),
    ('Lenovo ThinkPad X1', '电脑办公', 10999.00, '商务旗舰笔记本'),
    ('华为 MatePad Pro', '电脑办公', 3999.00, '华为旗舰平板'),
    ('微软 Surface Pro 10', '电脑办公', 8999.00, '二合一触屏笔记本'),
    # 影音娱乐（6个）
    ('Sony WH-1000XM6', '影音娱乐', 2499.00, '头戴式降噪耳机'),
    ('AirPods Pro 3', '影音娱乐', 1799.00, '苹果主动降噪耳机'),
    ('Bose QC Ultra', '影音娱乐', 3299.00, 'Bose旗舰降噪耳机'),
    ('JBL Charge 6', '影音娱乐', 1299.00, '便携蓝牙音箱'),
    ('Marshall Emberton III', '影音娱乐', 1499.00, '复古便携蓝牙音箱'),
    ('索尼 PS5光盘版', '影音娱乐', 3999.00, '次世代游戏主机'),
    # 服饰鞋包（7个）
    ('纯棉圆领T恤', '服饰鞋包', 129.00, '新疆长绒棉，舒适透气'),
    ('李宁运动跑鞋', '服饰鞋包', 499.00, '轻便缓震，透气网面'),
    ('商务双肩包', '服饰鞋包', 299.00, '防泼水，40L大容量'),
    ('Levis 501牛仔裤', '服饰鞋包', 699.00, '经典美式牛仔裤'),
    ('优衣库轻薄羽绒服', '服饰鞋包', 599.00, 'ULTRALIGHT DOWN，轻暖便携'),
    ('NIKE加绒连帽卫衣', '服饰鞋包', 399.00, '宽松版型，纯棉内里加绒'),
    ('阿迪达斯运动长裤', '服饰鞋包', 349.00, '透气速干，弹力面料'),
    # 图书教育（6个）
    ('Python编程：从入门到实践', '图书教育', 89.00, '零基础学Python畅销书'),
    ('算法导论（第4版）', '图书教育', 128.00, 'MIT经典算法教材'),
    ('深入浅出数据分析', '图书教育', 79.00, '数据分析入门经典'),
    ('考研英语词汇闪过', '图书教育', 49.00, '高频词汇速记'),
    ('三体全集（全三册）', '图书教育', 93.00, '刘慈欣科幻巨著'),
    ('牛津高阶英汉双解词典', '图书教育', 169.00, '第10版，语言学习必备'),
    # 美妆个护（5个）
    ('兰蔻小黑瓶精华50ml', '美妆个护', 1080.00, '肌底精华液，修护抗老'),
    ('雅诗兰黛DW持妆粉底液', '美妆个护', 420.00, '持妆控油，遮瑕不假面'),
    ('戴森Airwrap造型器', '美妆个护', 3999.00, '多功能造型，不伤发'),
    ('SK-II神仙水230ml', '美妆个护', 1590.00, '精华露，提亮肤色'),
    ('飞利浦电动牙刷HX9', '美妆个护', 699.00, '声波震动，2分钟智能计时'),
    # 家居生活（6个）
    ('米家台灯Pro', '家居生活', 349.00, '智能调光Ra95，护眼台灯'),
    ('膳魔师保温杯500ml', '家居生活', 269.00, '不锈钢真空保温12小时'),
    ('极米无屏电视Z6X', '家居生活', 2999.00, '家用投影仪，1080P分辨率'),
    ('小米空气净化器4 Pro', '家居生活', 1999.00, '除甲醛除菌，60㎡适用'),
    ('网易严选天然乳胶枕', '家居生活', 199.00, '天然乳胶，人体工学设计'),
    ('九阳破壁机Y1', '家居生活', 899.00, '免滤无渣，一键自清洗'),
    # 食品饮料（4个）
    ('三顿半精品超即溶咖啡', '食品饮料', 189.00, '冷萃速溶，24颗装'),
    ('良品铺子每日坚果大礼包', '食品饮料', 168.00, '7种坚果，10包装'),
    ('伊利安慕希原味酸奶', '食品饮料', 69.00, '原味酸奶205g×12盒'),
    ('农夫山泉矿泉水24瓶', '食品饮料', 36.00, '天然水源，550ml×24瓶'),
    # 运动户外（4个）
    ('探路者三合一冲锋衣', '运动户外', 899.00, '防风防水，可拆卸内胆'),
    ('迪卡侬加厚瑜伽垫', '运动户外', 129.00, '10mm加厚防滑，NBR材质'),
    ('小米手环8 Pro', '运动户外', 399.00, '150+运动模式，独立GPS'),
    ('Wilson碳素网球拍', '运动户外', 599.00, '专业碳纤维，减震手柄'),
]

order_statuses = ['待付款', '已付款', '已发货', '已完成', '已取消']
phone_prefixes = ['138','139','156','186','177','136','158','189','176','152','133','185','159','137','150']
address_pool = [
    '北京市朝阳区望京SOHO 3座1206', '上海市浦东新区张江高科技园区',
    '广东省深圳市南山区科技园南路', '浙江省杭州市余杭区阿里巴巴西溪园区',
    '四川省成都市高新区天府软件园', '江苏省南京市鼓楼区新模范马路',
    '湖北省武汉市洪山区光谷大道', '广东省广州市天河区珠江新城',
    '陕西省西安市雁塔区高新路', '湖南省长沙市岳麓区大学城',
    '山东省济南市历下区泉城路', '福建省厦门市思明区软件园二期',
    '重庆市江北区观音桥步行街', '天津市和平区南京路',
    '河南省郑州市金水区花园路', '安徽省合肥市蜀山区黄山路',
    '辽宁省大连市沙河口区软件园', '广西南宁市青秀区民族大道',
    '贵州省贵阳市云岩区中华路', '云南省昆明市盘龙区北京路',
]

# ---------- 4. 清空旧数据 ----------
for t in ['order_items', 'orders', 'products', 'users', 'staff', 'role_permissions', 'permissions', 'roles']:
    cursor.execute(f'DELETE FROM {t}')
    cursor.execute(f'ALTER TABLE {t} AUTO_INCREMENT = 1')
conn.commit()
print('旧数据已清空')

# ---------- 5. 插入角色 ----------
role_names = ['admin', 'operator', 'customer_service', 'warehouse']
role_ids = {}
for rn in role_names:
    cursor.execute('INSERT INTO roles (role_name) VALUES (%s)', (rn,))
    role_ids[rn] = cursor.lastrowid
conn.commit()
print(f'已插入 {len(role_ids)} 个角色')

# ---------- 6. 插入权限 ----------
permission_list = [
    ('view_products', '查看商品'), ('edit_products', '修改商品信息'), ('delete_products', '删除商品'),
    ('edit_inventory', '修改库存'), ('view_orders', '查看订单'), ('edit_orders', '修改订单'),
    ('delete_orders', '删除订单'), ('view_users', '查看用户'), ('edit_users', '修改用户信息'),
    ('view_analytics', '查看销售数据'), ('manage_roles', '管理角色权限'),
]
perm_ids = {}
for code, desc in permission_list:
    cursor.execute('INSERT INTO permissions (permission_name, description) VALUES (%s, %s)', (code, desc))
    perm_ids[code] = cursor.lastrowid
conn.commit()
print(f'已插入 {len(perm_ids)} 个权限')

# ---------- 7. 分配角色权限 ----------
role_perm_map = {
    'admin':            ['view_products','edit_products','delete_products','edit_inventory',
                         'view_orders','edit_orders','delete_orders',
                         'view_users','edit_users','view_analytics','manage_roles'],
    'operator':         ['view_products','edit_products','delete_products','edit_inventory',
                         'view_users','view_analytics'],
    'customer_service': ['view_products','view_orders','edit_orders','view_users','edit_users'],
    'warehouse':        ['view_products','view_orders','edit_orders'],
}
rp_count = 0
for rn, perms in role_perm_map.items():
    for pc in perms:
        cursor.execute('INSERT INTO role_permissions (role_id, permission_id) VALUES (%s, %s)',
                       (role_ids[rn], perm_ids[pc]))
        rp_count += 1
conn.commit()
print(f'已插入 {rp_count} 条角色权限映射')

# ---------- 8. 插入工作人员（10 人） ----------
staff_config = [
    ('系统管理员', 'admin'),
    ('张建国', 'operator'), ('李志强', 'operator'), ('王秀英', 'operator'),
    ('赵玉梅', 'customer_service'), ('刘明辉', 'customer_service'), ('陈海龙', 'customer_service'),
    ('杨晓峰', 'warehouse'), ('黄永刚', 'warehouse'), ('周丽华', 'warehouse'),
]
for sname, srole in staff_config:
    pwd = 'admin123' if srole == 'admin' else '123456'
    cursor.execute('INSERT INTO staff (staff_name, role_id, login_password) VALUES (%s, %s, %s)',
                   (sname, role_ids[srole], pwd))
conn.commit()
print(f'已插入 {len(staff_config)} 个工作人员')

# ---------- 9. 插入顾客（200 人） ----------
user_ids = []
for i in range(200):
    name = random.choice(surnames) + random.choice(given_names)
    phone = random.choice(phone_prefixes) + ''.join(str(random.randint(0, 9)) for _ in range(8))
    addr = random.choice(address_pool)
    level = random.choices([0,1,2,3], weights=[30,35,25,10], k=1)[0]
    cursor.execute(
        'INSERT INTO users (user_name, phone_num, address, user_level) VALUES (%s, %s, %s, %s)',
        (name, phone, addr, level)
    )
    user_ids.append(cursor.lastrowid)
conn.commit()
print(f'已插入 {len(user_ids)} 个顾客')

# ---------- 10. 插入商品（52 个，库存依据品类和价格差异化） ----------
product_ids = []
for name, cat, price, desc in product_pool:
    # 高价商品库存少，低价商品库存多
    if price > 5000:
        inv = random.randint(20, 150)
    elif price > 1000:
        inv = random.randint(80, 400)
    else:
        inv = random.randint(200, 800)
    adj_price = round(price * random.uniform(0.93, 1.07), 2)
    cursor.execute(
        'INSERT INTO products (product_name, category, price, inventory, description) VALUES (%s, %s, %s, %s, %s)',
        (name, cat, adj_price, inv, desc)
    )
    product_ids.append(cursor.lastrowid)
conn.commit()
print(f'已插入 {len(product_ids)} 个商品')

# ---------- 11. 插入订单 & 明细（~1000 单，跨 6 个月 2025-01~2025-06） ----------
base_date = datetime(2025, 1, 1)
buyer_ids = random.sample(user_ids, 185)   # 200人中 185 人下单（92.5%）
order_count = 0
item_count = 0

# 预先准备 2000 个随机时间点
rand_timestamps = []
for _ in range(2000):
    d = random.randint(0, 179)
    s = random.randint(0, 86399)
    rand_timestamps.append(base_date + timedelta(days=d, seconds=s))

ts_iter = iter(rand_timestamps)

for uid in buyer_ids:
    # 每人 2~15 单，分布偏中高频
    num_orders = random.choices([2,3,4,5,6,7,8,10,12,15],
                                weights=[8,12,18,20,15,10,8,5,3,1], k=1)[0]
    for _ in range(num_orders):
        order_time = next(ts_iter)
        status = random.choice(order_statuses)
        cursor.execute(
            'INSERT INTO orders (user_id, order_date, order_status, total_amount) VALUES (%s, %s, %s, 0)',
            (uid, order_time, status)
        )
        oid = cursor.lastrowid

        n_items = random.randint(1, 5)
        chosen = random.choices(product_ids, k=n_items)
        grouped = {}
        for pid in chosen:
            grouped[pid] = grouped.get(pid, 0) + random.randint(1, 3)

        total = 0.0
        for pid, qty in grouped.items():
            cursor.execute('SELECT price FROM products WHERE product_id = %s', (pid,))
            cur_price = float(cursor.fetchone()[0])
            snap = round(cur_price * random.uniform(0.88, 1.12), 2)
            cursor.execute(
                'INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (%s, %s, %s, %s)',
                (oid, pid, qty, snap)
            )
            total += snap * qty
            item_count += 1

        cursor.execute('UPDATE orders SET total_amount = %s WHERE order_id = %s',
                       (round(total, 2), oid))
        order_count += 1
        if order_count >= 1050:  # 上限保护
            break
    if order_count >= 1050:
        break

conn.commit()
print(f'已插入 {order_count} 个订单，{item_count} 条订单明细')

# ---------- 12. 验证 ----------
for tbl in ['roles','permissions','role_permissions','staff','users','products','orders','order_items']:
    cursor.execute(f'SELECT COUNT(*) FROM {tbl}')
    print(f'  {tbl}: {cursor.fetchone()[0]} 行')

cursor.execute('''
    SELECT r.role_name, COUNT(*) as cnt FROM staff s
    JOIN roles r ON s.role_id = r.role_id GROUP BY r.role_name
''')
print('工作人员角色分布:')
for row in cursor.fetchall():
    print(f'  {row[0]}: {row[1]} 人')

# 订单状态分布
cursor.execute('SELECT order_status, COUNT(*) FROM orders GROUP BY order_status')
print('订单状态分布:')
for row in cursor.fetchall():
    print(f'  {row[0]}: {row[1]} 单')

# 品类分布
cursor.execute('SELECT category, COUNT(*) FROM products GROUP BY category ORDER BY COUNT(*) DESC')
print('商品品类分布:')
for row in cursor.fetchall():
    print(f'  {row[0]}: {row[1]} 个')

cursor.close()
conn.close()
print('\n脚本执行完毕，连接已关闭')
