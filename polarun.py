import requests
import json
import re
import io
import sys
import subprocess
import platform
import importlib
import os
from dotenv import load_dotenv, set_key
import argparse

if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write("# This file contains environment variables for the applications\n")
        print("Файл .env создан.")

if not os.path.exists('polarun.bat'):
    with open('polarun.bat', 'w') as f:
        f.write(f"""cd PolaRun
polarun.py""")
    print("Файл polarun.bat создан.")

def get_api_key():
    load_dotenv() 
    api_key = os.getenv('API_KEY')
    if not api_key:
        api_key = input("Введите ваш API key: ")
        set_key('.env', 'API_KEY', api_key)
        os.environ['API_KEY'] = api_key
    return api_key

def get_proxy():
    load_dotenv() 
    proxy = os.getenv('PROXY')
    if not proxy:
        proxy = input("Введите ваши http/https прокси: ")
        set_key('.env', 'PROXY', proxy)
        os.environ['PROXY'] = proxy
    return proxy

my_system = platform.uname()

info = f"Ты должен писать код для пользователя только РАБОЧИЙ PYTHON код, он должен выполнять задачу пользователя. Код ДОЛЖЕН правильно работать, ты можешь смотреть инфу о пользователе с помощью модуля os. Вот информация об устройстве пользователя: System: {my_system.system} Release: {my_system.release} Node Name: {my_system.node}. Тебе надо отправить ТОЛЬКО код на Питоне, НИЧЕГО БОЛЬШЕ НЕ НАДО!"

proxies = {
    'https': None,
}

headers = {
    'Content-Type': 'application/json',
}

payload = {
    "contents": [
    ]
}

def parse_arguments():
    parser = argparse.ArgumentParser(description="PolaRun - CLI для взаимодействия с Gemini API")
    parser.add_argument("--proxy", action="store_true", help="Использовать прокси")
    return parser.parse_args()

def execute_code(code):
    old_stdout = sys.stdout
    new_stdout = io.StringIO()
    sys.stdout = new_stdout
    
    try:
        import_lines = [line.strip() for line in code.split('\n') if line.strip().startswith('import') or line.strip().startswith('from')]
        modules_to_install = []

        for line in import_lines:
            module_name = line.split()[1].split('.')[0]
            try:
                importlib.import_module(module_name)
            except ImportError:
                modules_to_install.append(module_name)

        if modules_to_install:
            print("Установка недостающих модулей:")
            for module in modules_to_install:
                print(f"Установка модуля: {module}")
                subprocess.check_call([sys.executable, "-m", "pip", "install", module])

            importlib.invalidate_caches()

        exec_globals = {}
        exec(code, exec_globals)
        return new_stdout.getvalue()

    except Exception as e:
        return f"Ошибка при выполнении кода: {str(e)}"

    finally:
        sys.stdout = old_stdout

def process_sse(response):
    res = ""
    for line in response.iter_lines():
        if line:
            line = line.decode('utf-8')
            if line.startswith('data: '):
                data = line[6:]
                if data == '[DONE]':
                    break
                try:
                    json_data = json.loads(data)
                    if 'candidates' in json_data and json_data['candidates']:
                        text = json_data['candidates'][0]['content']['parts'][0]['text']
                        res += text
                        print(text, end='', flush=True)
                except json.JSONDecodeError:
                    print(f"\nError decoding JSON: {data}")
                except KeyError:
                    print(f"\nUnexpected data structure: {data}")
    return res

def code(k):
    code_blocks = re.findall(r'```(?:python)?\s*(.*?)```', k, re.DOTALL)
    if code_blocks:
        for i, code in enumerate(code_blocks):
            run_code = 'y'
            if run_code.lower() == 'y':
                result = execute_code(code)
                print("Результат выполнения кода:")
                print(result)
                payload["contents"].append({
                    "role": "user",
                    "parts": { "text": "Результат выполнения кода:" + str(result) }
                })

while True:
    args = parse_arguments()
    user_input = input(">> ")
    
    payload["contents"].append({
      "role": "user",
      "parts": { "text": user_input }
    })
    
    proxies = {
        'https': get_proxy(),
    } if args.proxy else None
    
    load_dotenv() 
    api_key = get_api_key()
    if not api_key:
        api_key = get_api_key()
    url = f'https://generativelanguage.googleapis.com/v1/models/gemini-1.5-pro:streamGenerateContent?alt=sse&key={api_key}'
    
    res = ""
    payload1 = payload.copy()
    payload1["contents"].insert(len(payload1["contents"]) - 1, {"role": "user", "parts": {"text": info}})
    if proxies["https"] != None:
        response = requests.post(url, headers=headers, json=payload1, proxies=proxies, stream=True)
    
    if response.status_code == 429:
        url = f'https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:streamGenerateContent?alt=sse&key={api_key}'
        res = ""
        payload1 = payload.copy()
        payload1["contents"].insert(len(payload1["contents"]) - 1, {"role": "user", "parts": {"text": info}})
        response = requests.post(url, headers=headers, json=payload1, proxies=proxies, stream=True)
    
    print("<< ", end = "")
    if response.status_code == 200:
        k = process_sse(response)
        payload["contents"].append({
            "role": "model",
            "parts": { "text": k }
        })
        print()
        code(k)             
    else:
        print(f"Error: {response.status_code} - {response.text}")

