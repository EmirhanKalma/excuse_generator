import socket

# ЗАМЕТКА: Твой URL из кода
url = "api-inference.huggingface.co"

print("--- ТЕСТ 1: Проверка на скрытые русские буквы ---")
for char in url:
    # ЗАМЕТКА: Выводим код каждого символа. 
    # Если все символы латинские, коды должны быть строго меньше 128.
    if ord(char) > 127:
        print(f"НАЙДЕН СКРЫТЫЙ СИМВОЛ: '{char}' с кодом {ord(char)}")
    else:
        print(f"Символ '{char}' - ОК (код {ord(char)})")

print("\n--- ТЕСТ 2: Чистый системный запрос DNS ---")
try:
    # ЗАМЕТКА: Пытаемся разрешить имя без всяких requests и urllib3
    ip = socket.gethostbyname(url)
    print(f"Успех! Системный DNS нашел IP: {ip}")
except Exception as e:
    print(f"Системный DNS выдал ошибку: {e}")