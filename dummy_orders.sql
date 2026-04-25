-- ══════════════════════════════════════════════════════════════
-- dummy_orders.sql — Aurus Jewels Trend Analysis Seed Data
-- Run ONCE in MySQL: source dummy_orders.sql
-- Creates: admin account + gold rate history + test customers + 15 orders
-- ══════════════════════════════════════════════════════════════

USE AurusJewels;

-- ── 1. Admin Account ──────────────────────────────────────────
-- Password: hardik1305 (bcrypt hashed)
-- After running this, log in with:
--   Email: hardikmalhotra1305@gmail.com
--   Password: hardik1305
INSERT INTO dim_customers
    (full_name, email, phone, password_hash, role,
     loyalty_tier, total_spend, is_active)
VALUES (
    'Hardik Malhotra',
    'hardikmalhotra1305@gmail.com',
    '9999999999',
    '$2b$12$K8BXQ1v1v3z5Q5Q5Q5Q5Qu5Q5Q5Q5Q5Q5Q5Q5Q5Q5Q5Q5Q5Q5Q5',
    'admin',
    'platinum',
    0.00,
    1
)
ON DUPLICATE KEY UPDATE role='admin', is_active=1;

-- NOTE: The password hash above is a placeholder.
-- Run this Python snippet ONCE to set the real password:
--
--   from core.auth import hash_password
--   from database.db import execute_write
--   execute_write(
--       "UPDATE dim_customers SET password_hash=%s WHERE email=%s",
--       (hash_password('hardik1305'), 'hardikmalhotra1305@gmail.com')
--   )
--
-- Or run this in a Python shell from your project root.


-- ── 2. Gold Rate History — Mar 2025 → Mar 2026 ───────────────
-- One record per month per metal/karat
-- Shows realistic upward trend with festive spikes

INSERT IGNORE INTO dim_gold_rates
    (metal_type, karat, rate_per_gram, effective_date, source)
VALUES
-- March 2025
('gold',   '22K', 6220.00, '2025-03-01', 'IBJA'),
('gold',   '18K', 5088.00, '2025-03-01', 'IBJA'),
('silver', '925',   82.00, '2025-03-01', 'IBJA'),
-- April 2025 (Akshaya Tritiya spike)
('gold',   '22K', 6480.00, '2025-04-01', 'IBJA'),
('gold',   '18K', 5302.00, '2025-04-01', 'IBJA'),
('silver', '925',   84.00, '2025-04-01', 'IBJA'),
-- May 2025
('gold',   '22K', 6310.00, '2025-05-01', 'IBJA'),
('gold',   '18K', 5162.00, '2025-05-01', 'IBJA'),
('silver', '925',   82.50, '2025-05-01', 'IBJA'),
-- June 2025 (monsoon low)
('gold',   '22K', 6150.00, '2025-06-01', 'IBJA'),
('gold',   '18K', 5031.00, '2025-06-01', 'IBJA'),
('silver', '925',   80.50, '2025-06-01', 'IBJA'),
-- July 2025 (monsoon low)
('gold',   '22K', 6080.00, '2025-07-01', 'IBJA'),
('gold',   '18K', 4975.00, '2025-07-01', 'IBJA'),
('silver', '925',   80.00, '2025-07-01', 'IBJA'),
-- August 2025
('gold',   '22K', 6200.00, '2025-08-01', 'IBJA'),
('gold',   '18K', 5073.00, '2025-08-01', 'IBJA'),
('silver', '925',   81.50, '2025-08-01', 'IBJA'),
-- September 2025 (pre-festive)
('gold',   '22K', 6450.00, '2025-09-01', 'IBJA'),
('gold',   '18K', 5278.00, '2025-09-01', 'IBJA'),
('silver', '925',   83.50, '2025-09-01', 'IBJA'),
-- October 2025 (Dhanteras/Diwali — big spike)
('gold',   '22K', 6820.00, '2025-10-01', 'IBJA'),
('gold',   '18K', 5580.00, '2025-10-01', 'IBJA'),
('silver', '925',   87.00, '2025-10-01', 'IBJA'),
-- November 2025 (Diwali continued + wedding season starts)
('gold',   '22K', 7150.00, '2025-11-01', 'IBJA'),
('gold',   '18K', 5850.00, '2025-11-01', 'IBJA'),
('silver', '925',   89.00, '2025-11-01', 'IBJA'),
-- December 2025 (peak wedding season)
('gold',   '22K', 7380.00, '2025-12-01', 'IBJA'),
('gold',   '18K', 6038.00, '2025-12-01', 'IBJA'),
('silver', '925',   91.00, '2025-12-01', 'IBJA'),
-- January 2026 (wedding season)
('gold',   '22K', 7540.00, '2026-01-01', 'IBJA'),
('gold',   '18K', 6169.00, '2026-01-01', 'IBJA'),
('silver', '925',   92.00, '2026-01-01', 'IBJA'),
-- February 2026
('gold',   '22K', 7690.00, '2026-02-01', 'IBJA'),
('gold',   '18K', 6292.00, '2026-02-01', 'IBJA'),
('silver', '925',   92.50, '2026-02-01', 'IBJA'),
-- March 2026
('gold',   '22K', 7850.00, '2026-03-01', 'IBJA'),
('gold',   '18K', 6422.00, '2026-03-01', 'IBJA'),
('silver', '925',   93.00, '2026-03-01', 'IBJA');


-- ── 3. Test Customers ─────────────────────────────────────────
INSERT IGNORE INTO dim_customers
    (customer_id, full_name, email, phone,
     password_hash, role, loyalty_tier, total_spend, is_active)
VALUES
(901, 'Priya Sharma',  'priya.sharma@demo.in',  '9876543210', '', 'customer', 'gold',     185000.00, 1),
(902, 'Ananya Kapoor', 'ananya.k@demo.in',       '9812345678', '', 'customer', 'silver',    72000.00, 1),
(903, 'Rohit Verma',   'rohit.v@demo.in',        '9845612345', '', 'customer', 'platinum', 580000.00, 1);


-- ── 4. Test Addresses ─────────────────────────────────────────
INSERT IGNORE INTO dim_addresses
    (address_id, customer_id, label, line1, line2,
     city, state, pincode, is_default)
VALUES
(901, 901, 'Home', '12 Shivaji Marg',   NULL, 'New Delhi',  'Delhi',       '110001', 1),
(902, 902, 'Home', '45 Marine Lines',   NULL, 'Mumbai',     'Maharashtra', '400002', 1),
(903, 903, 'Home', '8 Residency Road',  NULL, 'Bengaluru',  'Karnataka',   '560025', 1);


-- ── 5. Orders + Items ─────────────────────────────────────────
-- 15 orders spread across seasons with realistic Indian buying patterns

-- Order 1: Mar 2025 — Regular purchase
INSERT IGNORE INTO fact_orders
    (order_id, customer_id, address_id, order_date, subtotal,
     gst_amount, total_amount, status, payment_method, loyalty_discount)
VALUES (1001, 901, 901, '2025-03-14 11:30:00',
        23890.00, 1195.00, 25085.00, 'delivered', 'online', 0);
INSERT IGNORE INTO fact_order_items
    (item_id, order_id, product_id, quantity,
     weight_g, rate_per_g, making_pct, unit_price, gst_rate)
VALUES (2001, 1001, 1, 1, 3.2, 6220.00, 0.12, 23890.00, 0.05);

-- Order 2: Apr 2025 — Akshaya Tritiya
INSERT IGNORE INTO fact_orders
    (order_id, customer_id, address_id, order_date, subtotal,
     gst_amount, total_amount, status, payment_method, loyalty_discount)
VALUES (1002, 902, 902, '2025-04-30 14:20:00',
        33020.00, 1651.00, 34671.00, 'delivered', 'online', 0);
INSERT IGNORE INTO fact_order_items
    (item_id, order_id, product_id, quantity,
     weight_g, rate_per_g, making_pct, unit_price, gst_rate)
VALUES (2002, 1002, 10, 1, 4.5, 6480.00, 0.14, 33020.00, 0.05);

-- Order 3: Apr 2025 — Akshaya Tritiya (second order)
INSERT IGNORE INTO fact_orders
    (order_id, customer_id, address_id, order_date, subtotal,
     gst_amount, total_amount, status, payment_method, loyalty_discount)
VALUES (1003, 903, 903, '2025-04-30 16:45:00',
        24410.00, 1221.00, 25631.00, 'delivered', 'online', 1221.00);
INSERT IGNORE INTO fact_order_items
    (item_id, order_id, product_id, quantity,
     weight_g, rate_per_g, making_pct, unit_price, gst_rate)
VALUES (2003, 1003, 1, 1, 3.2, 6480.00, 0.12, 24410.00, 0.05);

-- Order 4: May 2025 — Regular
INSERT IGNORE INTO fact_orders
    (order_id, customer_id, address_id, order_date, subtotal,
     gst_amount, total_amount, status, payment_method, loyalty_discount)
VALUES (1004, 901, 901, '2025-05-18 10:00:00',
        14820.00, 741.00, 15561.00, 'delivered', 'cod', 0);
INSERT IGNORE INTO fact_order_items
    (item_id, order_id, product_id, quantity,
     weight_g, rate_per_g, making_pct, unit_price, gst_rate)
VALUES (2004, 1004, 20, 1, 2.0, 6310.00, 0.10, 14820.00, 0.05);

-- Order 5: Jun 2025 — Monsoon low season
INSERT IGNORE INTO fact_orders
    (order_id, customer_id, address_id, order_date, subtotal,
     gst_amount, total_amount, status, payment_method, loyalty_discount)
VALUES (1005, 902, 902, '2025-06-22 13:15:00',
        33130.00, 1657.00, 34787.00, 'delivered', 'online', 0);
INSERT IGNORE INTO fact_order_items
    (item_id, order_id, product_id, quantity,
     weight_g, rate_per_g, making_pct, unit_price, gst_rate)
VALUES (2005, 1005, 39, 1, 5.0, 6150.00, 0.08, 33130.00, 0.05);

-- Order 6: Aug 2025 — Monsoon low
INSERT IGNORE INTO fact_orders
    (order_id, customer_id, address_id, order_date, subtotal,
     gst_amount, total_amount, status, payment_method, loyalty_discount)
VALUES (1006, 903, 903, '2025-08-05 15:30:00',
        14520.00, 726.00, 15246.00, 'delivered', 'online', 726.00);
INSERT IGNORE INTO fact_order_items
    (item_id, order_id, product_id, quantity,
     weight_g, rate_per_g, making_pct, unit_price, gst_rate)
VALUES (2006, 1006, 20, 1, 2.0, 6200.00, 0.10, 14520.00, 0.05);

-- Order 7: Sep 2025 — Pre-festive buildup
INSERT IGNORE INTO fact_orders
    (order_id, customer_id, address_id, order_date, subtotal,
     gst_amount, total_amount, status, payment_method, loyalty_discount)
VALUES (1007, 901, 901, '2025-09-28 11:00:00',
        34790.00, 1740.00, 36530.00, 'delivered', 'online', 0);
INSERT IGNORE INTO fact_order_items
    (item_id, order_id, product_id, quantity,
     weight_g, rate_per_g, making_pct, unit_price, gst_rate)
VALUES (2007, 1007, 10, 1, 4.5, 6450.00, 0.14, 34790.00, 0.05);

-- Order 8: Oct 2025 — Dhanteras (peak gold buying)
INSERT IGNORE INTO fact_orders
    (order_id, customer_id, address_id, order_date, subtotal,
     gst_amount, total_amount, status, payment_method, loyalty_discount)
VALUES (1008, 902, 902, '2025-10-20 09:30:00',
        64340.00, 3217.00, 67557.00, 'delivered', 'online', 0);
INSERT IGNORE INTO fact_order_items
    (item_id, order_id, product_id, quantity,
     weight_g, rate_per_g, making_pct, unit_price, gst_rate)
VALUES (2008, 1008, 30, 1, 8.1, 6820.00, 0.18, 64340.00, 0.05);

-- Order 9: Oct 2025 — Dhanteras chain purchase
INSERT IGNORE INTO fact_orders
    (order_id, customer_id, address_id, order_date, subtotal,
     gst_amount, total_amount, status, payment_method, loyalty_discount)
VALUES (1009, 903, 903, '2025-10-20 17:00:00',
        36860.00, 1843.00, 38703.00, 'delivered', 'online', 1843.00);
INSERT IGNORE INTO fact_order_items
    (item_id, order_id, product_id, quantity,
     weight_g, rate_per_g, making_pct, unit_price, gst_rate)
VALUES (2009, 1009, 39, 1, 5.0, 6820.00, 0.08, 36860.00, 0.05);

-- Order 10: Nov 2025 — Diwali multi-item gifting
INSERT IGNORE INTO fact_orders
    (order_id, customer_id, address_id, order_date, subtotal,
     gst_amount, total_amount, status, payment_method, loyalty_discount)
VALUES (1010, 901, 901, '2025-11-03 13:45:00',
        63400.00, 3170.00, 66570.00, 'delivered', 'online', 0);
INSERT IGNORE INTO fact_order_items
    (item_id, order_id, product_id, quantity,
     weight_g, rate_per_g, making_pct, unit_price, gst_rate)
VALUES
(2010, 1010, 1,  1, 3.2, 7150.00, 0.12, 26950.00, 0.05),
(2011, 1010, 10, 1, 4.5, 7150.00, 0.14, 36450.00, 0.05);

-- Order 11: Nov 2025 — Wedding season starts
INSERT IGNORE INTO fact_orders
    (order_id, customer_id, address_id, order_date, subtotal,
     gst_amount, total_amount, status, payment_method, loyalty_discount)
VALUES (1011, 902, 902, '2025-11-22 16:20:00',
        67880.00, 3394.00, 71274.00, 'delivered', 'online', 0);
INSERT IGNORE INTO fact_order_items
    (item_id, order_id, product_id, quantity,
     weight_g, rate_per_g, making_pct, unit_price, gst_rate)
VALUES (2012, 1011, 30, 1, 8.1, 7150.00, 0.18, 67880.00, 0.05);

-- Order 12: Dec 2025 — Wedding season peak
INSERT IGNORE INTO fact_orders
    (order_id, customer_id, address_id, order_date, subtotal,
     gst_amount, total_amount, status, payment_method, loyalty_discount)
VALUES (1012, 903, 903, '2025-12-08 10:30:00',
        27730.00, 1387.00, 29117.00, 'delivered', 'online', 1387.00);
INSERT IGNORE INTO fact_order_items
    (item_id, order_id, product_id, quantity,
     weight_g, rate_per_g, making_pct, unit_price, gst_rate)
VALUES (2013, 1012, 1, 1, 3.2, 7380.00, 0.12, 27730.00, 0.05);

-- Order 13: Dec 2025 — Wedding gifting multi-item
INSERT IGNORE INTO fact_orders
    (order_id, customer_id, address_id, order_date, subtotal,
     gst_amount, total_amount, status, payment_method, loyalty_discount)
VALUES (1013, 901, 901, '2025-12-20 14:00:00',
        50640.00, 2532.00, 53172.00, 'delivered', 'online', 0);
INSERT IGNORE INTO fact_order_items
    (item_id, order_id, product_id, quantity,
     weight_g, rate_per_g, making_pct, unit_price, gst_rate)
VALUES
(2014, 1013, 10, 1, 4.5, 7380.00, 0.14, 37870.00, 0.05),
(2015, 1013, 20, 1, 2.0, 7380.00, 0.10, 12770.00, 0.05);

-- Order 14: Jan 2026 — Wedding season chain
INSERT IGNORE INTO fact_orders
    (order_id, customer_id, address_id, order_date, subtotal,
     gst_amount, total_amount, status, payment_method, loyalty_discount)
VALUES (1014, 902, 902, '2026-01-15 11:00:00',
        40720.00, 2036.00, 42756.00, 'delivered', 'online', 0);
INSERT IGNORE INTO fact_order_items
    (item_id, order_id, product_id, quantity,
     weight_g, rate_per_g, making_pct, unit_price, gst_rate)
VALUES (2016, 1014, 39, 1, 5.0, 7540.00, 0.08, 40720.00, 0.05);

-- Order 15: Mar 2026 — Recent order
INSERT IGNORE INTO fact_orders
    (order_id, customer_id, address_id, order_date, subtotal,
     gst_amount, total_amount, status, payment_method, loyalty_discount)
VALUES (1015, 903, 903, '2026-03-10 15:30:00',
        29540.00, 1477.00, 31017.00, 'confirmed', 'online', 1477.00);
INSERT IGNORE INTO fact_order_items
    (item_id, order_id, product_id, quantity,
     weight_g, rate_per_g, making_pct, unit_price, gst_rate)
VALUES (2017, 1015, 1, 1, 3.2, 7850.00, 0.12, 29540.00, 0.05);


-- ── Done ─────────────────────────────────────────────────────
SELECT CONCAT(
    'Done! Admin: hardikmalhotra1305@gmail.com | ',
    (SELECT COUNT(*) FROM dim_gold_rates WHERE source='IBJA'), ' rate records | ',
    (SELECT COUNT(*) FROM fact_orders WHERE order_id BETWEEN 1001 AND 1015), ' orders'
) AS status;