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
from openai import OpenAI
import httpx

if not os.path.exists('.env'):
    with open('.env', 'w') as f:
        f.write("# This file contains environment variables for the applications\n")
    print("Файл .env создан.")

if not os.path.exists(os.path.expanduser("~\\PolaRun") + '\\polarun.bat'):
    load_dotenv() 
    v = ["gpt-3.5-turbo", "gpt-4o", "gemini-1.5-flash", "gemini-1.5-pro"]
    model = int(input("Выберите модель gpt-3.5-turbo/gpt-4o/gemini-1.5-flash/gemini-1.5-pro 0/1/2/3:\n"))
    if model < 0 or model > 3:
        model = 0
    set_key('.env', 'model', v[model])
    os.environ['model'] = v[model]
    c = input("Использовать прокси? y/n:\n")
    if (c == 'y'):
        proxy = input("Введите ваши http/https прокси:\n")
        set_key('.env', 'PROXY', proxy)
        os.environ['PROXY'] = proxy
        if c == 'y':
            set_key('.env', 'USE_PROXY', '1')
            os.environ['USE_PROXY'] = '1'
        else:
            set_key('.env', 'USE_PROXY', '0')
            os.environ['USE_PROXY'] = '0'
    with open(os.path.expanduser("~\\PolaRun") + '\\polarun.bat', 'w') as f:
        f.write(f"""cd {os.path.expanduser("~\\PolaRun")}
py {os.path.expanduser("~\\PolaRun") + '\\polarun.py'}""")
    with open(os.path.expanduser("~") + '\\polarun.bat', 'w') as f:
        f.write(f"""cd {os.path.expanduser("~")}
py {os.path.expanduser("~\\PolaRun") + '\\polarun.py'}""")
    print("Файл polarun.bat создан.")

def get_api_key():
    load_dotenv()
    model = get_model()
    if model in ["gemini-1.5-flash", "gemini-1.5-pro"]:
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            api_key = input("Введите ваш GOOGLE API key:\n")
            set_key('.env', 'GOOGLE_API_KEY', api_key)
            os.environ['GOOGLE_API_KEY'] = api_key
        return api_key
    else:
        api_key = os.getenv('CHATGPT_API_KEY')
        if not api_key:
            api_key = input("Введите ваш OPENAI API key:\n")
            set_key('.env', 'CHATGPT_API_KEY', api_key)
            os.environ['CHATGPT_API_KEY'] = api_key
        return api_key

def get_model():
    load_dotenv() 
    model = os.getenv('model')
    if not model:
        v = ["gpt-3.5-turbo", "gpt-4o", "gemini-1.5-flash", "gemini-1.5-pro"]
        model = int(input("Выберите модель gpt-3.5-turbo/gpt-4o/gemini-1.5-flash/gemini-1.5-pro: 0/1/2/3:\n"))
        if model < 0 or model > 3:
            model = 0
        set_key('.env', 'model', v[model])
        os.environ['model'] = v[model]
    return model

def change_model():
    load_dotenv() 
    v = ["gpt-3.5-turbo", "gpt-4o", "gemini-1.5-flash", "gemini-1.5-pro"]
    model = int(input("Выберите модель gpt-3.5-turbo/gpt-4o/gemini-1.5-flash/gemini-1.5-pro 0/1/2/3:\n"))
    if model < 0 or model > 3:
        model = 0
    set_key('.env', 'model', v[model])
    os.environ['model'] = v[model]
    return model

def change_proxy():
    load_dotenv() 
    proxy = input("Введите ваши http/https прокси:\n")
    set_key('.env', 'PROXY', proxy)
    os.environ['PROXY'] = proxy
    i = input("Хотите ли вы использовать прокси каждый раз при запуске PolaRun? y/n:\n")
    if i == 'y':
        set_key('.env', 'USE_PROXY', '1')
        os.environ['USE_PROXY'] = '1'
    else:
        set_key('.env', 'USE_PROXY', '0')
        os.environ['USE_PROXY'] = '0'
    return proxy

def get_proxy():
    load_dotenv() 
    proxy = os.getenv('PROXY')
    if not proxy:
        proxy = input("Введите ваши http/https прокси:\n")
        set_key('.env', 'PROXY', proxy)
        os.environ['PROXY'] = proxy
        i = input("Хотите ли вы использовать прокси каждый раз при запуске PolaRun? y/n:\n")
        if i == 'y':
            set_key('.env', 'USE_PROXY', '1')
            os.environ['USE_PROXY'] = '1'
        else:
            set_key('.env', 'USE_PROXY', '0')
            os.environ['USE_PROXY'] = '0'
    return proxy

def get_use_proxy():
    load_dotenv() 
    use_proxy = os.getenv('USE_PROXY')
    return use_proxy

my_system = platform.uname()

info = f"Ты должен писать код для пользователя только РАБОЧИЙ PYTHON код, он должен выполнять задачу пользователя. Код в ФОРМАТЕ: ```python\ncode\n```. Код ДОЛЖЕН правильно работать, ты можешь смотреть инфу о пользователе с помощью модуля os. Помни, что код СРАЗУ запускается, пользователь НЕ МОЖЕТ менять код!Вот информация об устройстве пользователя: System: {my_system.system} Release: {my_system.release} Node Name: {my_system.node}. Тебе надо отправить ТОЛЬКО код в соответствии с запросом ПОЛЬЗОВАТЕЛЯ на Питоне, НИЧЕГО БОЛЬШЕ НЕ НАДО!"
chat_gpt = [{"role": "system", "content": info}]
chat_gem = {"contents": []}

def parse_arguments():
    parser = argparse.ArgumentParser(description="PolaRun - CLI для взаимодействия с Gemini API")
    parser.add_argument("--proxy", action="store_true", help="Использовать прокси")
    parser.add_argument("--model", action="store_true", help="Сменить модель")
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

def code(k):
    code_blocks = re.findall(r'```(?:python)?\s*(.*?)```', k, re.DOTALL)
    if code_blocks:
        for i, code in enumerate(code_blocks):
            run_code = 'y'
            if run_code.lower() == 'y':
                result = execute_code(code)
                print("Результат выполнения кода:")
                print(result)
                chat_gpt.append({
                    "role": "user",
                    "content": "Результат выполнения кода:" + str(result)
                })

args = parse_arguments()
change_model1 = False
change_proxy1 = False
while True:
    if args.model and change_model1 == False:
        change_model()
        change_model1 = True
    if args.proxy and change_proxy1 == False:
        proxy_url = change_proxy()
        change_proxy1 = True
    load_dotenv()
    model = get_model()
    api_key = get_api_key()
    user_input = input(">> ")
    use_proxy = get_use_proxy()
    if use_proxy == '1':
        proxy_url = get_proxy()
    else:
        proxy_url = ""
    if model in ["gpt-3.5-turbo", "gpt-4o"]:
        client = OpenAI(api_key=api_key) if proxy_url is None or proxy_url == "" else OpenAI(api_key=api_key, http_client=httpx.Client(proxy=proxy_url))
        chat_gpt.append({
            "role": "user",
            "content": user_input
        })
        response = client.chat.completions.create(
            model=model,
            messages=chat_gpt
        )
        
        print("<< ", end = "")
        try:
            k = response.choices[0].message.content
            chat_gpt.append({
                "role": "assistant",
                "content": k
            })
            print(k)
            code(k)             
        except Exception as e:
            print(f"Error")
    else:
        headers = {
            'Content-Type': 'application/json',
        }
        proxies = {
            'https': proxy_url,
        }
        url = f'https://generativelanguage.googleapis.com/v1/models/{model}:generateContent?key={api_key}'
        chat_gem_copy = chat_gem.copy()
        chat_gem_copy["contents"].insert(len(chat_gem_copy["contents"]), {"role": "user", "parts": {"text": user_input}})
        chat_gem_copy["contents"].insert(len(chat_gem_copy["contents"]) - 1, {"role": "user", "parts": {"text": info}})
        response = requests.post(url, headers=headers, json=chat_gem_copy, proxies=proxies, stream=True)

        if response.status_code == 200:
            print("<< ", end = "")
            response_json = response.json()
            k = response_json['candidates'][0]['content']['parts'][0]['text']
            print(k)
            code(k)
