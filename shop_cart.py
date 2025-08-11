import db_connect as db

class ShoppingList:
    def __init__(self):
        self.list = []

    def add(self, menu_id, quantity, option):
        for item in self.list:
            if item["menu_id"] == menu_id and item["option"] == option:
                item["quantity"] += quantity
                return
        self.list.append({
            "menu_id": menu_id,
            "quantity": quantity,
            "option": option
        })

    def change_option(self, menu_id, option, new_option):
        for item in self.list:
            if item["menu_id"] == menu_id and item["option"] == option:
                item["option"] = new_option

    def delete(self, menu_id, option):
        self.list = [item for item in self.list if not (item["menu_id"] == menu_id and item["option"] == option)]

    def get_items(self):
        return self.list  # 장바구니 원본 데이터 반환

    # 이 함수는 장바구니에 담긴 정보를 테스트하기 위한 디버그 함수
    def print_all_list_info(self):
        if not self.list:
            print("장바구니가 비어있습니다.")
        else:
            for item in self.list:
                print(item)
