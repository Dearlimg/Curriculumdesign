import requests
import json
import time
from gamestate.game_state import GameState
from algo import evaluation


class QuoridorClient:
    def __init__(self, server_url: str, name: str, password: str):
        self.server_url = server_url
        self.password = password
        self.session = requests.Session()
        self.evaluator = evaluation.Evaluator()
        self.color = None
        self.game_id = None
        self.is_my_turn = False
        self.name = name
        self.userdata = {'name': name, 'pwd': password}

    def join_game(self):
        """加入游戏"""
        try:
            response = requests.post(
                f"{self.server_url}/join_game",
                data=self.userdata
            )
            print(f"[{self.name}] 服务器响应: {response.text}")
            
            if "your color is" in response.text:
                self.color = "black" if "black" in response.text else "white"
                print(f"[{self.name}] 服务器分配的颜色: {self.color}")
            
            return {"success": True, "message": response.text}
        except requests.exceptions.RequestException as e:
            print(f"[{self.name}] 请求失败: {str(e)}")
            return {"success": False, "message": str(e)}

    def get_chessboard(self):
        """获取棋盘状态"""
        try:
            response = requests.get(f"{self.server_url}/get_chessboard")
            data = response.json()
            board_data = data["chessboard"]
            
            if not all(key in board_data for key in ["black_pos", "white_pos", "black_blocks_num", 
                                                   "white_blocks_num", "black_blocks_pos", "white_blocks_pos"]):
                raise ValueError("棋盘数据不完整")
            
            # 确保 blocks_pos 是列表类型
            black_blocks = board_data["black_blocks_pos"] if isinstance(board_data["black_blocks_pos"], list) else []
            white_blocks = board_data["white_blocks_pos"] if isinstance(board_data["white_blocks_pos"], list) else []
            
            print(f"服务器返回的挡板数据: black_blocks={black_blocks}, white_blocks={white_blocks}")
            
            return {
                "success": True,
                "black_pos": board_data["black_pos"],
                "white_pos": board_data["white_pos"],
                "black_blocks_num": board_data["black_blocks_num"],
                "white_blocks_num": board_data["white_blocks_num"],
                "black_blocks_pos": black_blocks,
                "white_blocks_pos": white_blocks,
                "current_player": 1 if self.color == "black" else 2
            }
        except (requests.exceptions.RequestException, json.JSONDecodeError, ValueError) as e:
            print(f"[{self.name}] 获取棋盘状态失败: {str(e)}")
            return {"success": False, "message": str(e)}

    def get_game_status(self):
        """获取游戏状态"""
        try:
            response = requests.get(f"{self.server_url}/get_now_player_and_winner")
            data = response.json()
            return {
                "success": True,
                "current_player": data["now_player"],
                "game_over": bool(data["winner"]),
                "message": f"胜利者是: {data['winner']}" if data["winner"] else None
            }
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            print(f"[{self.name}] 获取游戏状态失败: {str(e)}")
            return {"success": False, "message": str(e)}

    def play_chess(self, move):
        """执行移动"""
        try:
            data = self.userdata.copy()
            data.update(move)
            response = requests.post(f"{self.server_url}/play_chess", data=data)
            print(f"[{self.name}] 服务器响应: {response.text}")
            return {"success": True, "message": response.text}
        except requests.exceptions.RequestException as e:
            print(f"[{self.name}] 执行移动失败: {str(e)}")
            return {"success": False, "message": str(e)}

    def make_move(self, game_state):
        """使用评估器选择并执行移动"""
        try:
            print(f"[{self.name}] 正在计算最优解...")
            move = self.evaluator.get_best_move(game_state, self.color)
            if not move:
                print(f"[{self.name}] 无法找到有效移动")
                return False

            print(f"[{self.name}] 执行移动: {move}")
            result = self.play_chess(move)
            if not result.get("success"):
                print(f"[{self.name}] 执行移动失败: {result.get('message')}")
                return False

            return True
        except Exception as e:
            print(f"[{self.name}] 执行移动时发生错误: {str(e)}")
            return False

    def run(self):
        """运行客户端主循环"""
        # 加入游戏
        join_result = self.join_game()
        if not join_result.get("success"):
            print(f"[{self.name}] 加入游戏失败: {join_result.get('message')}")
            return

        print(f"[{self.name}] 成功加入游戏，等待对手...")
        
        # 等待对手加入
        opponent_joined = False
        while not opponent_joined:
            try:
                # 获取游戏状态
                status = self.get_game_status()
                if not status.get("success"):
                    print(f"[{self.name}] 获取游戏状态失败: {status.get('message')}")
                    time.sleep(1)
                    continue
                
                # 检查是否有对手
                board = self.get_chessboard()
                if not board.get("success"):
                    print(f"[{self.name}] 获取棋盘状态失败: {board.get('message')}")
                    time.sleep(1)
                    continue
                
                # 检查对手是否已经加入
                opponent_color = "white" if self.color == "black" else "black"
                opponent_pos = board.get(f"{opponent_color}_pos")
                if opponent_pos:
                    opponent_joined = True
                    print(f"[{self.name}] 对手已加入游戏，开始游戏！")
                else:
                    print(f"[{self.name}] 等待对手加入...")
                    time.sleep(1)
                    
            except Exception as e:
                print(f"[{self.name}] 等待对手时发生错误: {str(e)}")
                time.sleep(1)

        # 主游戏循环
        while True:
            try:
                # 获取游戏状态
                status = self.get_game_status()
                if not status.get("success"):
                    print(f"[{self.name}] 获取游戏状态失败: {status.get('message')}")
                    time.sleep(1)
                    continue

                # 检查游戏是否结束
                if status.get("game_over"):
                    print(f"[{self.name}] 游戏结束: {status.get('message')}")
                    break

                # 检查是否轮到我们
                if status.get("current_player") != self.name:
                    time.sleep(1)
                    continue

                # 获取棋盘状态
                board = self.get_chessboard()
                if not board.get("success"):
                    print(f"[{self.name}] 获取棋盘状态失败: {board.get('message')}")
                    time.sleep(1)
                    continue

                # 创建游戏状态并执行移动
                game_state = GameState(board)
                if not self.make_move(game_state):
                    time.sleep(1)
                    continue

                # 等待一段时间再继续
                time.sleep(1)

            except Exception as e:
                print(f"[{self.name}] 运行客户端失败: {str(e)}")
                time.sleep(1) 