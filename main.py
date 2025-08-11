from llm import KioskAI
import db_connect as db
from shop_list import ShoppingList
import result_parser as parser

'''
stt, tts, db 통합 전 테스트용 메인 실행 코드입니다.
- 사용자 입력을 받아 LLM에 전달 후 응답 처리
- 함수 호출에 따라 장바구니(ShoppingList) 상태 변경
- STT, TTS 모듈은 추후 통합 시 주석 해제 후 사용 예정입니다.
'''

cart = ShoppingList()  # 장바구니 객체 초기화
llm_obj = KioskAI()  # LLM 대화 처리 객체 생성

while True:
    # 사용자로부터 채팅 텍스트 입력 받음
    user_input = input("채팅 입력 : ")

    if user_input == "quit":
        # 'quit' 입력 시 루프 종료 (프로그램 종료)
        break

    '''
    # 추후 STT 모듈과 연동 시 아래 코드 참고
    stt_handler = stt.STTProcessor(
        aggressiveness=2,
        whisper_model_name="base",
        noise_threshold_db=-40,
        silence_threshold_seconds=3.0
    )
    text = stt_handler.record_sound_to_text()  # 마이크로부터 음성 인식 결과 텍스트 얻기
    '''

    # LLM에 사용자 입력 및 DB 데이터(매장, 메뉴, 옵션) 전달, 응답 결과 수신
    llm_response = llm_obj.input_text_to_ai(
        user_input,
        db.get_info_of_store(),
        db.get_info_of_menu(),
        db.get_info_of_option()
    )

    # LLM 응답에서 대화 내용과 호출 함수 정보 파싱
    conversation_text, function_calls = parser.parse_llm_response(llm_response)

    # 사용자에게 출력할 대화 내용 출력
    print(conversation_text)

    # 함수 호출 정보를 바탕으로 장바구니 상태 변경 수행
    for function in function_calls:
        function_name = function["Function"]
        menu_id = function.get("MenuID")
        quantity = function.get("Quantity")
        option = function.get("Option")

        if function_name == "start":
            # 대화 시작 시 새로운 장바구니 생성 (초기화)
            cart = ShoppingList()
        elif function_name == "addMenu":
            # 메뉴 추가 요청 시 장바구니에 항목 추가
            cart.add(menu_id, quantity, option)
        elif function_name == "changeOption":
            # 옵션 변경 요청 시 해당 메뉴 옵션 수정
            newOption = function.get("NewOption")
            cart.changeOption(menu_id, option, newOption)
        elif function_name == "deleteMenu":
            # 메뉴 삭제 요청 시 장바구니에서 해당 메뉴 제거
            cart.delete(menu_id)
        elif function_name == "end":
            # 대화 종료 요청 시 별도 처리 없음 (필요시 확장 가능)
            pass

    '''
    # 추후 TTS 연동 시, 사용자에게 음성 출력
    tts.speak_korean(context)
    '''
