# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 与用户的协作方式（最重要）

**用户自己写所有代码。** 除非用户明确要求，否则不要直接写代码、编辑文件或创建 commit。你的职责是：
- 引导思路、审查代码、解释概念——指出问题、建议方案、用提问引导用户自己解决
- 当用户明确把前端/模板工作交给你时，可以代为完成（用户最关注的是数据库 + Python）
- 提供架构建议和上下文，但不直接实现

用户使用 IntelliJ IDEA + JetBrains MCP 插件进行开发。

**语言规则**：始终使用中文回复，但专业术语（如 SQL、LAG、JOIN、PRIMARY KEY、ECharts 等）保留英文。

---

## 项目概述

一个**电商数据分析平台**，用于数据分析/数据科学实习面试的作品集项目。包含完整的数据库设计、RBAC 权限模型、Flask Web 管理后台、随机测试数据生成脚本、以及 15 道递进式 SQL 分析题。

**技术栈**：MySQL 9.3 + Python 3.13 + Flask + pymysql + ECharts

---

## 常用命令

```bash
# 启动 Flask 开发服务器
cd /Users/junyuliang/Desktop/sql_project/SPD_26.5
conda activate sql-project
export DB_PASSWORD='your-password'
python app.py
# 浏览器打开 http://127.0.0.1:5000/login

# 重新生成测试数据（清空全部数据并重新插入）
export DB_PASSWORD='your-password'
python insert_data.py
```

---

## MySQL 连接信息

| 项目 | 值 |
|------|-----|
| Host | localhost |
| Port | 3306 |
| User | root |
| Password | 通过环境变量 `DB_PASSWORD` 设置 |
| Database | `SPD_26.5` |

---

## 数据库设计

### ER 图

```
                    ┌────────────────┐
                    │     roles      │
                    │ role_id PK     │
                    │ role_name      │
                    └───┬────────────┘
                        │ 1:N
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
   ┌──────────┐  ┌──────────┐  ┌──────────────┐
   │  staff   │  │role_perm │  │ permissions  │
   │staff_id  │  │(role_id, │  │permission_id │
   │staff_name│  │ perm_id) │  │perm_name     │
   │role_id FK│  └──────────┘  │description   │
   │login_pwd │                └──────────────┘
   └──────────┘

   ┌──────────┐      ┌──────────┐      ┌──────────────┐
   │  users   │ 1:N  │  orders  │ 1:N  │ order_items  │
   │user_id PK│◄─────│user_id FK│◄─────│PK(order_id,  │
   │user_name │      │order_date│      │  product_id) │
   │phone_num │      │status    │      │quantity      │
   │address   │      │total_amt │      │unit_price    │
   │level     │      └──────────┘      └──┬───────────┘
   │created_at│                          │ N:1
   └──────────┘                          ▼
                                  ┌──────────┐
                                  │ products │
                                  │product_id│
                                  │name,cat  │
                                  │price,inv │
                                  │descr,ts  │
                                  └──────────┘
```

**8 张表分为两组**：

| 分组 | 表 | 用途 |
|------|-----|------|
| RBAC 权限体系 | `roles`, `permissions`, `role_permissions`, `staff` | 工作人员登录 + 按角色控制菜单可见性 |
| 业务数据 | `users`, `products`, `orders`, `order_items` | 顾客、商品、订单、订单明细 |

### 核心设计决策与理由

| 决策 | 理由 |
|------|------|
| staff 与 users 分表 | 工作人员和顾客字段完全不同（staff 有 role_id 和 login_password，users 纯顾客属性），混在一起语义混乱 |
| orders 与 order_items 拆分 | 避免公共字段（下单时间、状态、地址）冗余和更新异常，符合数据库范式 |
| order_items 联合主键 `(order_id, product_id)` | 同一订单不能有两条同一商品的记录 |
| `unit_price` 快照存储 | 商品调价后历史订单金额不受影响，保证对账准确。测试数据中快照价故意 ±12% 偏离当前价来模拟调价场景 |
| total_amount 冗余在 orders | 查订单总额避免每次聚合计算，以空间换时间 |
| 金额用 `DECIMAL(10,2)` | 避免 FLOAT/DOUBLE 精度丢失 |
| 手机号用 `VARCHAR(20)` | 号码不是用来计算的，且座机可能以 0 开头 |
| 外键约束 | 保证引用完整性，防止孤儿记录 |
| 密码明文存储 | 当前简化版，生产应改为 bcrypt 哈希 |

### orders 表 order_status 枚举

5 种状态：`待付款`、`已付款`、`已发货`、`已完成`、`已取消`

---

## RBAC 权限模型

4 种角色 × 11 个权限，通过 `role_permissions` 中间表实现多对多：

| 权限 | admin | 运营(operator) | 客服(customer_service) | 仓库(warehouse) |
|------|:-----:|:----:|:----:|:----:|
| 查看/修改/删除商品 | ✓ | ✓ | ✓(看) | ✓(看) |
| 修改库存 | ✓ | ✓ | ✗ | ✗ |
| 查看/修改/删除订单 | ✓ | ✗ | ✓ | ✓(改状态) |
| 查看/修改用户 | ✓ | ✗ | ✓ | ✗ |
| 查看销售数据 | ✓ | ✓ | ✗ | ✗ |
| 管理角色权限 | ✓ | ✗ | ✗ | ✗ |

**权限执行流程**：用户登录（查 staff 表）→ 根据 role_id 查 role_permissions → 前端 `base.html` 根据 perms 列表渲染菜单，后端用装饰器 `@require_permission` 拦截无权限请求。

### 登录账号

| 用户名 | 密码 | 角色 | 可见菜单 |
|--------|------|------|------|
| 系统管理员 | `admin123` | admin | 首页+用户+商品+订单 |
| 张建国/李志强/王秀英 | `123456` | 运营 | 首页+商品 |
| 赵玉梅/刘明辉/陈海龙 | `123456` | 客服 | 首页+用户+订单 |
| 杨晓峰/黄永刚/周丽华 | `123456` | 仓库 | 首页+商品+订单 |

---

## 测试数据规模

| 表 | 行数 | 说明 |
|----|------|------|
| roles | 4 | admin, operator, customer_service, warehouse |
| permissions | 11 | 查看/编辑/删除商品、订单、用户等 |
| role_permissions | 25 | 4 角色 × 不同权限组合 |
| staff | 10 | 1 admin + 3 运营 + 3 客服 + 3 仓库 |
| users | 200 | 顾客，会员等级按 30:35:25:10 分布（0普通/1银卡/2金卡/3钻石） |
| products | 52 | 10 个品类，高价商品库存低、低价商品库存高 |
| orders | ~1021 | 跨 6 个月（2025-01~2025-06），5 种状态均匀分布 |
| order_items | ~3064 | 平均每单约 3 个商品 |

### 10 个品类

手机数码(7)、电脑办公(7)、影音娱乐(6)、服饰鞋包(7)、图书教育(6)、美妆个护(5)、家居生活(6)、食品饮料(4)、运动户外(4)

---

## Flask Web 应用

### 文件结构

```
sql_project/
├── CLAUDE.md                   # 本文件（项目根目录）
└── SPD_26.5/                   # 所有项目源码在此子目录下
    ├── SPD_schema.sql          # 8 张表的完整建表语句
    ├── insert_data.py          # 随机测试数据生成脚本（按外键依赖顺序插入）
    ├── analysis.sql            # 15 道 SQL 分析题（全部完成）
    ├── app.py                  # Flask Web 后台
    ├── PROJECT_SUMMARY.md      # 项目详细文档
    └── templates/
        ├── base.html           # 侧边栏框架（按角色渲染菜单，内置 CSS）
        ├── login.html          # 登录页
        ├── dashboard.html      # 首页看板（4 个统计卡片）
        ├── users.html          # 用户列表（200 位顾客）
        ├── products.html       # 商品管理（弹窗编辑+改库存）
        ├── orders.html         # 订单管理（弹窗改状态）
        └── analytics.html      # 销售分析（4 张 ECharts 图表）
```

### 已实现的路由

| 页面 | 路由 | 方法 | 权限要求 | 功能 |
|------|------|------|------|------|
| 登录 | `/login` | GET/POST | 无 | 用户名+密码验证，查 staff 表 |
| 退出 | `/logout` | GET | 无 | 清除 session |
| 看板 | `/` | GET | 登录 | 4 张统计卡（用户数/商品数/订单数/有效销售额） |
| 用户管理 | `/users` | GET | `view_users` | 顾客列表（ID、姓名、手机、地址、等级、注册时间） |
| 商品管理 | `/products` | GET | `view_products` | 商品列表 + 弹窗编辑 + 弹窗改库存 |
| 更新商品 | `/products/update` | POST | `edit_products` | 修改名称/品类/价格/描述 |
| 更新库存 | `/products/inventory` | POST | `edit_inventory` | 修改库存量 |
| 订单管理 | `/orders` | GET | `view_orders` | 订单列表（关联 users 显示用户名） |
| 改订单状态 | `/orders/status` | POST | `edit_orders` | 改订单状态（5 种可选） |
| 销售分析 | `/analytics` | GET | `view_analytics` | 4 张分析图表（趋势/品类/用户分层/归因） |
| 销售趋势 API | `/api/sales-trend` | GET | `view_analytics` | 按月销售额 + 环比增长率（LAG） |
| 品类分析 API | `/api/category-analysis` | GET | `view_analytics` | 品类销售额排行 + 占比 |
| 用户分层 API | `/api/user-segmentation` | GET | `view_analytics` | 按消费额分段（CASE WHEN） |
| 归因分析 API | `/api/attribution` | GET | `view_analytics` | 连环替代法量价拆解 |

### 认证与权限机制

- **`@login_required`**：检查 `session['staff_id']` 是否存在，不存在则重定向到 `/login`
- **`@require_permission('xxx')`**：查 `role_permissions` 表确认当前用户角色是否拥有该权限，无权限返回 403
- **前端渲染**：`base.html` 侧边栏用 `{% if 'view_users' in perms %}` 按权限显示/隐藏菜单项
- **Session 存储**：`staff_id`、`role_id`、`user_name`

### app.py 关键函数

- `get_db()` — 获取 pymysql 连接
- `get_staff_permissions(staff_id)` — 查某个工作人员的权限列表（通过 role_permissions JOIN）
- `@login_required` / `@require_permission(perm_name)` — 两个装饰器

---

## analysis.sql — 15 道 SQL 分析题（全部完成）

| 题号 | 难度 | 内容 | 考察点 |
|------|------|------|--------|
| 1 | 基础 | 查钻石会员 | WHERE 单表过滤 |
| 2 | 基础 | 低库存商品 | WHERE + 数值比较 |
| 3 | 基础 | 已取消订单+下单人 | 两表关联（LEFT JOIN） |
| 4 | 聚合 | 品类均价 | GROUP BY + 聚合 |
| 5 | 聚合 | 用户下单排名 | LEFT JOIN + GROUP BY + RANK() |
| 6 | 聚合 | 每日销售额 | GROUP BY + SUM |
| 7 | 窗口函数 | 明细占订单比例 | SUM() OVER(PARTITION BY) |
| 8 | 聚合 | 客单价 | WHERE 排除已取消 + GROUP BY |
| 9 | 子查询 | 交叉品类用户 | 两个 EXISTS 子查询取交集 |
| 10 | 窗口函数 | 每个品类销量最高商品 | RANK() OVER(PARTITION BY) + 子查询 |
| 11 | 子查询 | 动销率 | 标量子查询 + COUNT(DISTINCT) |
| 12 | 窗口函数 | 高价值用户前 20% | NTILE(5) 分桶 |
| 13 | 窗口函数 | 每月环比增长率 | LAG() + 子查询 |
| 14 | 聚合 | 复购率 | HAVING COUNT ≥ 2 + 标量子查询 |
| 15 | 综合 | 用户消费全景视图 | LEFT JOIN + 多表聚合 + CREATE VIEW |

---

## 当前项目状态与待办

### 已完成
- 数据库 8 张表设计与建表
- 测试数据生成脚本（insert_data.py）
- Flask 后台管理（登录、看板、用户/商品/订单 CRUD）
- RBAC 权限（前后端双重控制）
- 分析功能扩展（4 张 ECharts 图表 + `/analytics` 页面）
- analysis.sql 全部 15 题

### 远期计划
- **数据质量监控平台**（第二个独立项目）
