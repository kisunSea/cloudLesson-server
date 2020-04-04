import pymysql
pymysql.version_info = (1, 3, 13, "final", 0)  # 解决兼容性问题
pymysql.install_as_MySQLdb()