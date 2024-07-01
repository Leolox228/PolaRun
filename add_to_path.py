import os
import winreg

if not os.path.exists(default_path = os.path.expanduser("~\\PolaRun\\") + 'polarun.bat'):
    c = input("Если хотите использовать прокси, то введите y/n: ")
    with open('polarun.bat', 'w') as f:
        if c == 'y':
            f.write(f"""cd PolaRun
python {os.path.expanduser("~\\PolaRun\\") +  + 'polarun.py --proxy'}""")
        else:
            f.write(f"""cd PolaRun
python {os.path.expanduser("~\\PolaRun\\") +  + 'polarun.py'}""")
    print("Файл polarun.bat создан.")

def find_polarun_directory():
    default_path = os.path.expanduser("~\\PolaRun")
    if os.path.exists(default_path):
        return default_path
    
    return None

def add_to_path(directory):
    if not os.path.exists(directory):
        print(f"Директория {directory} не существует.")
        return False

    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Environment', 0, winreg.KEY_ALL_ACCESS) as key:
        path = winreg.QueryValueEx(key, 'PATH')[0]

    if directory.lower() in path.lower():
        print(f"Директория {directory} уже в PATH.")
        return True

    new_path = f"{path};{directory}"
    winreg.SetValueEx(key, 'PATH', 0, winreg.REG_EXPAND_SZ, new_path)

    os.environ['PATH'] = new_path

    print(f"Директория {directory} успешно добавлена в PATH.")
    return True

def main():
    polarun_dir = find_polarun_directory()
    if polarun_dir:
        if add_to_path(polarun_dir):
            print("Перезапустите командную строку, чтобы изменения вступили в силу.")
    else:
        print("Директория PolaRun не найдена.")

if __name__ == "__main__":
    main()