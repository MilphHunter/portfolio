import psycopg2

from get_goods import get_count_pages, get_products_id, get_products_info, get_some_info

connection = psycopg2.connect(
    host="localhost",
    user="postgres",
    password="ALINAsunrise2004",
    database="postgres"
)

cursor = connection.cursor()

create_table_query = """
CREATE TABLE IF NOT EXISTS rozetka (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255),
    site_id INT,
    price INT,
    old_price INT,
    href VARCHAR(255),
    brand VARCHAR(255),
    brand_id INT,
    docket VARCHAR(255),
    image_main VARCHAR(255),
    page INT
)
"""
cursor.execute(create_table_query)
connection.commit()

truncate_table_query = "TRUNCATE TABLE rozetka"
cursor.execute(truncate_table_query)
connection.commit()

insert_data_query = """
INSERT INTO rozetka (title, site_id, price, old_price, href, brand, brand_id, docket, image_main, page) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""
url = "https://hard.rozetka.com.ua/computers/c80095/page=1/"
max_page = get_count_pages(url)
products_id = get_products_id(max_page)
products = get_products_info(products_id)
data = get_some_info(products)
cursor.executemany(insert_data_query, data)
connection.commit()

cursor.close()
connection.close()
print('Done!')
