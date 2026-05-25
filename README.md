# CommerceInsight — 电商智能洞察平台

一个模拟企业级电商后台的**全栈数据分析平台**，涵盖数据库设计、RBAC 权限管理、Flask Web 后台、ECharts 可视化分析、以及 15 张业务报表查询。

**技术栈**：MySQL 9.3 + Python 3.13 + Flask + pymysql + ECharts 5.5

---

## 项目速览

| 模块 | 内容 |
|------|------|
| 数据库 | 8 张表（4 张 RBAC + 4 张业务），完整外键约束，DECIMAL 精确金额 |
| 测试数据 | 200 用户 / 52 商品 / 1000+ 订单 / 3000+ 明细，跨 6 个月 |
| 权限模型 | 4 角色 × 11 权限，前后端双重 RBAC 控制 |
| 管理后台 | 首页看板、用户管理、商品管理、订单管理 |
| 分析看板 | 4 张 ECharts 交互图表（趋势 / 品类 / 用户分层 / 归因分析） |
| 业务报表 | 15 张动态报表，支持参数化查询，覆盖运营/客服/采购/财务日常数据需求 |

---

## 快速启动

```bash
git clone <your-repo-url>
cd sql_project/SPD_26.5
conda create -n sql-project python=3.13
conda activate sql-project
pip install pymysql flask

# 设置 MySQL 密码
export DB_PASSWORD='your-password'

# 初始化数据库（在 MySQL 中执行 SPD_schema.sql）
# 生成测试数据
python insert_data.py

# 启动
python app.py
# 浏览器打开 http://127.0.0.1:5000/login
```

演示账号：`系统管理员` / `admin123`

---

## 数据库设计

```
roles ──1:N── staff ──1:N── role_permissions ──N:1── permissions
users ──1:N── orders ──1:N── order_items ──N:1── products
```

### 关键设计决策

- **orders / order_items 拆分** — 符合第三范式，避免公共字段冗余
- **unit_price 快照存储** — 商品调价后历史订单金额不受影响
- **金额统一 DECIMAL(10,2)** — 避免浮点精度丢失
- **order_items 联合主键 (order_id, product_id)** — 同一订单不能有重复商品

---

## 业务报表

平台内置 15 张业务报表，源于运营、采购、客服、财务等部门的真实数据需求，技术实现覆盖多层 SQL 能力：

| 业务场景 | 报表 | SQL 技术点 |
|----------|------|-----------|
| 运营 — 会员营销 | 钻石会员列表、高价值用户 Top 20% | WHERE 过滤、NTILE(5) 分桶 |
| 采购 — 库存管理 | 库存预警商品、品类商品统计、动销率 | GROUP BY 聚合、标量子查询 |
| 客服 — 订单分析 | 已取消订单查询、用户消费全景 | JOIN 关联、LEFT JOIN、VIEW |
| 运营 — 用户洞察 | 用户下单排名、用户客单价、交叉品类用户 | RANK() 排名、EXISTS 子查询 |
| 运营 — 商品运营 | 品类销量冠军 | RANK() OVER(PARTITION BY) |
| 财务 — 销售监控 | 每日销售额、月度环比增长率 | GROUP BY、LAG() 窗口函数 |
| 财务 — 订单明细 | 订单明细金额占比 | SUM() OVER(PARTITION BY) |
| 运营 — 用户粘性 | 复购率 | HAVING + 标量子查询 |

---

## 页面展示

| 页面 | 路由 | 功能 |
|------|------|------|
| 登录 | `/login` | 角色登录，按权限分配菜单 |
| 首页看板 | `/` | 用户数/商品数/订单数/销售额 统计卡片 |
| 用户管理 | `/users` | 200 位顾客列表 |
| 商品管理 | `/products` | 商品编辑 + 库存修改 |
| 订单管理 | `/orders` | 订单列表 + 状态修改 |
| 销售分析 | `/analytics` | 4 张 ECharts 分析图表 |
| 业务报表 | `/reports` | 15 张动态 SQL 报表 |
