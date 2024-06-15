import firebase_admin
from firebase_admin import credentials, firestore

# Firebase Admin SDK 초기화
cred_path = 'serviceAccountKey.json'
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)
db = firestore.client()

def get_consenting_users():
    users_ref = db.collection('users')
    docs = users_ref.get()
    
    consenting_users = []

    for doc in docs:
        user_data = doc.to_dict()
        if user_data.get('reception') == '동의':
            telegram_id = user_data.get('id')  # 텔레그램 ID 필드 추출
            if telegram_id:
                consenting_users.append(telegram_id)

    return consenting_users

if __name__ == '__main__':
    consenting_users = get_consenting_users()
    print("Reception '동의' Telegram IDs:", consenting_users)
