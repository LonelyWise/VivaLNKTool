import pymysql
pymysql.install_as_MySQLdb()


basedata = {
    'host': 'localhost',
    'port': 3307,
    'user': 'root',
    'passwd': 'test23',
    # 'db': 'hrm',
    'charset': 'utf8'
}
# 打开数据库连接
conn = pymysql.connect(**basedata)

try:
    # 使用 cursor() 方法创建一个游标对象 cursor
    cursor = conn.cursor()

    sql = '''create table UserReg(
           name CHAR(20) NOT NULL  PRIMARY KEY,
           age VARCHAR(6),
           sex CHAR(6),
           bir char(20),
           edu char(10),
           pro char(10),
           school char(18),
           tel VARCHAR(20),
           emile char(10),
           dep char(10)
          )'''
    cursor.execute(sql)

    # commit 修改
    conn.commit()

    # 关闭游标
    cursor.close()

    # 关闭链接
    conn.close()
    print("添加成功")
except:
    print("添加记录失败")

    # 发生错误时回滚
    conn.rollback()