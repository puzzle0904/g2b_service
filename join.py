import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox, QComboBox
import firebase_admin
from firebase_admin import credentials, firestore, auth

# Firebase Admin SDK 초기화
cred_path = 'serviceAccountKey.json'
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)
db = firestore.client()

class SignUpForm(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('회원가입')

        self.name_label = QLabel('이름:')
        self.name_entry = QLineEdit()

        self.email_label = QLabel('이메일:')
        self.email_entry = QLineEdit()

        self.password_label = QLabel('비밀번호:')
        self.password_entry = QLineEdit()
        self.password_entry.setEchoMode(QLineEdit.Password)

        self.telegram_label = QLabel('텔레그램 ID:')
        self.telegram_entry = QLineEdit()

        self.reception_label = QLabel('수신 동의:')
        self.reception_combo = QComboBox()
        self.reception_combo.addItems(['동의', '미동의'])

        self.sign_up_button = QPushButton('회원가입')
        self.sign_up_button.clicked.connect(self.sign_up)

        layout = QVBoxLayout()
        layout.addWidget(self.name_label)
        layout.addWidget(self.name_entry)
        layout.addWidget(self.email_label)
        layout.addWidget(self.email_entry)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_entry)
        layout.addWidget(self.telegram_label)
        layout.addWidget(self.telegram_entry)
        layout.addWidget(self.reception_label)
        layout.addWidget(self.reception_combo)
        layout.addWidget(self.sign_up_button)

        self.setLayout(layout)

    def sign_up(self):
        name = self.name_entry.text().strip()
        email = self.email_entry.text().strip()
        password = self.password_entry.text().strip()
        telegram_id = self.telegram_entry.text().strip()
        reception = self.reception_combo.currentText()

        # 간단한 입력 유효성 검사
        if not name or not email or not password or not telegram_id:
            QMessageBox.warning(self, '입력 오류', '이름, 이메일, 비밀번호, 텔레그램 ID는 필수 입력 사항입니다.')
            return

        # 이메일 중복 검사
        email_query = db.collection('users').where('Email', '==', email).get()
        if len(email_query) > 0:
            QMessageBox.warning(self, '중복 오류', '이미 사용 중인 이메일입니다.')
            return

        # 텔레그램 ID 중복 검사
        telegram_query = db.collection('users').where('TelegramID', '==', telegram_id).get()
        if len(telegram_query) > 0:
            QMessageBox.warning(self, '중복 오류', '이미 사용 중인 텔레그램 ID입니다.')
            return

        try:
            # Firebase Authentication에 사용자 생성
            user = auth.create_user(
                email=email,
                password=password,
                display_name=name
            )

            # Firebase에 사용자 정보 저장
            user_data = {
                'email': email,
                'id': telegram_id,
                'name': name,
                'reception': reception
            }
            db.collection('users').document(email).set(user_data)

            # 회원가입 성공 메시지 박스 표시
            QMessageBox.information(self, '회원가입 성공', '회원가입이 성공적으로 완료되었습니다.')

        except Exception as e:
            QMessageBox.warning(self, '회원가입 실패', f'회원가입 중 오류가 발생했습니다: {str(e)}')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    signup_form = SignUpForm()
    signup_form.show()
    sys.exit(app.exec_())