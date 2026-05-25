# 电商数据分析平台 — 项目总结

## 一句话概括

一个模拟电商后台的**数据分析全栈项目**：从数据库设计 → 测试数据生成 → RBAC 权限后台 → ECharts 可视化分析 → 15 道递进式 SQL 分析题，覆盖数据分析岗位面试全部硬技能考点。

**技术栈**：MySQL 9.3 + Python 3.13 + Flask + pymysql + ECharts 5.5

---

## 做了什么

| 模块 | 产出 | 展示能力 |
|------|------|----------|
| 数据库设计 | 8 张表，完整 ER 模型 + 建表语句 | 范式设计、外键约束、字段类型选型 |
| 测试数据 | 200 用户 / 52 商品 / 1000+ 订单 / 3000+ 明细，跨 6 个月 | Python 数据生成、模拟真实业务场景 |
| RBAC 权限 | 4 角色 × 11 权限，前后端双重控制 | 后端装饰器 + 前端按权限渲染菜单 |
| SQL 分析 | 15 道递进式分析题 | 窗口函数（RANK/NTILE/LAG）、子查询、EXISTS、VIEW |
| 可视化分析 | 4 张 ECharts 图表 | 销售趋势、品类分析、用户分层、连环替代法归因 |
| Flask 后台 | 7 个页面 + 5 个 API | Web 应用开发基础 |

---

## 数据规模

| 表 | 行数 |
|----|------|
| users（顾客） | 200 |
| products（商品） | 52（10 个品类） |
| orders（订单） | ~1021（跨 6 个月，5 种状态） |
| order_items（明细） | ~3064（平均每单 3 件） |
| staff（工作人员） | 10（4 种角色） |

---

## 数据库设计（核心亮点）

### ER 图

```
roles ──1:N── staff ──1:N── role_permissions ──N:1── permissions

users ──1:N── orders ──1:N── order_items ──N:1── products
```

### 关键设计决策（面试可展开讲）

| 决策 | 为什么 |
|------|--------|
| staff 与 users 分表 | 工作人员（有密码、角色）和顾客（纯消费者）字段完全不同，混表语义混乱 |
| orders 与 order_items 拆分 | 一个订单多个商品，不拆分会导致下单时间/状态/地址冗余 → 更新异常 |
| `unit_price` 快照存储 | 商品价格会变动，存下单时的价格保证历史订单对账准确。测试数据故意让快照价 ±12% 偏离原价模拟调价 |
| 金额用 DECIMAL(10,2) | FLOAT/DOUBLE 有精度问题（如 0.1 + 0.2 != 0.3），DECIMAL 精确到分 |
| order_items 联合主键 `(order_id, product_id)` | 同一订单不能有两条同一商品记录 |
| total_amount 冗余在 orders | 以空间换时间，查订单总额避免每次 JOIN order_items 再 SUM |
| 外键约束 | 保证引用完整性，防止孤儿记录（如订单关联了不存在的商品） |

---

## RBAC 权限模型

4 种角色（admin / 运营 / 客服 / 仓库），通过 `role_permissions` 中间表实现多对多的权限控制。

**权限执行流程**：登录 → 查 role_permissions 取权限列表 → 后端装饰器 `@require_permission` 拦截 → 前端 Jinja2 模板按权限渲染菜单项。

---

## SQL 分析题考点覆盖（15 道）

| 难度 | 题号 | 考点 |
|------|------|------|
| 基础 | 1-3 | WHERE 过滤、JOIN 两表关联 |
| 聚合 | 4-6, 8 | GROUP BY、聚合函数、LEFT JOIN vs INNER JOIN |
| 窗口函数 | 7, 10, 12, 13 | SUM() OVER(PARTITION BY)、RANK()、NTILE(5)、LAG() |
| 子查询 | 9, 11, 14 | EXISTS、标量子查询、HAVING |
| 综合 | 15 | 多表聚合 + LEFT JOIN + CREATE VIEW |

---

## 可视化分析页（`/analytics`）

必面运营和分析岗位展示数据发现能力：

1. **销售趋势** — 柱状图 + 折线图（双 Y 轴），月度销售额 + 环比增长率（LAG）
2. **品类分析** — 横向柱状图（排行） + 饼图（占比），品类销售额拆解
3. **用户分层** — 按消费额分 5 档（CASE WHEN），柱状图 + 折线图双维度
4. **归因分析** — 连环替代法拆解销售额变动：销量效应 vs 价格效应 vs 混合效应（堆叠柱状图）

---

## 启动与演示

```bash
cd /Users/junyuliang/Desktop/sql_project/SPD_26.5
conda activate sql-project
python app.py
# 浏览器打开 http://127.0.0.1:5000/login
```

演示账号：`系统管理员` / `admin123`（拥有全部权限）

---

## 面试可聊的扩展话题

- **数据量增长怎么办**：分库分表（按 user_id 取模）、读写分离、加索引
- **密码安全**：bcrypt 哈希 + salt，但这是作品集项目所以存了明文
- **SQL 优化**：EXPLAIN 分析执行计划、覆盖索引、避免 SELECT *
- **缓存**：Redis 缓存热门商品、排行榜
- **如果业务方需要实时分析**：换 OLAP 引擎（ClickHouse / Doris），MySQL 只做 OLTP
