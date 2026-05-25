use `SPD_26.5`;

-- ========================================
-- 权限体系（工作人员+角色+权限）
-- ========================================

create table IF NOT EXISTS roles(
    role_id int AUTO_INCREMENT primary key,
    role_name varchar(30) not null unique
);

create table IF NOT EXISTS permissions(
    permission_id int AUTO_INCREMENT primary key,
    permission_name varchar(50) not null unique,
    description varchar(100)
);

create table IF NOT EXISTS role_permissions(
    role_id int,
    permission_id int,
    PRIMARY KEY (role_id, permission_id),
    FOREIGN KEY (role_id) REFERENCES roles(role_id),
    FOREIGN KEY (permission_id) REFERENCES permissions(permission_id)
);

create table IF NOT EXISTS staff(
    staff_id int AUTO_INCREMENT primary key,
    staff_name varchar(50) not null,
    role_id int not null,
    login_password varchar(50) not null default '123456',
    created_at timestamp default current_timestamp,
    FOREIGN KEY (role_id) REFERENCES roles(role_id)
);

-- ========================================
-- 业务数据（纯顾客）
-- ========================================

create table IF NOT EXISTS users(
    user_id int AUTO_INCREMENT primary key,
    user_name varchar(50) not null,
    phone_num varchar(20) not null,
    address varchar(200) not null,
    user_level int not null default 0,
    created_at timestamp default current_timestamp
);

create table IF NOT EXISTS products(
    product_id int AUTO_INCREMENT primary key,
    product_name varchar(100) not null,
    category varchar(100),
    price decimal(7, 2) not null,
    inventory int not null default 0,
    description text,
    created_at timestamp default current_timestamp
);

create table IF NOT EXISTS orders(
    order_id int AUTO_INCREMENT primary key,
    user_id int NOT NULL,
    order_date timestamp DEFAULT current_timestamp,
    order_status varchar(20) DEFAULT '未付款',
    total_amount decimal(10,2) not null,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

create table IF NOT EXISTS order_items(
    order_id int,
    product_id int,
    quantity int NOT NULL,
    unit_price decimal(7,2) NOT NULL,
    PRIMARY KEY (order_id, product_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);
