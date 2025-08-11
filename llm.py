import openai
from dotenv import load_dotenv
import os
import re
import json

dotenv_path = r"C:\Users\nyeny\Desktop\학교\오픈SW\Projects\api_key.env"

class KioskLLM:
    def __init__(self):
        load_dotenv(dotenv_path=dotenv_path)
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = openai.OpenAI(api_key=self.api_key)
        self.chat_history = []

    def summarize_store(self, store_json: str) -> str:
        stores = json.loads(store_json)
        result = ""
        for store in stores:
            name = store.get("name", "")
            address = store.get("location", {}).get("address_kr", "")
            hours = store.get("business_hours", {})
            open_time = hours.get("open", "")
            close_time = hours.get("close", "")
            result += f"[매장]\n이름: {name} / 위치: {address}\n운영시간: {open_time} ~ {close_time}\n"
        return result

    def summarize_menus(self, menu_json: str) -> str:
        menus = json.loads(menu_json)
        result = "[메뉴]\n"
        for m in menus:
            menu_id = m.get("menu_id", "")
            name = m.get("name", {}).get("ko", "")
            price = m.get("price", "")
            option_ids = ", ".join(m.get("option_ids", [])) or "없음"
            result += f"- id: {menu_id} / 이름: {name} / 가격: {price} / 옵션: {option_ids}\n"
        return result

    def summarize_options(self, option_json: str) -> str:
        options = json.loads(option_json)
        result = "[옵션]\n"
        for opt in options:
            opt_id = opt.get("option_id", "")
            name = opt.get("name", "")
            choices = ", ".join([
                f"{choice['label']}({choice['price']:+})"
                for choice in opt.get("choices", [])
            ])
            result += f"- id: {opt_id} / 이름: {name} / 선택지: {choices}\n"
        return result

    def build_final_messages(self, user_input, store_data, menu_data, option_data):
        system_msg = {
            "role": "system",
            "content": "당신은 매장 키오스크에 탑재된 AI입니다. 아래 매장, 메뉴, 옵션 정보, 지침과 데이터 및 대화 이력을 참고하여 자연스럽게 응답하세요."
        }

        # 초기 데이터 제공은 첫 대화일 때만
        if not self.chat_history:
            store_summary = self.summarize_store(store_data)
            menu_summary = self.summarize_menus(menu_data)
            option_summary = self.summarize_options(option_data)
            intro_msg = {
                "role": "system",
                "content": f"""

                    {store_summary}

                    {menu_summary}

                    {option_summary}

                    [지침]
        - 친절하고 정중한 말투를 사용하세요.
        - 추천 이유와 옵션을 안내하세요.
        - 특수문자는 말하지 마세요.
        - 가격은 '천 원 추가돼요' 식으로 자연스럽게.
        - 정보를 한꺼번에 주지 말고 대화를 이어가세요.
        - 주문 외 질문은 다음 문구로 응답하세요:
          "죄송합니다 고객님.. 주문 외적인 질문은 답변이 불가능합니다..."

          [출력 형식]
        당신의 모든 응답은 다음 JSON 구조로 출력되어야 합니다:

        json
        {{
          "Conversation": "<사용자에게 출력할 응답 문장>",
          "FunctionCall": [
            {{
              "Function": "<함수 이름>",  // 필수
              "MenuID": <메뉴 ID>,       // 필요 시
              "Quantity": <수량>,         // 필요 시
              "Option":  {{ ["옵션ID", 선택index], ... }}, // 필요 시
              "NewOption": {{ ["옵션ID", 선택index], ... }} // 필요 시
            }}
          ]
        }}
        function 종류 :
        	start : 대화를 시작했을 경우의 함수
        	ex) user : "안녕하세요~"
        	assistant : {{
        		"Conversation" : "안녕하세요~ 인생치킨에 오신 것을 환영합니다. 무엇을 도와드릴까요?",
        		"FunctionCall" : {{
        			"Function" : "start"
        		}}
        	}}
        	justChat : 액션이 필요하지 않은 대화의 경우의 함수
        	ex) user : "여기에는 무슨 메뉴를 파나요? "
        	assistant : {{
        		"Conversation" : "저희 인생치킨은 인생후라이드, 인생양념, 인생간장 치킨이 있습니다! 무엇을 드릴까요?",
        		"FunctionCall" : {{
        			"Function" : "justChat"
        		}}
        	}}
        	user : "아 그러면 후라이드 치킨으로 주세요~"
        	assistant : {{
        		"Conversation" : "저희 인생 후라이드 치킨은 18000원이며, 옵션으로 순살 혹은 콤보로 변경시 2000원 추가되며, 맵기 조절이 가능합니다. 맵기는 순하게, 보통, 맵게가 있습니다. 어떻게 하시겠습니까?",
        		"FunctionCall" : {{
        			"Function" : "justChat"
        		}}		
        	}}
        	addMenu : 사용자가 메뉴를 추가해달라고 요청했을 경우의 함수
        	ex) user : "아 그러면 순살로 맵게 해서 주세요"
        	assistant : {{
        		"Conversation" : "네, 그러면 인생 후라이드 치킨 순살, 맵게해서 장바구니에 담았습니다. 총 가격은 2만원입니다. 추가로 주문하시겠습니까?",
        		"FunctionCall" : {{
        			"Function" : "addMenu",	
        			"MenuID" : "menu001",
        			"Quantity" : 1,
        			"Option" : [ 
        				{{ 
        					"optionID" : "opt001",
        					"index" : 1 
        				}}, 
        				{{
        					"optionID" : "opt002", 
        					"index" : 2 
        				}}
        			]
        		}}
        	}}
        	changeOption : 추가된 메뉴 내에서 옵션 변경을 요청했을 경우의 함수
        	ex) user: "아, 생각해보니까 제 부모님이 매운 걸 못 드시네요... 그냥 순한 맛으로 해주세요"
        	assistant : {{
        		"Conversation" : "네, 그러면 맵기를 순한 맛으로 변경해드리겠습니다. 추가로 필요하신게 있으신가요?",
        		"FunctionCall" : {{
        			"Function" : "changeOption",
        			"MenuID" : "menu001",
        			"Quantity" : 1,
        			"Option" : [ 
        				{{ 
        					"optionID" : "opt001",
        					"index" : 1 
        				}}, 
        				{{
        					"optionID" : "opt002", 
        					"index" : 2 
        				}}
        			],
        			"NewOption" : [ 
        				{{ 
        					"optionID" : "opt001",
        					"index" : 1 
        				}}, 
        				{{
        					"optionID" : "opt002", 
        					"index" : 0 
        				}}
        			]
        		}}
        	}}
        	deleteMenu : 추가된 메뉴 중 일부를 삭제 요청했을 경우의 함수
        	ex) user : "아~ 진짜 죄송해요. 후라이드 빼주실래요? 고민 좀 더 해볼게요."
        	assistant : {{
        		"Conversation" : "네, 그러면 후라이드 치킨을 제외하겠습니다. 고민 끝나시면 주문 도와드리겠습니다.",
        		"FunctionCall" : {{
        			"Function" : "deleteMenu",	
        			"MenuID" : "menu001",	
        			"Quantity" : 1,
        			"Option" : [ 
        				{{ 
        					"optionID" : "opt001",
        					"index" : 1 
        				}}, 
        				{{
        					"optionID" : "opt002", 
        					"index" : 0 
        				}}
        			]
        		}}
        	}}
        	purchase : 결제를 요청받았을 때의 함수
        	ex) user : "아... 그냥 치킨 안 먹어야겠다. 안녕히 계세요..."
        	assistant : {{
        		"Conversation" : "네, 감사합니다. 안녕히 가세요.",	
        		"FunctionCall" : {{
        			"Function" : "end"
        		}}
        	}}
        	end : 대화가 끝났을 경우의 함수
        	ex) user : "아... 그냥 치킨 안 먹어야겠다. 안녕히 계세요..."
        	assistant : {{
        		"Conversation" : "네, 감사합니다. 안녕히 가세요.",	
        		"FunctionCall" : {{
        			"Function" : "end"
        		}}
        	}}

                    """
            }
            self.chat_history.append(intro_msg)

        self.chat_history.append({"role": "user", "content": user_input})
        return [system_msg] + self.chat_history

    def extract_json_from_markdown(self, md_text):
        pattern = r"```json\s*(\{.*?\})\s*```"
        match = re.search(pattern, md_text, re.DOTALL)
        if match:
            return match.group(1)
        return md_text

    def input_text_to_ai(self, user_msg):
        messages = self.build_final_messages(user_msg)
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.3
        )
        response_dict = response.model_dump()
        reply = response_dict['choices'][0]['message']['content']
        self.chat_history.append({"role": "assistant", "content": reply})
        return self.extract_json_from_markdown(reply)


if __name__ == "__main__":
    dotenv_path = r"C:\Users\nyeny\Desktop\오픈SW\Projects\module\api_key.env"
    kiosk_ai = KioskLLM(dotenv_path)

    while True:
        user_input = input("사용자 입력: ")
        if user_input.lower() in ["종료", "exit", "quit"]:
            print("종료합니다.")
            break

        result_json = kiosk_ai.input_text_to_ai(user_input)
        print("AI 응답 JSON:\n", result_json)
