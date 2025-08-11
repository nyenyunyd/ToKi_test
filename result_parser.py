import json

def function_of_result(result):
    data = json.loads(result)
    context = data["Conversation"]
    function_calls = data["FunctionCall"]
    # 1개만 들어와서 dictionary 타입인경우 list(dict) 타입으로 변경
    if isinstance(function_calls, dict):
        function_calls = [function_calls]

    return context, function_calls

