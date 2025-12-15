import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
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


class LoginFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # UI Elements
        frame = ttk.LabelFrame(self, text="ログイン", padding="20")
        frame.place(relx=0.5, rely=0.5, anchor="center")
        
        ttk.Label(frame, text="Email:").grid(row=0, column=0, sticky="w", pady=5)
        self.email_entry = ttk.Entry(frame, width=30)
        self.email_entry.grid(row=0, column=1, pady=5)
        self.email_entry.insert(0, USER_EMAIL if USER_EMAIL else "")
        
        ttk.Label(frame, text="Password:").grid(row=1, column=0, sticky="w", pady=5)
        self.pass_entry = ttk.Entry(frame, show="*", width=30)
        self.pass_entry.grid(row=1, column=1, pady=5)
        self.pass_entry.insert(0, USER_PASSWORD if USER_PASSWORD else "")
        
        ttk.Button(frame, text="ログイン", command=self.login).grid(row=2, column=0, columnspan=2, pady=20, sticky="ew")

    def login(self):
        email = self.email_entry.get().strip()
        password = self.pass_entry.get().strip()
        
        if not email or not password:
            messagebox.showwarning("入力エラー", "メールアドレスとパスワードを入力してください。")
            return

        if self.controller.auth.sign_in(email, password):
            self.controller.db = RealtimeDB(self.controller.auth)
            self.controller._setup_user_profile()
            self.controller.show_main_frame()
        else:
            messagebox.showerror("ログイン失敗", "ログインに失敗しました。メールアドレスまたはパスワードを確認してください。")


class MainFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Header
        header = ttk.Frame(self, padding="10")
        header.pack(fill="x")
        
        ttk.Label(header, text="📋 アンケート一覧", font=("Helvetica", 16, "bold")).pack(side="left")
        ttk.Button(header, text="終了", command=self.controller.quit).pack(side="right", padx=5)
        ttk.Button(header, text="✏️ 投稿", command=self.open_post_dialog).pack(side="right")
        
        # List Area
        self.tree = ttk.Treeview(self, columns=("title", "author"), show="headings", selectmode="browse")
        self.tree.heading("title", text="タイトル")
        self.tree.heading("author", text="投稿者")
        self.tree.column("title", width=400)
        self.tree.column("author", width=150)
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tree.bind("<Double-1>", self.on_item_double_click)
        
        # Data storage
        self.questions_map = {} # item_id -> question_id
        self.questions_data = {} # question_id -> data
        
        self.load_questions()
        
    def load_questions(self):
        # Clear list
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.questions_map.clear()
        self.questions_data.clear()
        
        # Fetch
        questions = self.controller.db.get("questions")
        if not questions:
            return

        for qid, q_data in questions.items():
            author_id = q_data.get("sender", "")
            author_name = self.controller.get_user_name(author_id)
            title = q_data.get("name", "タイトルなし")
            
            item_id = self.tree.insert("", "end", values=(title, author_name))
            self.questions_map[item_id] = qid
            self.questions_data[qid] = q_data

    def open_post_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("新規アンケート投稿")
        dialog.geometry("400x300")
        
        ttk.Label(dialog, text="タイトル:").pack(anchor="w", padx=10, pady=5)
        title_entry = ttk.Entry(dialog, width=40)
        title_entry.pack(padx=10, fill="x")
        
        ttk.Label(dialog, text="内容:").pack(anchor="w", padx=10, pady=5)
        body_text = tk.Text(dialog, height=8)
        body_text.pack(padx=10, fill="both", expand=True)
        
        def submit():
            title = title_entry.get().strip()
            body = body_text.get("1.0", "end").strip()
            if not title or not body:
                messagebox.showwarning("入力エラー", "タイトルと内容を入力してください。")
                return
            
            data = {
                "name": title,
                "body": body,
                "sender": self.controller.auth.user_id
            }
            if self.controller.db.post("questions", data):
                messagebox.showinfo("成功", "アンケートを投稿しました！")
                dialog.destroy()
                self.load_questions()
            else:
                messagebox.showerror("エラー", "投稿に失敗しました。")
                
        ttk.Button(dialog, text="投稿する", command=submit).pack(pady=10)

    def on_item_double_click(self, event):
        selected_item = self.tree.selection()
        if not selected_item:
            return
        
        item_id = selected_item[0]
        qid = self.questions_map.get(item_id)
        if qid:
            q_data = self.questions_data.get(qid)
            self.controller.show_detail_frame(qid, q_data)


class DetailFrame(ttk.Frame):
    def __init__(self, parent, controller, question_id, question_data):
        super().__init__(parent)
        self.controller = controller
        self.question_id = question_id
        self.question_data = question_data
        
        # Header with Back button
        header = ttk.Frame(self, padding="5")
        header.pack(fill="x")
        ttk.Button(header, text="< 戻る", command=self.go_back).pack(side="left")
        
        # Question Content
        content_frame = ttk.LabelFrame(self, text="アンケート内容", padding="15")
        content_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(content_frame, text=question_data.get("name", ""), font=("Helvetica", 14, "bold")).pack(anchor="w")
        ttk.Label(content_frame, text=f"投稿者: {self.controller.get_user_name(question_data.get('sender', ''))}", foreground="gray").pack(anchor="w")
        
        body_txt = tk.Text(content_frame, height=5, wrap="word", relief="flat", bg="#f0f0f0")
        body_txt.insert("1.0", question_data.get("body", ""))
        body_txt.configure(state="disabled")
        body_txt.pack(fill="x", pady=10)
        
        # Answers List
        ttk.Label(self, text="💬 回答一覧", font=("Helvetica", 12)).pack(anchor="w", padx=10, pady=(10, 0))
        
        list_frame = ttk.Frame(self)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.answers_text = tk.Text(list_frame, state="disabled", wrap="word")
        scrollbar = ttk.Scrollbar(list_frame, command=self.answers_text.yview)
        self.answers_text.configure(yscrollcommand=scrollbar.set)
        
        self.answers_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.load_answers()
        
        # Post Answer Area
        post_frame = ttk.Frame(self, padding="10")
        post_frame.pack(fill="x")
        
        ttk.Label(post_frame, text="回答を投稿:").pack(anchor="w")
        self.new_answer_entry = ttk.Entry(post_frame)
        self.new_answer_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(post_frame, text="送信", command=self.submit_answer).pack(side="right")
        
    def go_back(self):
        self.controller.show_main_frame()
        
    def load_answers(self):
        self.answers_text.configure(state="normal")
        self.answers_text.delete("1.0", "end")
        
        answers = self.controller.db.get(f"answers/{self.question_id}")
        if not answers:
            self.answers_text.insert("end", "(まだ回答はありません)\n")
        else:
            for aid, a_data in answers.items():
                name = self.controller.get_user_name(a_data.get("sender", ""))
                body = a_data.get("body", "")
                self.answers_text.insert("end", f"👤 {name}:\n{body}\n\n" + "-"*40 + "\n\n")
        
        self.answers_text.configure(state="disabled")
        
    def submit_answer(self):
        body = self.new_answer_entry.get().strip()
        if not body:
            return
            
        data = {
            "target": self.question_id,
            "body": body,
            "sender": self.controller.auth.user_id
        }
        
        if self.controller.db.post(f"answers/{self.question_id}", data):
            self.new_answer_entry.delete(0, "end")
            self.load_answers()
            messagebox.showinfo("成功", "回答を送信しました！")
        else:
            messagebox.showerror("エラー", "送信に失敗しました。")


class SurveyGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("アンケートアプリ (GUI)")
        self.geometry("400x300")
        
        self.auth = FirebaseAuth()
        self.db = None
        self.user_cache = {}  # user_id -> name
        
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        
        self.container = ttk.Frame(self)
        self.container.pack(fill="both", expand=True)
        
        self.show_login_frame()
        
    def show_login_frame(self):
        self._clear_frame()
        LoginFrame(self.container, self).pack(fill="both", expand=True)

    def show_main_frame(self):
        self._clear_frame()
        self.geometry("600x700")
        MainFrame(self.container, self).pack(fill="both", expand=True)

    def show_detail_frame(self, qid, q_data):
        self._clear_frame()
        DetailFrame(self.container, self, qid, q_data).pack(fill="both", expand=True)

    def _clear_frame(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    def _setup_user_profile(self):
        """ログイン後のユーザーチェック"""
        user_data = self.db.get(f"users/{self.auth.user_id}")
        if not user_data or not user_data.get("name"):
            # 名前登録が必要
            new_name = simpledialog.askstring("プロフィール設定", "表示名を入力してください:")
            if not new_name:
                new_name = self.auth.email.split("@")[0]
            
            profile = {
                "name": new_name,
                "email": self.auth.email,
                "id": self.auth.user_id
            }
            self.db.put(f"users/{self.auth.user_id}", profile)
            self.user_cache[self.auth.user_id] = new_name
        else:
            self.user_cache[self.auth.user_id] = user_data["name"]

    def get_user_name(self, user_id):
        if user_id in self.user_cache:
            return self.user_cache[user_id]
        
        if not self.db: return "不明"
        
        # Fetch and cache
        u_data = self.db.get(f"users/{user_id}")
        if u_data:
            name = u_data.get("name", "名無し")
            self.user_cache[user_id] = name
            return name
        return "不明"


if __name__ == "__main__":
    app = SurveyGUI()
    app.mainloop()
