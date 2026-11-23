import tkinter as tk
from tkinter import filedialog, ttk
from pathlib import Path


def normalize_raw_path(raw: str) -> str:
    """前後の空白・改行・ダブルクォーテーションを除去する"""
    s = raw.strip()
    if len(s) >= 2 and s.startswith('"') and s.endswith('"'):
        s = s[1:-1].strip()
    return s


def to_escaped_backslash(path_str: str) -> str:
    """JSON文字列用に \\ へ変換"""
    if not path_str:
        return ""
    p = Path(path_str)
    normalized = str(p)
    return normalized.replace("\\", "\\\\")


def to_forward_slash(path_str: str) -> str:
    """JSON文字列用に / へ変換"""
    if not path_str:
        return ""
    p = Path(path_str)
    return p.as_posix()


class JsonPathHelperApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("JSON Path Helper")
        self.geometry("740x360")
        self.minsize(640, 320)

        self.auto_close_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar(value="パスを貼り付けるか、参照・クリップボード取得を使ってください。")

        self.result_vars: dict[str, tk.StringVar] = {
            "file_bs": tk.StringVar(),
            "file_fs": tk.StringVar(),
            "parent_bs": tk.StringVar(),
            "parent_fs": tk.StringVar(),
        }
        self.copy_buttons: list[ttk.Button] = []

        self._build_ui()
        self.input_entry.focus_set()

    def _get_initial_dir(self) -> str:
        """現在の入力パスからダイアログの初期フォルダを推測する"""
        cleaned = normalize_raw_path(self.input_var.get())
        if not cleaned:
            return ""
        p = Path(cleaned)
        if p.exists():
            return str(p if p.is_dir() else p.parent)
        if p.parent.exists():
            return str(p.parent)
        return ""

    def _build_ui(self) -> None:
        pad = {"padx": 10, "pady": 6}

        # 入力エリア
        input_frame = ttk.LabelFrame(self, text="入力パス（生パス・\"パス\"・/パス 対応）")
        input_frame.pack(fill="x", **pad)

        self.input_var = tk.StringVar()
        self.input_var.trace_add("write", lambda *_: self._update_outputs())

        self.input_entry = ttk.Entry(input_frame, textvariable=self.input_var)
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(8, 6), pady=8)

        btn_file = ttk.Button(input_frame, text="ファイル", width=8, command=self.browse_file)
        btn_file.pack(side="left", padx=(0, 4), pady=8)

        btn_folder = ttk.Button(input_frame, text="フォルダ", width=8, command=self.browse_folder)
        btn_folder.pack(side="left", padx=(0, 4), pady=8)

        btn_paste = ttk.Button(input_frame, text="クリップボードから取得", command=self.load_from_clipboard)
        btn_paste.pack(side="left", padx=(0, 4), pady=8)

        btn_clear = ttk.Button(input_frame, text="クリア", width=7, command=self.clear_all)
        btn_clear.pack(side="left", padx=(0, 8), pady=8)

        # 出力エリア
        out_frame = ttk.LabelFrame(self, text="JSON用 変換結果")
        out_frame.pack(fill="both", expand=True, **pad)
        out_frame.columnconfigure(1, weight=1)

        rows = [
            ("対象パス (\\\\)", "file_bs"),
            ("対象パス (/)", "file_fs"),
            ("親フォルダ (\\\\)", "parent_bs"),
            ("親フォルダ (/)", "parent_fs"),
        ]

        for idx, (label_text, key) in enumerate(rows):
            lbl = ttk.Label(out_frame, text=label_text, width=16, anchor="w")
            lbl.grid(row=idx, column=0, padx=(10, 6), pady=6, sticky="w")

            entry = ttk.Entry(out_frame, textvariable=self.result_vars[key], state="readonly")
            entry.grid(row=idx, column=1, padx=4, pady=6, sticky="ew")

            btn = ttk.Button(
                out_frame,
                text="コピー",
                width=10,
                command=lambda k=key, b=idx: self.copy_value(k, b),
            )
            btn.grid(row=idx, column=2, padx=(4, 10), pady=6)
            self.copy_buttons.append(btn)

        # 下部オプション＆ステータス
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(fill="x", padx=10, pady=(0, 8))

        chk = ttk.Checkbutton(
            bottom_frame,
            text="コピー後に自動で閉じる",
            variable=self.auto_close_var,
        )
        chk.pack(side="left")

        status_lbl = ttk.Label(bottom_frame, textvariable=self.status_var, anchor="e")
        status_lbl.pack(side="right", fill="x", expand=True)

    def browse_file(self) -> None:
        init_dir = self._get_initial_dir()
        selected = filedialog.askopenfilename(
            parent=self,
            title="ファイルを選択",
            initialdir=init_dir if init_dir else None,
        )
        if selected:
            self.input_var.set(selected)
            self.status_var.set("ファイルを選択しました。")

    def browse_folder(self) -> None:
        init_dir = self._get_initial_dir()
        selected = filedialog.askdirectory(
            parent=self,
            title="フォルダを選択",
            initialdir=init_dir if init_dir else None,
            mustexist=True,
        )
        if selected:
            self.input_var.set(selected)
            self.status_var.set("フォルダを選択しました。")

    def _update_outputs(self) -> None:
        cleaned = normalize_raw_path(self.input_var.get())
        if not cleaned:
            for v in self.result_vars.values():
                v.set("")
            self.status_var.set("パスを入力してください。")
            return

        p = Path(cleaned)
        parent_str = str(p.parent) if str(p.parent) != cleaned else cleaned

        self.result_vars["file_bs"].set(to_escaped_backslash(cleaned))
        self.result_vars["file_fs"].set(to_forward_slash(cleaned))
        self.result_vars["parent_bs"].set(to_escaped_backslash(parent_str))
        self.result_vars["parent_fs"].set(to_forward_slash(parent_str))
        self.status_var.set("変換完了")

    def load_from_clipboard(self) -> None:
        try:
            clip = self.clipboard_get()
        except tk.TclError:
            self.status_var.set("クリップボードにテキストがありません。")
            return

        cleaned = normalize_raw_path(clip)
        if not cleaned:
            self.status_var.set("クリップボードが空です。")
            return

        self.input_var.set(cleaned)
        self.status_var.set("クリップボードからパスを取得しました。")

    def clear_all(self) -> None:
        self.input_var.set("")
        self.status_var.set("クリアしました。")
        self.input_entry.focus_set()

    def copy_value(self, key: str, btn_index: int) -> None:
        val = self.result_vars[key].get()
        if not val:
            self.status_var.set("コピーするパスがありません。")
            return

        self.clipboard_clear()
        self.clipboard_append(val)
        self.update()

        btn = self.copy_buttons[btn_index]
        orig_text = btn.cget("text")
        btn.configure(text="済！")
        self.status_var.set(f"コピーしました: {val}")

        if self.auto_close_var.get():
            self.after(150, self.destroy)
        else:
            self.after(900, lambda: btn.configure(text=orig_text))


if __name__ == "__main__":
    app = JsonPathHelperApp()
    app.mainloop()