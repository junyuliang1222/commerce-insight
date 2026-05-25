use `SPD_26.5`;

-- ========================================
-- users 表规则（4条）
-- ========================================

INSERT INTO quality_rules (rule_name, target_table, target_column, rule_type, rule_config, severity, description)
VALUES ('用户姓名不能为空', 'users', 'user_name', 'not_null', '{}', 'critical', 'user_name 列不允许 NULL');

INSERT INTO quality_rules (rule_name, target_table, target_column, rule_type, rule_config, severity, description)
VALUES ('手机号不能为空', 'users', 'phone_num', 'not_null', '{}', 'critical', 'phone_num 列不允许 NULL');

INSERT INTO quality_rules (rule_name, target_table, target_column, rule_type, rule_config, severity, description)
VALUES ('手机号格式校验', 'users', 'phone_num', 'pattern_match', '{"pattern": "^1[3-9]\\\\d{9}$"}', 'warning', '手机号应为 11 位数字，以 1 开头，第二位 3-9');

INSERT INTO quality_rules (rule_name, target_table, target_column, rule_type, rule_config, severity, description)
VALUES ('会员等级在有效范围内', 'users', 'user_level', 'value_in_set', '{"values": [0, 1, 2, 3]}', 'critical', 'user_level 只能为 0(普通) 1(银卡) 2(金卡) 3(钻石)');

-- ========================================
-- products 表规则（4条）
-- ========================================

INSERT INTO quality_rules (rule_name, target_table, target_column, rule_type, rule_config, severity, description)
VALUES ('商品名称不能为空', 'products', 'product_name', 'not_null', '{}', 'critical', 'product_name 列不允许 NULL');

INSERT INTO quality_rules (rule_name, target_table, target_column, rule_type, rule_config, severity, description)
VALUES ('商品价格必须大于0', 'products', 'price', 'value_range', '{"min": 0.01}', 'critical', 'price 必须为正数');

INSERT INTO quality_rules (rule_name, target_table, target_column, rule_type, rule_config, severity, description)
VALUES ('库存不能为负数', 'products', 'inventory', 'value_range', '{"min": 0}', 'critical', 'inventory 必须 >= 0');

INSERT INTO quality_rules (rule_name, target_table, target_column, rule_type, rule_config, severity, description)
VALUES ('品类必须在已知范围内', 'products', 'category', 'value_in_set', '{"values": ["手机数码", "电脑办公", "影音娱乐", "服饰鞋包", "图书教育", "美妆个护", "家居生活", "食品饮料", "运动户外"]}', 'warning', 'category 必须是 10 个已知品类之一');

-- ========================================
-- orders 表规则（4条）
-- ========================================

INSERT INTO quality_rules (rule_name, target_table, target_column, rule_type, rule_config, severity, description)
VALUES ('订单状态必须在5种状态内', 'orders', 'order_status', 'value_in_set', '{"values": ["待付款", "已付款", "已发货", "已完成", "已取消"]}', 'critical', 'order_status 只能是 5 种预定义状态之一');

INSERT INTO quality_rules (rule_name, target_table, target_column, rule_type, rule_config, severity, description)
VALUES ('订单金额必须大于0', 'orders', 'total_amount', 'value_range', '{"min": 0.01}', 'critical', 'total_amount 必须为正数');

INSERT INTO quality_rules (rule_name, target_table, target_column, rule_type, rule_config, severity, description)
VALUES ('订单用户必须存在', 'orders', 'user_id', 'referential_integrity', '{"parent_table": "users", "parent_column": "user_id"}', 'critical', 'orders.user_id 必须在 users 表中存在');

INSERT INTO quality_rules (rule_name, target_table, target_column, rule_type, rule_config, severity, description)
VALUES ('订单金额与明细汇总一致', 'orders', NULL, 'business_logic', '{"check_sql": "SELECT o.order_id FROM orders o JOIN order_items oi ON o.order_id = oi.order_id GROUP BY o.order_id HAVING ABS(o.total_amount - SUM(oi.unit_price * oi.quantity)) > 0.01"}', 'critical', 'orders.total_amount 应等于其 order_items 金额汇总');

-- ========================================
-- order_items 表规则（4条）
-- ========================================

INSERT INTO quality_rules (rule_name, target_table, target_column, rule_type, rule_config, severity, description)
VALUES ('购买数量必须大于0', 'order_items', 'quantity', 'value_range', '{"min": 1}', 'critical', 'quantity 必须 >= 1');

INSERT INTO quality_rules (rule_name, target_table, target_column, rule_type, rule_config, severity, description)
VALUES ('明细单价必须大于0', 'order_items', 'unit_price', 'value_range', '{"min": 0.01}', 'critical', 'unit_price 必须为正数');

INSERT INTO quality_rules (rule_name, target_table, target_column, rule_type, rule_config, severity, description)
VALUES ('明细商品必须存在', 'order_items', 'product_id', 'referential_integrity', '{"parent_table": "products", "parent_column": "product_id"}', 'critical', 'order_items.product_id 必须在 products 表中存在');

INSERT INTO quality_rules (rule_name, target_table, target_column, rule_type, rule_config, severity, description)
VALUES ('明细订单必须存在', 'order_items', 'order_id', 'referential_integrity', '{"parent_table": "orders", "parent_column": "order_id"}', 'critical', 'order_items.order_id 必须在 orders 表中存在');
