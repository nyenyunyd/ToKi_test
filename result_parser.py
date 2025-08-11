import json

def parse_llm_response(response_text: str):
    """
    LLM으로부터 받은 JSON 형태의 응답 문자열을 파싱하여,
    대화 내용과 함수 호출 리스트를 추출합니다.

    Args:
        response_text (str): LLM이 반환한 JSON 문자열

    Returns:
        tuple:
            - conversation_text (str): 사용자에게 보여줄 응답 문장
            - function_calls (list[dict]): 호출해야 할 함수들 정보 리스트
    """
    data = json.loads(response_text)
    conversation_text = data.get("Conversation", "")
    function_calls = data.get("FunctionCall", [])

    # FunctionCall이 단일 dict일 경우 리스트로 감싸기
    if isinstance(function_calls, dict):
        function_calls = [function_calls]

    return conversation_text, function_calls
