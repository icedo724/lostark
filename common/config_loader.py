import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(BASE_DIR, 'config')

def load_api_key():
    try:
        with open(os.path.join(CONFIG_DIR, 'api.txt'), 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        raise FileNotFoundError("config/api.txt 파일을 찾을 수 없습니다.")

def load_db_config():
    try:
        with open(os.path.join(CONFIG_DIR, 'db.txt'), 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise Exception(f"DB 설정 로드 실패: {e}")