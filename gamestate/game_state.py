from typing import Tuple, List, Dict
import copy
from collections import deque

def wall_single_to_double(wall):
    x, y, d = wall
    if d == 1:  # 横向
        return ((x, y, 1), (x, y+1, 1))
    else:       # 纵向
        return ((x, y, 0), (x+1, y, 0))

class GameState:
    def __init__(self, state: Dict):
        self.state = copy.deepcopy(state)
        self.player_color = "black" if self.state["current_player"] == 1 else "white"
        self.opponent_color = "white" if self.player_color == "black" else "black"
        self._blocks_cache = None  # 添加缓存

    def get_possible_moves(self) -> List[Dict]:
        moves = []
        pos = tuple(self.state[f"{self.player_color}_pos"])
        target_row = 9 if self.player_color == "black" else 1
        walls_left = self.state[f"{self.player_color}_blocks_num"]

        # 生成棋子移动
        moves.extend(self._generate_chess_moves(pos, target_row))

        # 生成挡板移动
        if walls_left > 0:
            moves.extend(self._generate_wall_moves(pos, target_row))
        print("get_possible_moves",moves)
        return self._filter_duplicate_moves(moves)

    def _generate_chess_moves(self, pos: Tuple[int, int], target_row: int) -> List[Dict]:
        moves = []
        directions = [(1,0), (0,-1), (0,1), (-1,0)]
        opponent_pos = tuple(self.state[f"{self.opponent_color}_pos"])

        for dx, dy in directions:
            new_pos = (pos[0]+dx, pos[1]+dy)
            if not self._is_valid_position(new_pos):
                continue

            if not self._is_blocked(pos, new_pos):
                moves.append({"type": "move_chess", "pos": f"{new_pos}"})

                # 检查跳跃
                if new_pos == opponent_pos:
                    jump_pos = (new_pos[0]+dx, new_pos[1]+dy)
                    # 跳跃时，必须两步都不被挡板阻挡
                    if (self._is_valid_position(jump_pos)
                        and not self._is_blocked(pos, new_pos)
                        and not self._is_blocked(new_pos, jump_pos)):
                        moves.append({"type": "move_chess", "pos": f"{jump_pos}"})
        return moves

    def _generate_wall_moves(self, pos: Tuple[int, int], target_row: int) -> List[Dict]:
        moves = []
        all_blocks = self._get_all_blocks()
        for x in range(1, 9):
            for y in range(1, 9):
                # 横向挡板（d=1）
                if y < 9:
                    wall = (x, y, 1)
                    if self._is_valid_wall(wall, all_blocks):
                        moves.append({"type": "put_blocks", "block_position": str(wall_single_to_double(wall))})
                # 纵向挡板（d=0）
                if x < 9:
                    wall = (x, y, 0)
                    if self._is_valid_wall(wall, all_blocks):
                        moves.append({"type": "put_blocks", "block_position": str(wall_single_to_double(wall))})
        return moves

    def _get_blocking_walls(self, path: List[Tuple[int, int]], pos: Tuple[int, int], is_defensive=False) -> List[Dict]:
        walls = []
        if len(path) < 2: return walls

        for i in range(len(path)-1):
            p1, p2 = path[i], path[i+1]
            if p1[0] == p2[0]:  # 水平移动
                y = min(p1[1], p2[1])
                wall = (p1[0], y, 0)  # 纵向挡板
                if self._is_valid_wall(wall):
                    walls.append({"type": "put_blocks", "block_position": str(wall_single_to_double(wall))})
            else:  # 垂直移动
                x = min(p1[0], p2[0])
                wall = (x, p1[1], 1)  # 横向挡板
                if self._is_valid_wall(wall):
                    walls.append({"type": "put_blocks", "block_position": str(wall_single_to_double(wall))})

        return walls

    def _generate_all_wall_candidates(self) -> List[Dict]:
        walls = []
        all_blocks = self._get_all_blocks()
        for x in range(1, 9):
            for y in range(1, 9):
                # 横向挡板（d=1）
                if y < 9:
                    wall = (x, y, 1)
                    double_wall = wall_single_to_double(wall)
                    if self._is_valid_wall(wall, all_blocks):
                        walls.append({"type": "put_blocks", "block_position": str(double_wall)})
                # 纵向挡板（d=0）
                if x < 9:
                    wall = (x, y, 0)
                    double_wall = wall_single_to_double(wall)
                    if self._is_valid_wall(wall, all_blocks):
                        walls.append({"type": "put_blocks", "block_position": str(double_wall)})
        return walls

    def _is_valid_position(self, pos: Tuple[int, int]) -> bool:
        return 1 <= pos[0] <= 9 and 1 <= pos[1] <= 9

    def _get_all_blocks(self) -> List[List[int]]:
        all_blocks = []
        for block in self.state["black_blocks_pos"] + self.state["white_blocks_pos"]:
            if isinstance(block[0], int):  # 单格
                all_blocks.append(list(block))
            else:  # 扩展挡板
                for b in block:
                    all_blocks.append(list(b))
        return all_blocks

    def _get_extended_wall_positions(self) -> set:
        extended_positions = set()
        # extended_positions=set(self.state["black_blocks_pos"] + self.state["white_blocks_pos"])

        for block in self.state["black_blocks_pos"] + self.state["white_blocks_pos"]:
            if isinstance(block[0], int):  # 单格
                extended_positions.add(tuple(block))
            else:  # 扩展挡板
                extended_positions.add(tuple(block[0]))
                extended_positions.add(tuple(block[1]))
        return extended_positions

    def _is_blocked(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> bool:
        x1, y1 = from_pos
        x2, y2 = to_pos
        all_blocks = self._get_all_blocks()  # 已统一为列表格式
        # 纵向移动
        if abs(x2 - x1) == 1 and y1 == y2:
            min_x = min(x1, x2)
            if [min_x, y1, 1] in all_blocks:
                return True
        # 横向移动
        if abs(y2 - y1) == 1 and x1 == x2:
            min_y = min(y1, y2)
            if [x1, min_y, 0] in all_blocks:
                return True
        return False

    def _is_valid_wall(self, wall: Tuple, all_blocks: List = None) -> bool:
        x, y, d = wall
        double_wall = wall_single_to_double(wall)
        
        # 检查是否已存在
        all_double_blocks = self.state["black_blocks_pos"] + self.state["white_blocks_pos"]
        if double_wall in all_double_blocks:
            return False
        
        # 检查边界
        if d == 0:  # 纵向挡板
            if not (1 <= x <= 8 and 1 <= y <= 9):
                return False
        else:  # 横向挡板
            if not (1 <= x <= 9 and 1 <= y <= 8):
                return False
            
        if all_blocks is None:
            all_blocks = self._get_all_blocks()
        
        # 检查扩展后的挡板是否与已有挡板重叠
        extended_positions = self._get_extended_wall_positions()
        if d == 1:  # 横向挡板
            if (x, y, 1) in extended_positions or (x, y+1, 1) in extended_positions:
                return False
        else:  # 纵向挡板
            if (x, y, 0) in extended_positions or (x+1, y, 0) in extended_positions:
                return False
            
        # 检查是否形成死局
        new_state = copy.deepcopy(self.state)
        new_state[f"{self.player_color}_blocks_pos"] = new_state[f"{self.player_color}_blocks_pos"] + [double_wall]
        new_game_state = GameState(new_state)
        player_ok = len(new_game_state.find_shortest_path(tuple(self.state[f"{self.player_color}_pos"]), 9 if self.player_color == "black" else 1)) > 0
        opponent_ok = len(new_game_state.find_shortest_path(tuple(self.state[f"{self.opponent_color}_pos"]), 9 if self.opponent_color == "black" else 1)) > 0
        return player_ok and opponent_ok

    def _filter_duplicate_moves(self, moves: List[Dict]) -> List[Dict]:
        seen = set()
        return [m for m in moves if str(m) not in seen and not seen.add(str(m))]

    def is_terminal(self) -> bool:
        return (self.state["black_pos"][0] == 9 or
                self.state["white_pos"][0] == 1)


    # bfs
    def find_shortest_path(self, start: Tuple[int, int], target_row: int) -> List[Tuple[int, int]]:
        queue = deque([(start, [start])])
        visited = set([start])

        while queue:
            current, path = queue.popleft()
            if current[0] == target_row:
                return path
            for dx, dy in [(0,-1),(0,1),(1,0),(-1,0)]:
            # for dx, dy in [(0,1),(0,-1),(1,0),(-1,0)]:
                new_pos = (current[0]+dx, current[1]+dy)
                if self._is_valid_position(new_pos) and new_pos not in visited and not self._is_blocked(current, new_pos):
                    visited.add(new_pos)
                    queue.append((new_pos, path + [new_pos]))
        return []

    def find_all_shortest_paths(self, start: Tuple[int, int], target_row: int) -> List[List[Tuple[int, int]]]:
        """查找所有可能的最短路径"""
        # 首先找到一条最短路径来确定最短长度
        first_path = self.find_shortest_path(start, target_row)
        if not first_path:
            return []
        shortest_length = len(first_path)
        
        # 使用BFS找到所有最短路径
        all_paths = []
        queue = deque([(start, [start])])
        visited = set([start])
        
        while queue:
            current, path = queue.popleft()
            
            # 如果当前路径长度已经超过最短长度，跳过
            if len(path) > shortest_length:
                continue
                
            if current[0] == target_row:
                if len(path) == shortest_length:
                    all_paths.append(path)
                continue
                
            # 按照右、左、下、上的顺序探索
            for dx, dy in [(0,1),(0,-1),(1,0),(-1,0)]:
                new_pos = (current[0]+dx, current[1]+dy)
                if (self._is_valid_position(new_pos) and 
                    new_pos not in visited and 
                    not self._is_blocked(current, new_pos)):
                    visited.add(new_pos)
                    queue.append((new_pos, path + [new_pos]))
        
        return all_paths

    def apply_move(self, move: Dict) -> 'GameState':
        new_state = copy.deepcopy(self.state)
        if move["type"] == "move_chess":
            new_state[f"{self.player_color}_pos"] = eval(move["pos"])
        else:  # put_blocks
            block = eval(move["block_position"])
            new_state[f"{self.player_color}_blocks_pos"].append(block)
            new_state[f"{self.player_color}_blocks_num"] -= 1
        new_state["current_player"] = 2 if new_state["current_player"] == 1 else 1
        return GameState(new_state)

    def is_valid_move(self, state, current_pos, target_pos):
        if not (1 <= target_pos[0] <= 9 and 1 <= target_pos[1] <= 9):
            return False

        all_blocks = [list(b) for b in state._get_all_blocks()]
        x1, y1 = current_pos
        x2, y2 = target_pos

        # 纵向移动
        if abs(x2 - x1) == 1 and y1 == y2:
            if x2 < x1:  # 向上
                if [x2, y1, 1] in all_blocks:
                    return False
            else:  # 向下
                if [x1, y1, 1] in all_blocks:
                    return False

        # 横向移动
        if abs(y2 - y1) == 1 and x1 == x2:
            if y2 < y1:  # 向左
                if [x1, y2, 0] in all_blocks:
                    return False
            else:  # 向右
                if [x1, y1, 0] in all_blocks:
                    return False

        return True

    def _is_wall_between_positions(self, wall, pos1, pos2):
        x1, y1 = pos1
        x2, y2 = pos2
        (wx1, wy1, wd1), (wx2, wy2, wd2) = wall
        # 水平移动
        if x1 == x2 and abs(y2 - y1) == 1:
            if wd1 == 0 and wx1 == x1 and wy1 == min(y1, y2):
                return True
        # 垂直移动
        elif y1 == y2 and abs(x2 - x1) == 1:
            if wd1 == 1 and wy1 == y1 and wx1 == min(x1, x2):
                return True
        return False 