import pymysql
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'  # 定义日志格式
)

db_host = "ipv6.tangtuan.top"  # 数据库服务主机
db_user = "instock_user"  # 数据库访问用户
db_password = "1qasde#2WW"  # 数据库访问密码
db_database = "instockdb"  # 数据库名称
db_port = 3306  # 数据库服务端口
db_charset = "utf8mb4"  # 数据库字符集

MYSQL_CONN_URL = "mysql+pymysql://%s:%s@%s:%s/%s?charset=%s" % (
    db_user, db_password, db_host, db_port, db_database, db_charset)
logging.info(f"数据库链接信息：{ MYSQL_CONN_URL}")

MYSQL_CONN_DBAPI = {'host': db_host, 'user': db_user, 'password': db_password, 'database': db_database,
                    'charset': db_charset, 'port': db_port, 'autocommit': True}


# DB Api -数据库连接对象connection
def get_connection():
    try:
        return pymysql.connect(**MYSQL_CONN_DBAPI)
    except Exception as e:
        logging.error(f"database.conn_not_cursor处理异常：{MYSQL_CONN_DBAPI}{e}")
    return None


# 尝试连接到 MySQL 数据库
try:
    conn = get_connection()
    if conn:
        logging.info("数据库连接成功")
        # 这里可以添加数据库操作的代码
        # ...
finally:
    if conn:
        conn.close()
        logging.info("数据库连接已关闭")