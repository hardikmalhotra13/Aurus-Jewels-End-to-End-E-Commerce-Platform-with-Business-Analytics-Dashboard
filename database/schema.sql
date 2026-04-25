-- ============================================================
-- AURUS JEWELS — Complete Database Schema
-- MySQL 8.x | InnoDB | UTF-8mb4
-- ============================================================

CREATE DATABASE IF NOT EXISTS AurusJewels
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE AurusJewels;

-- ============================================================
-- DIMENSION TABLES
-- ============================================================

CREATE TABLE dim_customers (
    customer_id   INT AUTO_INCREMENT PRIMARY KEY,
    full_name     VARCHAR(100)  NOT NULL,
    email         VARCHAR(150)  UNIQUE NOT NULL,
    password_hash VARCHAR(255)  NOT NULL,
    phone         VARCHAR(20),
    role          ENUM('customer','admin') DEFAULT 'customer',
    loyalty_tier  ENUM('member','silver','gold','platinum') DEFAULT 'member',
    total_spend   DECIMAL(12,2) DEFAULT 0.00,
    is_active     TINYINT(1)    DEFAULT 1,
    created_at    TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE dim_categories (
    category_id   INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    slug          VARCHAR(100) UNIQUE NOT NULL,
    display_order INT          DEFAULT 0,
    image_path    VARCHAR(255)
) ENGINE=InnoDB;

CREATE TABLE dim_products (
    product_id      INT AUTO_INCREMENT PRIMARY KEY,
    sku             VARCHAR(20)   UNIQUE NOT NULL,
    name            VARCHAR(150)  NOT NULL,
    description     TEXT,
    category_id     INT           NOT NULL,
    metal_type      ENUM('gold','silver') NOT NULL,
    karat           ENUM('22K','18K','925') NOT NULL,
    weight_g        DECIMAL(8,3)  NOT NULL,
    making_pct      DECIMAL(5,4)  NOT NULL,
    stock_qty       INT           DEFAULT 0,
    image_main      VARCHAR(255),
    image_2         VARCHAR(255),
    image_3         VARCHAR(255),
    image_4         VARCHAR(255),
    is_featured     TINYINT(1)    DEFAULT 0,
    is_active       TINYINT(1)    DEFAULT 1,
    bis_hallmark_no VARCHAR(50),
    created_at      TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES dim_categories(category_id)
) ENGINE=InnoDB;

CREATE TABLE dim_gold_rates (
    rate_id        INT AUTO_INCREMENT PRIMARY KEY,
    metal_type     ENUM('gold','silver') NOT NULL,
    karat          ENUM('22K','18K','925') NOT NULL,
    rate_per_gram  DECIMAL(10,2) NOT NULL,
    effective_date DATE          NOT NULL,
    source         VARCHAR(100)  DEFAULT 'IBJA',
    updated_by     INT,
    created_at     TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (updated_by) REFERENCES dim_customers(customer_id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE dim_addresses (
    address_id    INT AUTO_INCREMENT PRIMARY KEY,
    customer_id   INT          NOT NULL,
    label         VARCHAR(50)  DEFAULT 'Home',
    full_name     VARCHAR(100) NOT NULL,
    phone         VARCHAR(20)  NOT NULL,
    address_line1 VARCHAR(255) NOT NULL,
    address_line2 VARCHAR(255),
    city          VARCHAR(100) NOT NULL,
    state         VARCHAR(100) NOT NULL,
    pincode       VARCHAR(10)  NOT NULL,
    is_default    TINYINT(1)   DEFAULT 0,
    created_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES dim_customers(customer_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE dim_coupons (
    coupon_id       INT AUTO_INCREMENT PRIMARY KEY,
    coupon_code     VARCHAR(50)   UNIQUE NOT NULL,
    discount_pct    DECIMAL(5,2)  NOT NULL,
    min_order_value DECIMAL(12,2) DEFAULT 0,
    max_uses        INT           DEFAULT 100,
    used_count      INT           DEFAULT 0,
    valid_from      DATE          NOT NULL,
    valid_until     DATE          NOT NULL,
    is_active       TINYINT(1)    DEFAULT 1,
    created_at      TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE dim_vendors (
    vendor_id      INT AUTO_INCREMENT PRIMARY KEY,
    name           VARCHAR(150) NOT NULL,
    contact_person VARCHAR(100),
    phone          VARCHAR(20),
    email          VARCHAR(150),
    address        TEXT,
    gst_no         VARCHAR(20),
    is_active      TINYINT(1)   DEFAULT 1,
    created_at     TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ============================================================
-- FACT TABLES
-- ============================================================

CREATE TABLE fact_orders (
    order_id            INT AUTO_INCREMENT PRIMARY KEY,
    customer_id         INT           NOT NULL,
    shipping_address_id INT,
    order_status        ENUM('pending','confirmed','processing','shipped','delivered','cancelled') DEFAULT 'pending',
    subtotal            DECIMAL(12,2) NOT NULL,
    discount_amount     DECIMAL(12,2) DEFAULT 0,
    coupon_code         VARCHAR(50),
    coupon_discount     DECIMAL(12,2) DEFAULT 0,
    loyalty_discount    DECIMAL(12,2) DEFAULT 0,
    seasonal_discount   DECIMAL(12,2) DEFAULT 0,
    threshold_discount  DECIMAL(12,2) DEFAULT 0,
    cgst_amount         DECIMAL(12,2) DEFAULT 0,
    sgst_amount         DECIMAL(12,2) DEFAULT 0,
    total_amount        DECIMAL(12,2) NOT NULL,
    gold_rate_22k       DECIMAL(10,2),
    gold_rate_18k       DECIMAL(10,2),
    silver_rate_925     DECIMAL(10,2),
    invoice_number      VARCHAR(50),
    invoice_path        VARCHAR(255),
    notes               TEXT,
    created_at          TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id)         REFERENCES dim_customers(customer_id),
    FOREIGN KEY (shipping_address_id) REFERENCES dim_addresses(address_id)
) ENGINE=InnoDB;

CREATE TABLE fact_order_items (
    item_id        INT AUTO_INCREMENT PRIMARY KEY,
    order_id       INT           NOT NULL,
    product_id     INT           NOT NULL,
    product_name   VARCHAR(150)  NOT NULL,
    karat          VARCHAR(10),
    metal_type     VARCHAR(20),
    weight_g       DECIMAL(8,3),
    quantity       INT           NOT NULL DEFAULT 1,
    gold_rate_used DECIMAL(10,2),
    metal_value    DECIMAL(12,2),
    making_charge  DECIMAL(12,2),
    pre_gst_amount DECIMAL(12,2),
    gst_amount     DECIMAL(12,2),
    unit_price     DECIMAL(12,2) NOT NULL,
    line_total     DECIMAL(12,2) NOT NULL,
    FOREIGN KEY (order_id)   REFERENCES fact_orders(order_id),
    FOREIGN KEY (product_id) REFERENCES dim_products(product_id)
) ENGINE=InnoDB;

-- ============================================================
-- OPERATIONAL TABLES
-- ============================================================

CREATE TABLE customer_cart (
    cart_id     INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    product_id  INT NOT NULL,
    quantity    INT NOT NULL DEFAULT 1,
    added_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_cart_item (customer_id, product_id),
    FOREIGN KEY (customer_id) REFERENCES dim_customers(customer_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id)  REFERENCES dim_products(product_id)   ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE customer_wishlist (
    wishlist_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    product_id  INT NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_wishlist_item (customer_id, product_id),
    FOREIGN KEY (customer_id) REFERENCES dim_customers(customer_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id)  REFERENCES dim_products(product_id)   ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE password_reset_tokens (
    token_id    INT AUTO_INCREMENT PRIMARY KEY,
    token       VARCHAR(255) UNIQUE NOT NULL,
    customer_id INT          NOT NULL,
    expires_at  TIMESTAMP    NOT NULL,
    used        TINYINT(1)   DEFAULT 0,
    created_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES dim_customers(customer_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE email_log (
    log_id        INT AUTO_INCREMENT PRIMARY KEY,
    to_email      VARCHAR(150) NOT NULL,
    subject       VARCHAR(255),
    status        ENUM('sent','failed') DEFAULT 'sent',
    sent_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    error_message TEXT
) ENGINE=InnoDB;

CREATE TABLE stock_log (
    log_id     INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT          NOT NULL,
    change_qty INT          NOT NULL,
    reason     VARCHAR(255),
    changed_by INT,
    changed_at TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES dim_products(product_id),
    FOREIGN KEY (changed_by) REFERENCES dim_customers(customer_id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE admin_ledger (
    ledger_id      INT AUTO_INCREMENT PRIMARY KEY,
    admin_id       INT          NOT NULL,
    action         VARCHAR(255) NOT NULL,
    table_affected VARCHAR(100),
    record_id      INT,
    details        TEXT,
    created_at     TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES dim_customers(customer_id)
) ENGINE=InnoDB;

-- ============================================================
-- VIEWS
-- ============================================================

CREATE OR REPLACE VIEW v_current_rates AS
SELECT metal_type, karat, rate_per_gram, effective_date, source
FROM dim_gold_rates
WHERE (metal_type, karat, effective_date) IN (
    SELECT metal_type, karat, MAX(effective_date)
    FROM dim_gold_rates
    GROUP BY metal_type, karat
);

CREATE OR REPLACE VIEW v_active_products AS
SELECT p.*, c.name AS category_name, c.slug AS category_slug
FROM dim_products p
JOIN dim_categories c ON p.category_id = c.category_id
WHERE p.is_active = 1;

CREATE OR REPLACE VIEW v_featured_products AS
SELECT * FROM v_active_products WHERE is_featured = 1;

CREATE OR REPLACE VIEW v_low_stock AS
SELECT product_id, sku, name, stock_qty, category_name
FROM v_active_products WHERE stock_qty < 5;

CREATE OR REPLACE VIEW v_order_summary AS
SELECT
    o.order_id, o.order_status, o.total_amount, o.created_at,
    c.full_name  AS customer_name,
    c.email      AS customer_email,
    COUNT(i.item_id) AS item_count
FROM fact_orders o
JOIN dim_customers c         ON o.customer_id = c.customer_id
LEFT JOIN fact_order_items i ON o.order_id    = i.order_id
GROUP BY o.order_id;

-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX idx_products_category ON dim_products(category_id);
CREATE INDEX idx_products_featured  ON dim_products(is_featured, is_active);
CREATE INDEX idx_orders_customer    ON fact_orders(customer_id);
CREATE INDEX idx_orders_status      ON fact_orders(order_status);
CREATE INDEX idx_rates_date         ON dim_gold_rates(effective_date DESC);
CREATE INDEX idx_cart_customer      ON customer_cart(customer_id);
CREATE INDEX idx_wishlist_customer  ON customer_wishlist(customer_id);

-- ============================================================
-- SEED DATA — CATEGORIES
-- ============================================================

INSERT INTO dim_categories (name, slug, display_order, image_path) VALUES
('Pendants',  'pendants',  1, 'static/images/categories/pendants.jpg'),
('Rings',     'rings',     2, 'static/images/categories/rings.jpg'),
('Earrings',  'earrings',  3, 'static/images/categories/earrings.jpg'),
('Bracelets', 'bracelets', 4, 'static/images/categories/bracelets.jpg'),
('Chains',    'chains',    5, 'static/images/categories/chains.jpg');

-- ============================================================
-- SEED DATA — GOLD RATES
-- ============================================================

INSERT INTO dim_gold_rates (metal_type, karat, rate_per_gram, effective_date, source) VALUES
('gold',   '22K', 6850.00, CURDATE(), 'IBJA'),
('gold',   '18K', 5600.00, CURDATE(), 'IBJA'),
('silver', '925',   85.00, CURDATE(), 'IBJA');

-- ============================================================
-- SEED DATA — ALL 48 PRODUCTS
-- ============================================================

INSERT INTO dim_products
  (sku, name, description, category_id, metal_type, karat,
   weight_g, making_pct, stock_qty, image_main, is_featured, bis_hallmark_no)
VALUES

-- ── PENDANTS ────────────────────────────────────────────────
('P001','Classic Diamond Heart Pendant',
 'Elegant 18K gold heart pendant with sparkling diamond accents, perfect for everyday luxury.',
 1,'gold','18K',3.2,0.12,15,
 'static/images/products/pendants/pendant_heart_18k.jpg',1,'BIS18K0001'),

('P002','Sapphire Halo Teardrop Pendant',
 'Stunning 22K gold teardrop with a vivid sapphire halo — a statement of timeless beauty.',
 1,'gold','22K',4.5,0.14,10,
 'static/images/products/pendants/pendant_sapphire_22k.jpg',1,'BIS22K0002'),

('P003','Floral Cluster Diamond Pendant',
 'Intricately crafted floral cluster pendant in 18K gold with brilliant diamond chips.',
 1,'gold','18K',3.8,0.13,12,
 'static/images/products/pendants/pendant_floral_18k.jpg',0,'BIS18K0003'),

('P004','Crescent Moon Diamond Pendant',
 'Celestial crescent moon pendant in 22K gold, adorned with shimmering diamond chips.',
 1,'gold','22K',3.0,0.12,8,
 'static/images/products/pendants/pendant_moon_22k.jpg',1,'BIS22K0004'),

('P005','Lotus Motif Gold Pendant',
 'Traditional lotus motif hand-crafted in premium 22K hallmarked gold.',
 1,'gold','22K',5.1,0.10,20,
 'static/images/products/pendants/pendant_lotus_22k.jpg',0,'BIS22K0005'),

('P006','Infinity Diamond Pendant',
 'Contemporary infinity loop pendant in 18K gold with pave diamond inlay.',
 1,'gold','18K',2.8,0.15,18,
 'static/images/products/pendants/pendant_infinity_18k.jpg',0,'BIS18K0006'),

('P007','Temple Bell Pendant',
 'Sacred temple bell pendant in pure 22K gold — a cherished traditional keepsake.',
 1,'gold','22K',6.2,0.10,6,
 'static/images/products/pendants/pendant_temple_22k.jpg',0,'BIS22K0007'),

('P008','Peacock Feather Pendant',
 'Breathtaking peacock feather design in 22K gold with exquisite detailing.',
 1,'gold','22K',4.9,0.12,9,
 'static/images/products/pendants/pendant_peacock_22k.jpg',0,'BIS22K0008'),

('P041','Kundan Choker Necklace',
 'Regal Kundan choker in 22K gold with rich gemstone meenakari work — bridal magnificence.',
 1,'gold','22K',18.5,0.14,3,
 'static/images/products/pendants/pendant_kundan_choker_22k.jpg',1,'BIS22K0041'),

('P044','Antique Temple Necklace Set',
 'Exquisite antique temple necklace set in 22K gold with matching earrings and tikka.',
 1,'gold','22K',32.0,0.12,2,
 'static/images/products/pendants/pendant_temple_set_22k.jpg',1,'BIS22K0044'),

-- ── RINGS ────────────────────────────────────────────────────
('P009','Classic Solitaire Engagement Ring',
 'The timeless solitaire — a brilliant-cut diamond set in premium 18K gold.',
 2,'gold','18K',4.8,0.15,14,
 'static/images/products/rings/ring_solitaire_18k.jpg',1,'BIS18K0009'),

('P010','Princess Cut Diamond Ring',
 'A dazzling princess-cut diamond in a four-prong 18K gold setting.',
 2,'gold','18K',5.2,0.18,7,
 'static/images/products/rings/ring_princess_18k.jpg',1,'BIS18K0010'),

('P011','Floral Band Ring',
 'Delicate floral band ring in 22K gold — lightweight, elegant, and deeply feminine.',
 2,'gold','22K',4.0,0.12,22,
 'static/images/products/rings/ring_floral_22k.jpg',0,'BIS22K0011'),

('P012','Emerald Halo Ring',
 'A vivid Colombian-cut emerald surrounded by a diamond halo in lustrous 18K gold.',
 2,'gold','18K',5.8,0.18,5,
 'static/images/products/rings/ring_emerald_18k.jpg',0,'BIS18K0012'),

('P013','Traditional Signet Ring',
 'Commanding 22K gold signet ring — a heritage piece crafted for generations.',
 2,'gold','22K',7.5,0.10,11,
 'static/images/products/rings/ring_signet_22k.jpg',0,'BIS22K0013'),

('P014','Twisted Band Diamond Ring',
 'Modern twisted shank design with pave diamond accents in 18K gold.',
 2,'gold','18K',3.9,0.16,16,
 'static/images/products/rings/ring_twisted_18k.jpg',0,'BIS18K0014'),

('P015','Ruby Cluster Ring',
 'Deep red ruby cluster ring in 22K gold — vibrant, passionate, unforgettable.',
 2,'gold','22K',5.0,0.14,8,
 'static/images/products/rings/ring_ruby_22k.jpg',0,'BIS22K0015'),

('P016','Sterling Silver Stackable Ring',
 'Minimalist stackable band in 925 sterling silver — wear one or layer many.',
 2,'silver','925',2.5,0.20,30,
 'static/images/products/rings/ring_stack_925.jpg',0,'BIS9250016'),

('P042','Diamond Solitaire Nose Pin',
 'A delicate 18K gold nose pin with a single brilliant-cut diamond.',
 2,'gold','18K',0.8,0.22,25,
 'static/images/products/rings/ring_nosepin_18k.jpg',0,'BIS18K0042'),

('P048','Three-Tone Gold Ring',
 'An architectural statement ring weaving rose, white, and yellow 18K gold in one band.',
 2,'gold','18K',5.5,0.17,10,
 'static/images/products/rings/ring_threetone_18k.jpg',0,'BIS18K0048'),

-- ── EARRINGS ─────────────────────────────────────────────────
('P017','Classic Diamond Stud Earrings',
 'The wardrobe essential — brilliant diamond studs in secure 18K gold push-back settings.',
 3,'gold','18K',3.6,0.15,20,
 'static/images/products/earrings/earring_stud_18k.jpg',1,'BIS18K0017'),

('P018','Jhumka Chandelier Earrings',
 'Iconic chandelier jhumkas in 22K gold with dancing pearl drops — bridal perfection.',
 3,'gold','22K',8.2,0.10,12,
 'static/images/products/earrings/earring_jhumka_22k.jpg',1,'BIS22K0018'),

('P019','Pearl Drop Earrings',
 'Lustrous South Sea pearl drops suspended from 22K gold.',
 3,'gold','22K',5.4,0.12,15,
 'static/images/products/earrings/earring_pearl_22k.jpg',0,'BIS22K0019'),

('P020','Geometric Hoop Earrings',
 'Bold geometric hoops in 18K gold — contemporary architecture you can wear.',
 3,'gold','18K',4.1,0.14,18,
 'static/images/products/earrings/earring_hoop_18k.jpg',0,'BIS18K0020'),

('P021','Peacock Dangle Earrings',
 'Magnificent peacock dangle earrings in 22K gold with meenakari enamel work.',
 3,'gold','22K',7.8,0.11,8,
 'static/images/products/earrings/earring_peacock_22k.jpg',0,'BIS22K0021'),

('P022','Sterling Silver Leaf Earrings',
 'Organically sculpted leaf earrings in 925 sterling silver.',
 3,'silver','925',3.2,0.22,25,
 'static/images/products/earrings/earring_leaf_925.jpg',0,'BIS9250022'),

('P023','Ruby Teardrop Danglers',
 'Passionate ruby teardrop danglers in 22K gold — a splash of royal red.',
 3,'gold','22K',6.3,0.12,10,
 'static/images/products/earrings/earring_ruby_22k.jpg',0,'BIS22K0023'),

('P024','Minimalist Bar Earrings',
 'Sleek linear bar earrings in 18K gold — modern architecture, minimal drama.',
 3,'gold','18K',2.2,0.18,22,
 'static/images/products/earrings/earring_bar_18k.jpg',0,'BIS18K0024'),

('P043','Polki Drop Earrings',
 'Regal uncut polki diamond drop earrings in 22K gold with hand-set gemstones.',
 3,'gold','22K',9.2,0.13,5,
 'static/images/products/earrings/earring_polki_22k.jpg',1,'BIS22K0043'),

-- ── BRACELETS ────────────────────────────────────────────────
('P025','Diamond Tennis Bracelet',
 'A continuous river of brilliance — 18K gold tennis bracelet with channel-set diamonds.',
 4,'gold','18K',12.5,0.18,6,
 'static/images/products/bracelets/bracelet_tennis_18k.jpg',1,'BIS18K0025'),

('P026','Gold Kada Bangle',
 'The quintessential Indian kada in 22K gold — solid, substantial, and forever.',
 4,'gold','22K',18.0,0.08,10,
 'static/images/products/bracelets/bracelet_kada_22k.jpg',1,'BIS22K0026'),

('P027','Charm Link Bracelet',
 'Playful charm link bracelet in 18K gold — each charm tells a story.',
 4,'gold','18K',8.4,0.15,12,
 'static/images/products/bracelets/bracelet_charm_18k.jpg',0,'BIS18K0027'),

('P028','Filigree Bangle Set (pair)',
 'Breathtaking filigree work bangles in 22K gold — heirloom craftsmanship.',
 4,'gold','22K',22.0,0.10,8,
 'static/images/products/bracelets/bracelet_filigree_22k.jpg',0,'BIS22K0028'),

('P029','Sterling Silver Cuff Bracelet',
 'Bold open cuff in 925 sterling silver — strong, sculptural, statement-making.',
 4,'silver','925',14.0,0.20,15,
 'static/images/products/bracelets/bracelet_cuff_925.jpg',0,'BIS9250029'),

('P030','Pearl & Gold Bracelet',
 'Alternating freshwater pearls and 22K gold links — the harmony of ocean and earth.',
 4,'gold','22K',9.8,0.12,10,
 'static/images/products/bracelets/bracelet_pearl_22k.jpg',0,'BIS22K0030'),

('P031','Infinity Stackable Bangles (set of 3)',
 'A trio of delicate infinity bangles in 18K gold — wear together or apart.',
 4,'gold','18K',10.5,0.16,8,
 'static/images/products/bracelets/bracelet_infinity_18k.jpg',0,'BIS18K0031'),

('P032','Traditional Meenakari Bangle',
 'Vibrant meenakari enamel bangle in 22K gold — a festival of colour and craft.',
 4,'gold','22K',15.5,0.11,6,
 'static/images/products/bracelets/bracelet_meenakari_22k.jpg',0,'BIS22K0032'),

('P045','Sterling Silver Anklet Pair',
 'Dainty matching anklets in 925 sterling silver with tiny charm detailing.',
 4,'silver','925',18.0,0.18,20,
 'static/images/products/bracelets/bracelet_anklet_925.jpg',0,'BIS9250045'),

('P046','Twisted Rope Gold Bangle',
 'Classic twisted rope bangle in 22K gold — the strength of tradition.',
 4,'gold','22K',16.5,0.10,7,
 'static/images/products/bracelets/bracelet_rope_22k.jpg',0,'BIS22K0046'),

-- ── CHAINS ───────────────────────────────────────────────────
('P033','Maharani Figaro Chain',
 'The iconic figaro chain in 22K gold — alternating links that catch light from every angle.',
 5,'gold','22K',12.5,0.12,12,
 'static/images/products/chains/chain_figaro_22k.jpg',1,'BIS22K0033'),

('P034','Box Chain Necklace',
 'Perfectly square box chain links in 22K gold — architectural precision for daily wear.',
 5,'gold','22K',8.8,0.10,18,
 'static/images/products/chains/chain_box_22k.jpg',1,'BIS22K0034'),

('P035','Rope Twist Chain',
 'Lush rope-twist chain in 22K gold — a classic that never goes out of style.',
 5,'gold','22K',10.2,0.10,15,
 'static/images/products/chains/chain_rope_22k.jpg',0,'BIS22K0035'),

('P036','Curb Link Chain',
 'Bold flat curb link chain in 22K gold — substantial, masculine, enduring.',
 5,'gold','22K',14.0,0.09,10,
 'static/images/products/chains/chain_curb_22k.jpg',0,'BIS22K0036'),

('P037','Wheat Chain Necklace',
 'Delicate interwoven wheat chain in 22K gold — incredibly flexible, beautifully lustrous.',
 5,'gold','22K',9.5,0.10,14,
 'static/images/products/chains/chain_wheat_22k.jpg',0,'BIS22K0037'),

('P038','Sterling Silver Herringbone Chain',
 'Ultra-flat herringbone chain in 925 sterling silver — liquid metal on skin.',
 5,'silver','925',11.0,0.18,20,
 'static/images/products/chains/chain_herringbone_925.jpg',0,'BIS9250038'),

('P039','Diamond Cut Chain',
 'Machine-faceted diamond-cut chain in 22K gold that refracts light like a prism.',
 5,'gold','22K',7.8,0.11,16,
 'static/images/products/chains/chain_diamondcut_22k.jpg',0,'BIS22K0039'),

('P040','Singapore Chain',
 'Intricate woven Singapore chain in 18K gold — lightweight luxury for everyday.',
 5,'gold','18K',6.5,0.13,18,
 'static/images/products/chains/chain_singapore_18k.jpg',0,'BIS18K0040'),

('P047','Venetian Box Chain 22K',
 'Refined Venetian box chain in 22K gold — square links with rounded corners.',
 5,'gold','22K',11.2,0.09,12,
 'static/images/products/chains/chain_venetian_22k.jpg',0,'BIS22K0047');

-- ============================================================
-- SEED DATA — SAMPLE COUPONS
-- ============================================================

INSERT INTO dim_coupons
  (coupon_code, discount_pct, min_order_value, max_uses, valid_from, valid_until)
VALUES
('WELCOME10', 10.00, 10000,  500, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 6 MONTH)),
('FESTIVE15', 15.00, 25000,  200, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 2 MONTH)),
('GOLD5',      5.00,  5000, 1000, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 1 YEAR));

-- ============================================================
-- AFTER REGISTERING, RUN THIS TO MAKE YOURSELF ADMIN:
-- UPDATE dim_customers SET role='admin' WHERE email='your@email.com';
-- ============================================================