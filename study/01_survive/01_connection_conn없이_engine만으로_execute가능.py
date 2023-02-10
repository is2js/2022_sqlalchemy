from sqlalchemy import create_engine

# 1. engine 생성
engine = create_engine('mysql+pymysql://root:564123@localhost:3306/cinema')
# print(engine)
# python .\01_survive\01_connection.py
# Engine(mysql+pymysql://root:***@localhost:3306/cinema)

# 2. conn 객체 생성
conn = engine.connect()

# 3. conn객체로 execute query 가능
response = conn.execute('SELECT * FROM filmes;')

for row in response:
    print(row)
    # ('Forest Gump', 'Drama', 1994)
    # 4. 응답row는 속성을 가진다.
    print(row.title)
    # Forest Gump

# 5. conn없이 바로 engine으로도 execute가 가능하다.
response2 = engine.execute('SELECT * FROM filmes;')
for row in response2:
    print(row)
    # ('Forest Gump', 'Drama', 1994)
    # 4. 응답row는 속성을 가진다.
    print(row.title)
