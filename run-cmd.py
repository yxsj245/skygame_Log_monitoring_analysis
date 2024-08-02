import os
import re
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

class LogFileHandler(FileSystemEventHandler):
    def __init__(self, log_file):
        self.log_file = log_file
        self.file_position = 0  # 记录文件的当前位置
        self.replacement_patterns = {
            r'Received friends\. updated:(\d+) new:(\d+) rewrited:(\d+)': self.translate_friends_received,
            r'\[REMOTE\] Authority revoked from local because of server request': '[更换房主...]由于服务器请求，从本地吊销了权限',
            r'Complying with LevelServer revoke request': '[更换房主...]遵循LevelServer的吊销请求',
            r'\[REMOTE\] Synchronized authority with LevelServer because of election': '[更换房主成功]由于选举，已将权限与LevelServer同步',
            r'Add recent collectible (\d+)': self.translate_add_collectible,
            r'Synced!': '同步完成！',
            r'SetAchievementStats succeeded\.': '重新设置统计值，成功了',
            r'\[REMOTE\] Cleared remote authority because of server request': '[更换房主...]因服务器请求清除了远程权限',
            r'\[REMOTE\] Local elected by server as authority': '[更换房主成功]本地被服务器选为权限(这将说明您当前为房主)',
            r'Players updated: (\d+) total, (\d+) in level': self.translate_players_updated,
            r'Resync friends\.count: (\d+)': self.translate_resync_friends,
            r'move to \[(.*?)\] with (\d+) others\.': self.translate_move,
            r'Queuing move: \[(.*?)\]': self.translate_queuing_move,
            r'Connecting to server: \[(.*?)\]': self.translate_connecting_server,
            r'Connected to game server: \[(.*?)\] event data: (\d+)': self.translate_connected_server,
            r'Recvd PlayerJoined: ([a-f0-9\-]+)': self.translate_player_joined,
            r'Resync friends\.': '重新同步好友。',
            r'.*error.*': '日志当前输出出现错误,游戏会暂停日志信息输出，请重启游戏和脚本。',
        }

    def on_modified(self, event):
        if event.src_path == self.log_file:
            self.process_new_lines()

    def translate_friends_received(self, updated, new, rewrited):
        return f"收到玩家 更新：{updated}，新增：{new}，重写：{rewrited}"

    def translate_add_collectible(self, collectible_id):
        return f"添加最近的使用表情 {collectible_id}"

    def translate_players_updated(self, total, level):
        return f"玩家更新：共[{total}]人，当前房间内[{level}]人"

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
        return None  # 未匹配则返回None

    def process_new_lines(self):
        with open(self.log_file, 'r', encoding='utf-8') as file:
            file.seek(self.file_position)  # 移动到上次记录的位置
            new_lines = file.readlines()
            self.file_position = file.tell()  # 更新文件位置

        if new_lines:
            last_line = new_lines[-1].strip()  # 获取最后一行并去除换行符
            translated_line = self.apply_replacements(last_line)
            if translated_line:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"{timestamp} - {translated_line}")

def main():
    print("游戏只有每次启动进入主菜单才会清空日志内容，请确保游戏已启动并登陆成功再启动监听")
    log_file_path = input("请输入日志文件的路径到具体log文件: ")
    event_handler = LogFileHandler(log_file_path)
    observer = Observer()
    observer.schedule(event_handler, path=os.path.dirname(log_file_path), recursive=False)
    observer.start()
    print("脚本开始监控日志输出")

    try:
        while True:
            time.sleep(0.01)  # 使用0.01秒间隔轮询检查新内容
            event_handler.process_new_lines()  # 轮询检查新内容
    except KeyboardInterrupt:
        observer.stop()

    observer.join()

if __name__ == "__main__":
    main()
