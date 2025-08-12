from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["test"]
options_col = db["option_info"]
stores_col = db["store_info"]
menus_col = db["menu_info"]

def insert_store_info():
    # 받은 JSON 데이터 (예시)
    store_json = {
        "store": {
            "id": "0001",
            "name": "1년 전통 국밥",
            "description": "무려 1년 전통의 비법 육수로 끓여낸 순대 국밥! 나도 모르게 소주를 시키게 되버릴 지도 몰라!!",
            "location": {
                "address_kr": "경기도 평택시 신장로 55, 1층",
                "address_en": "55, Sinjang-ro, Pyeongtaek-si, Gyeonggi-do, Republic of Korea",
                "latitude": 37.081408,
                "longitude": 127.047182
            },
            "contact": {
                "phone": "031-252-1211",
                "email": "onegookbap@naver.com"
            },
            "business_hours": {
                "open": "07:00",
                "last_order": "21:30",
                "close": "22:00"
            },
            "holidays": {
                "weekly": ["월"],
                "special": ["x"]
            },
            "options": {
                "dine_in": True,
                "take_out": True,
                "kiosk_available": True,
                "multi_language": ["ko", "en"]
            }
        }
    }

    # MongoDB 저장용 문서 변환
    store_doc = {
        "store_id": store_json["store"]["id"],
        "name": store_json["store"]["name"],
        "description": store_json["store"].get("description", ""),
        "location": store_json["store"].get("location", {}),
        "contact": store_json["store"].get("contact", {}),
        "business_hours": store_json["store"].get("business_hours", {}),
        "holidays": store_json["store"].get("holidays", {}),
        "options": store_json["store"].get("options", {})
    }

    # MongoDB에 저장
    result = stores_col.insert_one(store_doc)
    print(f"Inserted store with _id: {result.inserted_id}")

def insert_option_info():
    options_json = {
        "options": [
            {
                "id": "opt001",
                "name": "국물 양",
                "type": "single",
                "choices": [
                    {"label": "국물 양 많이", "price": 1000},
                    {"label": "국물 양 보통", "price": 0},
                    {"label": "국물 양 적게", "price": -1000}
                ]
            },
            {
                "id": "opt002",
                "name": "밥",
                "type": "single",
                "choices": [
                    {"label": "밥 따로 제공(공기밥)", "price": 0},
                    {"label": "밥 끓여서 제공", "price": 0}
                ]
            },
            {
                "id": "opt003",
                "name": "다대기",
                "type": "single",
                "choices": [
                    {"label": "다대기 따로 제공", "price": 0},
                    {"label": "다대기 끓여서 제공", "price": 0}
                ]
            },
            {
                "id": "opt004",
                "name": "요리",
                "type": "single",
                "choices": [
                    {"label": "대자", "price": 10000},
                    {"label": "중자", "price": 5000},
                    {"label": "소자", "price": 0}
                ]
            }
        ]
    }

    # 옵션 문서로 변환 후 저장
    for opt in options_json["options"]:
        option_doc = {
            "option_id": opt["id"],
            "name": opt["name"],
            "type": opt.get("type", "single"),
            "choices": opt.get("choices", [])
        }
        options_col.insert_one(option_doc)
        print(f"Inserted option: {option_doc['option_id']}")

def insert_menu_info():
    menu_json = {
        "menu": [
            {
                "id": "m001",
                "name": {"ko": "순대 국밥", "en": "SoonDae GookBap"},
                "price": 9000,
                "image": "x",
                "option_ids": ["opt001", "opt002", "opt003"]
            },
            {
                "id": "m002",
                "name": {"ko": "내장 국밥", "en": "NaeZang GookBap"},
                "price": 9000,
                "image": "x",
                "option_ids": ["opt001", "opt002", "opt003"]
            },
            {
                "id": "m003",
                "name": {"ko": "반반 국밥", "en": "BanBan GookBap"},
                "price": 10000,
                "image": "x",
                "option_ids": ["opt001", "opt002", "opt003"]
            },
            {
                "id": "m004",
                "name": {"ko": "막창 국밥", "en": "MacChang GookBap"},
                "price": 12000,
                "image": "x",
                "option_ids": ["opt001", "opt002", "opt003"]
            },
            {
                "id": "m005",
                "name": {"ko": "순대 한 접시", "en": "SoonDae 1 Plate"},
                "price": 15000,
                "image": "x",
                "option_ids": ["opt004"]
            },
            {
                "id": "m006",
                "name": {"ko": "내장 한 접시", "en": "NaeZang 1 Plate"},
                "price": 15000,
                "image": "x",
                "option_ids": ["opt004"]
            },
            {
                "id": "m007",
                "name": {"ko": "반반 한 접시", "en": "BanBan 1 Plate"},
                "price": 20000,
                "image": "x",
                "option_ids": ["opt004"]
            },
            {
                "id": "m008",
                "name": {"ko": "음료", "en": "Drink"},
                "price": 2000,
                "image": "x",
                "option_ids": []
            },
            {
                "id": "m009",
                "name": {"ko": "주류", "en": "Soju"},
                "price": 5000,
                "image": "x",
                "option_ids": []
            },
            {
                "id": "m010",
                "name": {"ko": "공기밥", "en": "Rice"},
                "price": 1000,
                "image": "x",
                "option_ids": []
            },
            {
                "id": "m011",
                "name": {"ko": "육수 추가", "en": "More Soup"},
                "price": 3000,
                "image": "x",
                "option_ids": []
            }
        ]
    }

    for item in menu_json["menu"]:
        menu_doc = {
            "menu_id": item["id"],
            "name": item.get("name", {}),
            "price": item.get("price", 0),
            "image": item.get("image", ""),
            "option_ids": item.get("option_ids", [])
        }
        menus_col.insert_one(menu_doc)
        print(f"Inserted menu: {menu_doc['menu_id']}")


insert_option_info()
insert_menu_info()