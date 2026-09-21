DROP TABLE IF EXISTS fact_sales;
DROP TABLE IF EXISTS dim_product;

CREATE TABLE dim_product (
    product_key    SERIAL PRIMARY KEY,
    product_id     VARCHAR(50) NOT NULL,
    product_name   VARCHAR(255) NOT NULL,
    category       VARCHAR(100) NOT NULL,
    sub_category   VARCHAR(100) NOT NULL,
    CONSTRAINT uq_product UNIQUE (product_id, product_name)
);


CREATE TABLE fact_sales (
    row_id           SERIAL PRIMARY KEY,
    order_id         VARCHAR(50) NOT NULL,

    product_key      INTEGER NOT NULL
        REFERENCES dim_product(product_key),

    customer_id      VARCHAR(50) NOT NULL
        REFERENCES dim_customer(customer_id),

    geography_id     INTEGER NOT NULL
        REFERENCES dim_geography(geography_id),

    order_date_id    INTEGER NOT NULL
        REFERENCES dim_time(date_id),

    ship_date_id     INTEGER NOT NULL
        REFERENCES dim_time(date_id),

    order_priority   VARCHAR(20),
    ship_mode        VARCHAR(50),

    sales            NUMERIC(12,2) NOT NULL CHECK (sales >= 0),
    profit           NUMERIC(12,2) NOT NULL,
    quantity         INTEGER NOT NULL CHECK (quantity > 0),
    discount         NUMERIC(5,2) NOT NULL CHECK (discount >= 0 AND discount <= 1),
    shipping_cost    NUMERIC(10,2) NOT NULL CHECK (shipping_cost >= 0)
);

CREATE INDEX idx_fact_sales_order_date ON fact_sales(order_date_id);
CREATE INDEX idx_fact_sales_product    ON fact_sales(product_key);
CREATE INDEX idx_fact_sales_customer   ON fact_sales(customer_id);
CREATE INDEX idx_fact_sales_geography  ON fact_sales(geography_id);
CREATE INDEX idx_dim_product_category  ON dim_product(category, sub_category);
