import re
import json
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch


dotenv_path = r"C:\Users\nyeny\Desktop\학교\오픈SW\Projects\api_key.env"

class KioskAI:
    '''
     키오스크 AI LLM 클래스
     - DeepSeek 모델 로딩 및 대화 히스토리 관리
     - 매장, 메뉴, 옵션 데이터 요약 함수 포함
     - 사용자 입력에 따라 LLM 질의 메시지 생성 및 응답 처리
     '''

    def __init__(self, dotenv_path=None):
        '''
        초기화
        - 대화 이력 리스트 초기화
        '''
        self.conversation_history = ""
        self.tokenizer, self.model = self.load_model()

    def load_model(self):
        model_name = "deepseek-ai/deepseek-llm-7b-instruct"
        print(f"모델 로딩 중: {model_name} ...")
        model_path = "C:/Users/nyeny/Downloads/"  # ✅ 로컬 경로 지정

        tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            device_map="auto",  # GPU 자동 할당
            torch_dtype=torch.float16,
            trust_remote_code=True
        )

        print("✅ 모델 로딩 완료.")
        return tokenizer, model

    def get_store_summary(self, store_json: str) -> str:
        '''
        매장 데이터 JSON 문자열을 파싱하여 요약 문자열 생성
        매장명, 위치, 운영시간 정보 포함
        '''
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

    def get_menu_summary(self, menu_json: str) -> str:
        '''
        메뉴 데이터 JSON 문자열을 파싱하여 메뉴 목록 요약 생성
        메뉴 ID, 이름(한국어), 가격, 옵션 ID 목록 포함
        '''
        menus = json.loads(menu_json)
        result = "[메뉴]\n"
        for m in menus:
            menu_id = m.get("menu_id", "")
            name = m.get("name", {}).get("ko", "")
            price = m.get("price", "")
            option_ids = ", ".join(m.get("option_ids", [])) or "없음"
            result += f"- id: {menu_id} / 이름: {name} / 가격: {price} / 옵션: {option_ids}\n"
        return result

    def get_option_summary(self, option_json: str) -> str:
        '''
        옵션 데이터 JSON 문자열을 파싱하여 옵션 목록 요약 생성
        옵션 ID, 이름, 선택지 라벨과 가격 포함
        '''
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

    def prepare_chat_messages(self, user_input, store_data, menu_data, option_data):
        '''
        사용자 입력과 매장, 메뉴, 옵션 요약 정보를 기반으로
        OpenAI API에 보낼 메시지 배열 생성

        - 첫 대화 시 매장/메뉴/옵션 요약과 지침 메시지(system role) 포함
        - 이후 대화는 기존 히스토리와 현재 사용자 입력 추가
        '''

        # 초기 데이터 제공은 첫 대화일 때만
        if not self.conversation_history:
            store_summary = self.get_store_summary(store_data)
            menu_summary = self.get_menu_summary(menu_data)
            option_summary = self.get_option_summary(option_data)
            intro_msg = f"""

        당신은 매장 키오스크에 탑재된 AI입니다. 아래 매장, 메뉴, 옵션 정보, 지침과 데이터 및 대화 이력을 참고하여 자연스럽게 응답하세요.
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

        ```json
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

            self.conversation_history+=intro_msg

        self.conversation_history += f"\n사용자: {user_input}\nAI: "
        return self.conversation_history

    def extract_json_from_response(self, md_text):
        '''
        OpenAI 응답의 마크다운 포맷 내 JSON 코드블럭에서
        JSON 문자열만 추출

        Args:
            md_text (str): 마크다운 형식의 문자열

        Returns:
            str: JSON 문자열 (찾지 못하면 원본 문자열 반환)
        '''
        pattern = r"```json\s*(\{.*?\})\s*```"
        match = re.search(pattern, md_text, re.DOTALL)
        if match:
            return match.group(1)
        return md_text

    def input_text_to_ai(self, user_input, store_data, menu_data, option_data):
        '''
        사용자 메시지를 받아 최종 메시지 배열 생성 후
        DeepSeek AI Model 에 요청하여 응답받고,
        응답 내 JSON 부분을 추출하여 반환

        Args:
            user_input (str): 사용자 입력 텍스트
            store_data (str): 매장 데이터 JSON 문자열
            menu_data (str): 메뉴 데이터 JSON 문자열
            option_data (str): 옵션 데이터 JSON 문자열

        Returns:
            str: OpenAI 응답 내 JSON 문자열
        '''
        # 모델에 넘길 최종 프롬프트 생성 (긴 문자열)
        prompt = self.prepare_chat_messages(user_input, store_data, menu_data, option_data)
        # 토크나이저에 문자열 전달,토큰별로 나누고, 딕셔너리로 반환하지만 pt의 경우 pytorch 텐서로 반환
        input_ids = self.tokenizer(prompt, return_tensors="pt").input_ids.to(self.model.device)

        # 역전파 계산 X, 학습이 아닌 추론(생성)이므로 제외함으로써 속도 증가
        # 입력 토큰을 통해 텍스트 생성
        # input_ids: 모델에 넣을 입력 토큰(문장 토큰화 결과)
        # max_new_tokens=200: 새로 생성할 최대 토큰 수 (즉, 응답 길이 제한)
        # temperature=0.8: 생성 텍스트의 다양성을 조절 낮을수록 더 결정적이고 예측 가능한 답변 높을수록 더 창의적이고 다양한 답변
        # top_p=0.95: 누적 확률이 95%가 될 때까지 후보군에서 샘플링(누적 확률 샘플링) 다양성을 유지하면서도 이상한 답변을 줄이기 위한 기법
        # do_sample=True: 확률 기반 샘플링을 하겠다는 의미 (아니면 무조건 확률 1위 선택)

        with torch.no_grad():
            output = self.model.generate(
                input_ids,
                max_new_tokens=200,
                temperature=0.8,
                top_p=0.95,
                do_sample=True
            )
        # 사용자 입력 토큰의 길이를 구합니다.
        input_len = input_ids.shape[1]
        # output[0]는 [사용자 입력 토큰 + AI 응답 토큰] 전체 시퀀스입니다.
        # 따라서 input_len 이후의 토큰들만 슬라이싱하여 AI 답변 부분만 추출합니다.
        # tolist()는 Tensor를 파이썬 리스트로 변환하는 메서드

        response_tokens = output[0][input_len:].tolist()
        # 사용자 입력(prompt) 제외 후, AI 답변 부분만 추출
        assistant_response = self.tokenizer.decode(response_tokens, skip_special_tokens=True)

        # 7) 대화 히스토리 업데이트
        self.conversation_history+=assistant_response
        print(assistant_response)
        return self.extract_json_from_response(assistant_response)

# 모듈 테스트
if __name__ == "__main__":
    ai = KioskAI()
    tokenizer, model = ai.load_model()