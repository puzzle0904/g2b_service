import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox
import firebase_admin
from firebase_admin import credentials, auth
import subprocess

# Firebase Admin SDK 초기화
cred_path = 'serviceAccountKey.json'
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)

class LoginForm(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('로그인')

        self.email_label = QLabel('이메일:')
        self.email_entry = QLineEdit()

        self.password_label = QLabel('비밀번호:')
        self.password_entry = QLineEdit()
        self.password_entry.setEchoMode(QLineEdit.Password)

        self.login_button = QPushButton('로그인')
        self.login_button.clicked.connect(self.login)

        self.signup_button = QPushButton('회원가입')
        self.signup_button.clicked.connect(self.open_signup_form)

        layout = QVBoxLayout()
        layout.addWidget(self.email_label)
        layout.addWidget(self.email_entry)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_entry)
        layout.addWidget(self.login_button)
        layout.addWidget(self.signup_button)

        self.setLayout(layout)

    def login(self):
        email = self.email_entry.text().strip()
        password = self.password_entry.text().strip()

        # 간단한 입력 유효성 검사
        if not email or not password:
            QMessageBox.warning(self, '입력 오류', '이메일과 비밀번호는 필수 입력 사항입니다.')
            return

        try:
            # Firebase Authentication을 사용하여 로그인
            user = auth.get_user_by_email(email)
            # 실제 애플리케이션에서는 비밀번호 확인을 Firebase 클라이언트 SDK로 해야 합니다
            QMessageBox.information(self, '로그인 성공', f'환영합니다, {user.display_name}님!')

        except firebase_admin._auth_utils.UserNotFoundError:
            QMessageBox.warning(self, '로그인 실패', '로그인에 실패했습니다: 이메일을 찾을 수 없습니다.')
        except Exception as e:
            QMessageBox.warning(self, '로그인 실패', f'로그인 중 오류가 발생했습니다: {str(e)}')

    def open_signup_form(self):
        # 회원가입 폼을 실행
        subprocess.Popen([sys.executable, 'join.py'])

if __name__ == '__main__':
    app = QApplication(sys.argv)
    login_form = LoginForm()
    login_form.show()
    sys.exit(app.exec_())
