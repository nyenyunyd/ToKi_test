from pymongo import MongoClient
import json

# 1) MongoDB 서버 연결 (로컬 MongoDB가 27017 포트에서 실행 중이라 가정)
client = MongoClient("mongodb://localhost:27017/")

# 2) 사용할 데이터베이스 선택 (없으면 자동 생성)
db = client["test"]

# 3) 컬렉션 선택 (테이블과 유사, 없으면 자동 생성)
stores_col = db["store_info"]
menus_col = db["menu_info"]
option_col = db["option_info"]

store_info = []
menu_info = []
option_info = []

def init_data():
    store_info.clear()
    menu_info.clear()
    option_info.clear()

    for store in stores_col.find({}, {"_id": False}):
        store_info.append(store)
    for menu in menus_col.find({}, {"_id": False}):
        menu_info.append(menu)
    for option in option_col.find({}, {"_id": False}):
        option_info.append(option)

init_data()

def get_info_of_store():
    return json.dumps(store_info, ensure_ascii=False, indent=2)

def get_info_of_menu():
    return json.dumps(menu_info, ensure_ascii=False, indent=2)

def get_info_of_option():
    return json.dumps(option_info, ensure_ascii=False, indent=2)

def get_menu_by_id(menu_id):
    return next((m for m in menu_info if m["menu_id"] == menu_id), None)

def get_option_by_id(option_id):
    return next((o for o in option_info if o["option_id"] == option_id), None)

if __name__ == "__main__":
    init_data()

# 5) 문서 조회 (find_one)
#found_store = stores_col.find_one({"store_id": "store001"})
#print(found_store)

# 6) 여러 문서 조회 (find)
#for store in stores_col.find():
    #print(store)