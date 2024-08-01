import os
import re
from datetime import datetime
import tkinter as tk
from tkinter.scrolledtext import ScrolledText

class LogFileHandler:
    def __init__(self, log_file, text_widget):
        self.log_file = log_file
        self.file_position = 0
        self.text_widget = text_widget
        self.replacement_patterns = {
            r'Received friends\. updated:(\d+) new:(\d+) rewrited:(\d+)': self.translate_friends_received,
            r'\[REMOTE\] Authority revoked from local because of server request': '由于服务器请求，从本地吊销了权限',
            r'Complying with LevelServer revoke request': '遵循LevelServer的吊销请求',
            r'\[REMOTE\] Synchronized authority with LevelServer because of election': 'REMOTE 由于选举，已将权限与[LevelServer]同步',
            r'Add recent collectible (\d+)': self.translate_add_collectible,
            r'Synced!': '同步完成！',
            r'SetAchievementStats succeeded\.': 'SetAchievementStats成功了',
            r'\[REMOTE\] Cleared remote authority because of server request': 'REMOTE 因服务器请求清除了远程权限',
            r'\[REMOTE\] Local elected by server as authority': 'REMOTE 本地被服务器选为权限(这将说明您当前为房主)',
            r'Players updated: (\d+) total, (\d+) in level': self.translate_players_updated,
            r'Resync friends\.count: (\d+)': self.translate_resync_friends,
            r'move to \[(.*?)\] with (\d+) others\.': self.translate_move,
            r'Queuing move: \[(.*?)\]': self.translate_queuing_move,
            r'Connecting to server: \[(.*?)\]': self.translate_connecting_server,
            r'Connected to game server: \[(.*?)\] event data: (\d+)': self.translate_connected_server,
            r'Recvd PlayerJoined: ([a-f0-9\-]+)': self.translate_player_joined,
            r'Resync friends\.': '重新同步好友。',
        }

    def translate_friends_received(self, updated, new, rewrited):
        return f"收到好友信息。更新：{updated}，新增：{new}，重写：{rewrited}"

    def translate_add_collectible(self, collectible_id):
        return f"添加最近的收藏品 {collectible_id}"

    def translate_players_updated(self, total, level):
        return f"玩家更新：共[{total}]人，级别内[{level}]人"

    def translate_resync_friends(self, count):
        return f"重新同步好友数量：{count}"

    def translate_move(self, ip_port, others):
        return f"和其它{others}人一起搬移到[{ip_port}]"

    def translate_queuing_move(self, ip_port):
        return f"排队搬移到 [{ip_port}]"

    def translate_connecting_server(self, ip_port):
        return f"连接到服务器: [{ip_port}]"

    def translate_connected_server(self, ip_port, event_data):
        return f"已连接到游戏服务器: [{ip_port}] 事件数据: {event_data}"

    def translate_player_joined(self, uuid):
        return f"接收到玩家加入：{uuid}"

    def apply_replacements(self, line):
        for pattern, replacer in self.replacement_patterns.items():
            match = re.search(pattern, line)
            if match:
                if callable(replacer):
                    return replacer(*match.groups())
                else:
                    return replacer
        return None

    def process_new_lines(self):
        with open(self.log_file, 'r', encoding='utf-8') as file:
            file.seek(self.file_position)
            new_lines = file.readlines()
            self.file_position = file.tell()

        if new_lines:
            last_line = new_lines[-1].strip()
            translated_line = self.apply_replacements(last_line)
            if translated_line:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.text_widget.insert(tk.END, f"{timestamp} - {translated_line}\n")
                self.text_widget.see(tk.END)  # 自动滚动到最后

def main():
    log_file_path = input("请输入日志文件的路径: ")

    root = tk.Tk()
    root.title("日志监控器")
    root.attributes("-topmost", True)  # 设置窗口始终在最前面

    text_widget = ScrolledText(root, wrap=tk.WORD, width=80, height=3)  # 设置显示三行
    text_widget.pack(fill=tk.BOTH, expand=True)

    log_handler = LogFileHandler(log_file_path, text_widget)

    def poll_log_file():
        log_handler.process_new_lines()
        root.after(10, poll_log_file)  # 每1秒检查一次日志文件

    poll_log_file()  # 启动轮询

    def on_closing():
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    root.mainloop()

if __name__ == "__main__":
    main()
