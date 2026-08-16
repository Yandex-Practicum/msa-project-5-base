CREATE SCHEMA IF NOT EXISTS shop;

CREATE TABLE shop.orders (
    id          INTEGER PRIMARY KEY,
    customer_id INTEGER        NOT NULL,
    amount      NUMERIC(10, 2) NOT NULL,
    status      TEXT           NOT NULL
);

INSERT INTO shop.orders (id, customer_id, amount, status) VALUES
    (1, 101, 1500.00, 'paid'),
    (2, 102,  420.50, 'paid'),
    (3, 103,  890.00, 'pending'),
    (4, 104,  220.00, 'paid'),
    (5, 105, 3100.75, 'paid');
