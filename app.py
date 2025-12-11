#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
アンケートターミナルアプリ
Firebase Realtime Database + Authentication 使用
"""

import requests
import json
from config import WEB_API_KEY, DATABASE_URL, AUTH_API_URL, USER_EMAIL, USER_PASSWORD


class FirebaseAuth:
    """Firebase Authentication クラス"""
    
    def __init__(self):
        self.id_token = None
        self.user_id = None
        self.email = None
        self.refresh_token = None
    
    def sign_in(self, email: str, password: str) -> bool:
        """メール/パスワードでログイン"""
        url = f"{AUTH_API_URL}:signInWithPassword?key={WEB_API_KEY}"
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        
        try:
            response = requests.post(url, json=payload)
            data = response.json()
            
            if response.status_code == 200:
                self.id_token = data.get("idToken")
                self.user_id = data.get("localId")
                self.email = data.get("email")
                self.refresh_token = data.get("refreshToken")
                return True
            else:
                error_message = data.get("error", {}).get("message", "Unknown error")
                print(f"ログイン失敗: {error_message}")
                return False
        except Exception as e:
            print(f"ログインエラー: {e}")
            return False
    
    def sign_up(self, email: str, password: str) -> bool:
        """新規アカウント作成"""
        url = f"{AUTH_API_URL}:signUp?key={WEB_API_KEY}"
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        
        try:
            response = requests.post(url, json=payload)
            data = response.json()
            
            if response.status_code == 200:
                self.id_token = data.get("idToken")
                self.user_id = data.get("localId")
                self.email = data.get("email")
                self.refresh_token = data.get("refreshToken")
                return True
            else:
                error_message = data.get("error", {}).get("message", "Unknown error")
                print(f"新規登録失敗: {error_message}")
                return False
        except Exception as e:
            print(f"新規登録エラー: {e}")
            return False


class RealtimeDB:
    """Firebase Realtime Database クラス"""
    
    def __init__(self, auth: FirebaseAuth):
        self.auth = auth
        self.base_url = DATABASE_URL.rstrip("/")
    
    def _get_auth_param(self) -> str:
        """認証トークンパラメータを返す"""
        return f"auth={self.auth.id_token}"
    
    def get(self, path: str) -> dict | None:
        """データ読み取り (GET)"""
        url = f"{self.base_url}/{path}.json?{self._get_auth_param()}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"GETエラー: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"GETエラー: {e}")
            return None
    
    def post(self, path: str, data: dict) -> str | None:
        """データ追加 (POST) - 自動ID生成"""
        url = f"{self.base_url}/{path}.json?{self._get_auth_param()}"
        try:
            response = requests.post(url, json=data)
            if response.status_code == 200:
                result = response.json()
                return result.get("name")  # 生成されたIDを返す
            else:
                print(f"POSTエラー: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"POSTエラー: {e}")
            return None
    
    def put(self, path: str, data: dict) -> bool:
        """データ設定 (PUT) - 上書き"""
        url = f"{self.base_url}/{path}.json?{self._get_auth_param()}"
        try:
            response = requests.put(url, json=data)
            if response.status_code == 200:
                return True
            else:
                print(f"PUTエラー: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"PUTエラー: {e}")
            return False
    
    def patch(self, path: str, data: dict) -> bool:
        """データ更新 (PATCH) - 部分更新"""
        url = f"{self.base_url}/{path}.json?{self._get_auth_param()}"
        try:
            response = requests.patch(url, json=data)
            if response.status_code == 200:
                return True
            else:
                print(f"PATCHエラー: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"PATCHエラー: {e}")
            return False


class SurveyApp:
    """アンケートアプリメインクラス"""
    
    def __init__(self):
        self.auth = FirebaseAuth()
        self.db = None
        self.user_name = None
    
    def login(self) -> bool:
        """ログイン処理"""
        print("\n" + "=" * 50)
        print("      アンケートアプリへようこそ！")
        print("=" * 50)
        
        # config.pyのデフォルト値を使用または直接入力
        use_default = input("\n設定ファイルのアカウントを使用しますか？ (y/n): ").strip().lower()
        
        if use_default == 'y':
            email = USER_EMAIL
            password = USER_PASSWORD
        else:
            email = input("メールアドレス: ").strip()
            password = input("パスワード: ").strip()
        
        print("\nログイン中...")
        if self.auth.sign_in(email, password):
            self.db = RealtimeDB(self.auth)
            print(f"✓ ログイン成功！ (User ID: {self.auth.user_id})")
            
            # ユーザー名の設定/確認
            self._setup_user_profile()
            return True
        else:
            return False
    
    def _setup_user_profile(self):
        """ユーザープロフィール設定"""
        user_data = self.db.get(f"users/{self.auth.user_id}")
        
        if user_data and user_data.get("name"):
            self.user_name = user_data["name"]
            print(f"✓ ようこそ、{self.user_name}さん！")
        else:
            print("\n初めてのご利用ですね！プロフィールを設定します。")
            self.user_name = input("名前を入力してください: ").strip()
            if not self.user_name:
                self.user_name = self.auth.email.split("@")[0]
            
            profile = {
                "name": self.user_name,
                "email": self.auth.email,
                "id": self.auth.user_id
            }
            if self.db.put(f"users/{self.auth.user_id}", profile):
                print(f"✓ プロフィールが保存されました！")
    
    def show_menu(self):
        """メニュー表示"""
        print("\n" + "-" * 50)
        print("どの操作をしますか?")
        print("  0: アンケート一覧表示")
        print("  1: アンケート投稿")
        print("  2: 回答投稿")
        print("  3: 回答一覧表示")
        print("  9: 終了")
        print("-" * 50)
    
    def list_questions(self) -> list:
        """アンケート一覧表示"""
        print("\n📋 アンケート一覧")
        print("=" * 50)
        
        questions = self.db.get("questions")
        question_list = []
        
        if not questions:
            print("  (登録されたアンケートはありません)")
            return question_list
        
        for idx, (qid, q_data) in enumerate(questions.items(), 1):
            question_list.append((qid, q_data))
            sender_name = self._get_user_name(q_data.get("sender", ""))
            print(f"  {idx}. {q_data.get('name', 'タイトルなし')}")
            print(f"     本文: {q_data.get('body', '')[:30]}...")
            print(f"     投稿者: {sender_name}")
            print()
        
        return question_list
    
    def post_question(self):
        """アンケート投稿"""
        print("\n✏️ アンケート投稿")
        print("=" * 50)
        
        name = input("アンケートタイトル: ").strip()
        if not name:
            print("❌ タイトルを入力してください。")
            return
        
        body = input("アンケート内容: ").strip()
        if not body:
            print("❌ 内容を入力してください。")
            return
        
        question_data = {
            "name": name,
            "body": body,
            "sender": self.auth.user_id
        }
        
        question_id = self.db.post("questions", question_data)
        if question_id:
            print(f"✓ アンケートが登録されました！ (ID: {question_id})")
        else:
            print("❌ アンケートの登録に失敗しました。")
    
    def post_answer(self):
        """回答投稿"""
        print("\n💬 回答投稿")
        print("=" * 50)
        
        # まずアンケート一覧を表示
        question_list = self.list_questions()
        if not question_list:
            return
        
        try:
            choice = int(input("\n質問番号を入力してください: ")) - 1
            if choice < 0 or choice >= len(question_list):
                print("❌ 無効な番号です。")
                return
        except ValueError:
            print("❌ 数字を入力してください。")
            return
        
        qid, q_data = question_list[choice]
        print(f"\n選択した質問: {q_data.get('name', '')}")
        print(f"本文: {q_data.get('body', '')}")
        
        answer_body = input("\n回答を入力してください: ").strip()
        if not answer_body:
            print("❌ 回答を入力してください。")
            return
        
        answer_data = {
            "target": qid,
            "body": answer_body,
            "sender": self.auth.user_id
        }
        
        answer_id = self.db.post(f"answers/{qid}", answer_data)
        if answer_id:
            print(f"✓ 質問[{q_data.get('name', '')}]に回答[{answer_body[:20]}...]を登録しました。")
        else:
            print("❌ 回答の登録に失敗しました。")
    
    def list_answers(self):
        """回答一覧表示"""
        print("\n📖 回答一覧表示")
        print("=" * 50)
        
        # まずアンケート一覧を表示
        question_list = self.list_questions()
        if not question_list:
            return
        
        try:
            choice = int(input("\n回答を見る質問番号: ")) - 1
            if choice < 0 or choice >= len(question_list):
                print("❌ 無効な番号です。")
                return
        except ValueError:
            print("❌ 数字を入力してください。")
            return
        
        qid, q_data = question_list[choice]
        print(f"\n質問: {q_data.get('name', '')}")
        print(f"本文: {q_data.get('body', '')}")
        print("-" * 40)
        
        answers = self.db.get(f"answers/{qid}")
        
        if not answers:
            print("  (回答がありません)")
            return
        
        print(f"\n📝 回答一覧 ({len(answers)}件):")
        for idx, (aid, a_data) in enumerate(answers.items(), 1):
            sender_name = self._get_user_name(a_data.get("sender", ""))
            print(f"  {idx}. {a_data.get('body', '')}")
            print(f"     - 投稿者: {sender_name}")
            print()
    
    def _get_user_name(self, user_id: str) -> str:
        """ユーザーIDから名前を取得"""
        if not user_id:
            return "不明"
        
        user_data = self.db.get(f"users/{user_id}")
        if user_data:
            return user_data.get("name", user_id[:8])
        return user_id[:8]
    
    def run(self):
        """アプリ実行"""
        if not self.login():
            print("❌ ログインに失敗しました。アプリを終了します。")
            return
        
        while True:
            self.show_menu()
            choice = input("> ").strip()
            
            if choice == "0":
                self.list_questions()
            elif choice == "1":
                self.post_question()
            elif choice == "2":
                self.post_answer()
            elif choice == "3":
                self.list_answers()
            elif choice == "9":
                print("\n👋 アプリを終了します。さようなら！")
                break
            else:
                print("❌ 無効な選択です。もう一度入力してください。")


if __name__ == "__main__":
    app = SurveyApp()
    app.run()
