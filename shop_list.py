import db_connect as db

class ShoppingList:
    """
    장바구니 내 메뉴 항목들을 관리하는 클래스입니다.
    """

    def __init__(self):
        """
        장바구니 초기화 (빈 리스트로 시작)
        """
        self.items = []

    def add(self, menu_id, quantity, option):
        """
        장바구니에 메뉴와 옵션을 추가합니다.
        동일 메뉴 및 옵션이 이미 존재하면 수량을 누적합니다.

        Args:
            menu_id (str): 메뉴 식별자
            quantity (int): 추가할 수량
            option (dict/list): 선택한 옵션 정보
        """
        for item in self.items:
            if item["menu_id"] == menu_id and item["option"] == option:
                item["quantity"] += quantity
                return
        self.items.append({
            "menu_id": menu_id,
            "quantity": quantity,
            "option": option
        })

    def change_option(self, menu_id, option, new_option):
        """
        장바구니 내 특정 메뉴 항목의 옵션을 변경합니다.

        Args:
            menu_id (str): 메뉴 식별자
            option (dict/list): 현재 옵션 정보
            new_option (dict/list): 변경할 새로운 옵션 정보
        """
        for item in self.items:
            if item["menu_id"] == menu_id and item["option"] == option:
                item["option"] = new_option
                break

    def delete(self, menu_id, option):
        """
        특정 메뉴 항목을 장바구니에서 삭제합니다.

        Args:
            menu_id (str): 메뉴 식별자
            option (dict/list): 삭제할 옵션 정보
        """
        self.items = [
            item for item in self.items
            if not (item["menu_id"] == menu_id and item["option"] == option)
        ]

    def get_items(self):
        """
        장바구니에 담긴 모든 항목을 반환합니다.

        Returns:
            list: 장바구니 항목 리스트
        """
        return self.items

    def print_all_list_info(self):
        """
        장바구니 내 모든 항목을 출력하는 디버그용 함수입니다.
        """
        if not self.items:
            print("장바구니가 비어있습니다.")
        else:
            for item in self.items:
                print(item)
