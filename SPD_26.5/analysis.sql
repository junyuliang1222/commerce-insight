
-- ========================================
-- 第一层：基础查询
-- ========================================
USE `SPD_26.5`;
-- 1. 查所有钻石会员（user_level=3）的姓名和手机号

SELECT user_name, phone_num
FROM users
where user_level = 3

-- 2. 查库存低于 100 的商品名称和库存量
SELECT product_name, inventory
FROM products
where inventory < 100

-- 3. 查「已取消」的订单的订单号、下单人姓名、下单时间
-- 提示：JOIN users 表
select
    o.order_id,
    u.user_name,
    o.order_date
from users u
left join  orders o on o.user_id = u.user_id
where o.order_status = '已取消'



-- ========================================
-- 第二层：聚合分析（GROUP BY）
-- ========================================

-- 4. 每个品类的商品数量和平均价格
SElECT
    category,
    count(*) as count,
    sum(price) / count(*) as avg_price
FROM products
GROUP BY category

-- 5. 每个用户的订单总数，按下单数量从多到少排名
-- 提示：即使没下过单的用户也需要显示吗？用什么 JOIN？
SELECT
    u.user_id,
    COUNT(o.order_id) as orders_count,
    RANK() over (ORDER BY COUNT(*) DESC ) as rankk
FROM users u
left join  orders o on u.user_id = o.user_id
GROUP BY u.user_id


-- 6. 统计每天的订单笔数和当天销售总额，按日期排序
SELECT
    COUNT(*) as day_orders,
    SUM(total_amount) as day_sales
FROM orders
GROUP BY order_date
ORDER BY order_date



-- ========================================
-- 第三层：进阶（窗口函数 / 子查询）
-- ========================================

-- 7. 列出每笔订单明细，并计算该明细行金额占所属订单总金额的百分比
-- 提示：窗口函数 SUM() OVER(PARTITION BY order_id) 或子查询
SELECT
    order_id,product_id,quantity,unit_price,
    quantity * unit_price as items_income,
    quantity * unit_price / SUM(quantity * unit_price) OVER(PARTITION BY order_id) as percent_of_total
FROM order_items

-- 8. 每个用户的「客单价」= 该用户所有订单总金额 / 订单数
-- 提示：只算已完成和已付款的订单，排除已取消
SELECT
    user_id,
    SUM(total_amount) / COUNT(*) AS kedanjia
FROM orders
WHERE order_status != '已取消'
GROUP BY user_id


-- 9. 找出「买了手机数码品类商品，又买了影音娱乐品类商品」的用户
-- 提示：子查询 + EXISTS，或者自连接
SELECT user_id
FROM users u
WHERE exists (
    SELECT *
    from orders o
    join order_items oi ON o.order_id = oi.order_id
    join products p on oi.product_id =  p.product_id
    where o.user_id = u.user_id AND category = '手机数码' and order_status != '已取消'

)
and exists(
    SELECT *
    from orders o
    join order_items oi ON o.order_id = oi.order_id
    join products p on oi.product_id = p.product_id
    where o.user_id = u.user_id AND category = '影音娱乐' and order_status != '已取消'
)





-- 10. 查询每个品类销量最高的商品
-- 提示：先用 GROUP BY 算每个商品的总销量，再用窗口函数 RANK() OVER(PARTITION BY category ORDER BY sales DESC)



select product_id,category
from (
         select
             p.product_id,
             sum(quantity) as sales, # 每个商品的总销量
             category,
             rank() over (partition by category order by sum(quantity) desc ) as rk
         from order_items oi
                  join products p on p.product_id = oi.product_id
         group by product_id,category
     ) as table2
where rk = 1




-- ========================================
-- 第四层：综合实战（多表联查 + 复杂逻辑）
-- ========================================

-- 11. 计算商品的「动销率」：有销量的商品数 / 总商品数
-- 提示：COUNT(DISTINCT 子查询)

select (select count(distinct product_id)  from order_items oi) / (select count(*) from products ) as dongxiaolv



-- 12. 找出「高价值用户」：消费总额在前 20% 的用户
-- 提示：NTILE(5) 窗口函数分 5 组，第 1 组就是前 20%
select *
from (
         select
             u.user_id,
             sum(o.total_amount) as user_total_amount,
             NTILE(5) over (order by sum(o.total_amount) desc ) as per
         from users u
         join (select *
               from orders o
               where o.order_status != '已取消') o on o.user_id = u.user_id
         group by u.user_id
     ) as new_table
where per = 1




-- 13. 计算每月环比增长率：对比当月和上月的销售总额变化
-- 提示：LAG() 窗口函数



select
    month,
    (month_amount - lats_month_amount)/ lats_month_amount as huanbizengzhang
from (
    select
        DATE_FORMAT(order_date, '%Y-%m') as 'month',
        sum(total_amount) as month_amount,
        lag(sum(total_amount)) over (order by DATE_FORMAT(order_date, '%Y-%m')) as lats_month_amount
    from orders
    WHERE order_status != '已取消'
    group by DATE_FORMAT(order_date, '%Y-%m')
    order by DATE_FORMAT(order_date, '%Y-%m')
     ) as table1





-- 14. 复购率：下过 2 单及以上的用户数 / 总下单用户数




select (select
            count(*) as fenzi # 下过 2 单及以上的用户数
        from (
                 select
                     user_id,
                     count(*) as user_order_count #每个用户的下单数
                 from orders
                 WHERE order_status != '已取消'
                 group by user_id
                 having count(*) >= 2
             ) as table1 )
        / (select count( distinct  user_id)
        from orders
        WHERE order_status != '已取消') as fugoulv




-- 15. 写一个「用户消费全景视图」：用户名、注册日期、首单日期、总消费金额、总订单数、客单价、最近一次下单日期
-- 提示：多表聚合 + JOIN，可考虑创建为 VIEW

drop view user_consumption_view;

create view user_consumption_view as

                                     select
                                         u.user_name,
                                         u.created_at,
                                         min(o.order_date) as first_order_time,
                                         COALESCE(SUM(o.total_amount), 0)as user_total_amount,
                                         COUNT(o.order_id) as total_orders_count,
                                         COALESCE(SUM(o.total_amount), 0) / NULLIF(COUNT(o.order_id), 0) AS kedanjia,
                                         max(o.order_date) as last_order_time
                                     from users u
                                     left join orders o on u.user_id = o.user_id and o.order_status != '已取消'
                                     group by u.user_id,u.user_name, u.created_at







