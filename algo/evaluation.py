from gamestate.game_state import wall_single_to_double
import copy

class Evaluator:
    def __init__(self):
        self.directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]  # 右、左、下、上

    def get_best_move(self, state, player_color):
        """获取最佳移动"""
        current_pos = tuple(state.state[f"{player_color}_pos"])
        opponent_color = "white" if player_color == "black" else "black"
        opponent_pos = tuple(state.state[f"{opponent_color}_pos"])
        target_row = 9 if player_color == "black" else 1

        # 1. 如果自己只差一步到终点，直接前进
        my_path = state.find_shortest_path(current_pos, target_row)
        if my_path and len(my_path) == 2:
            print("只差一步到终点，直接前进", my_path[1])
            return {"type": "move_chess", "pos": str(my_path[1])}

        # 2. 获取所有可能的移动
        moves = state.get_possible_moves()
        if not moves:
            return None
        print("所有可能的尝试", moves)

        # 3. 评估是否需要放置挡板
        should_place_wall = False
        remaining_walls = 10 - state.state.get(f"{player_color}_blocks_num", 0)
        if remaining_walls > 0:
            opponent_target = 1 if player_color == "black" else 9
            opponent_path = state.find_shortest_path(opponent_pos, opponent_target)
            if my_path and opponent_path:
                my_distance = len(my_path) - 1
                opponent_distance = len(opponent_path) - 1
                print("双方最短路径:", my_path, opponent_path)
                print("距离差:", my_distance, opponent_distance)
                # 只要对手距离目标更近或很近就考虑放挡板
                if (opponent_distance < my_distance) or (opponent_distance <= 3):
                    should_place_wall = True
        print("是否放置挡板", should_place_wall)

        # 4. 如果决定放置挡板，寻找最佳挡板位置
        if should_place_wall:
            wall_move = self.find_best_wall_placement(state, player_color, opponent_pos)
            if wall_move:
                return wall_move

        # 5. 如果没有放置挡板，选择最佳移动
        best_move = None
        best_score = float('-inf')
        for move in moves:
            if move["type"] == "move_chess":
                score = self.evaluate_move(state, move, player_color)
                if score > best_score:
                    best_score = score
                    best_move = move
        return best_move

    def evaluate_move(self, state, move, player_color):
        target_pos = eval(move["pos"])
        current_pos = tuple(state.state[f"{player_color}_pos"])
        opponent_color = "white" if player_color == "black" else "black"
        opponent_pos = tuple(state.state[f"{opponent_color}_pos"])
        target_row = 9 if player_color == "black" else 1
        distance_after = self.get_distance_to_target(state, target_pos, player_color)
        distance_before = self.get_distance_to_target(state, current_pos, player_color)
        score = (distance_before - distance_after) * 5
        if distance_after < distance_before:
            score += 3
        if (player_color == "black" and target_pos[0] > current_pos[0]) or \
           (player_color == "white" and target_pos[0] < current_pos[0]):
            score += 4
        opponent_distance = abs(target_pos[0] - opponent_pos[0]) + abs(target_pos[1] - opponent_pos[1])
        if opponent_distance > 2:
            score += 2
        return score

    def get_distance_to_target(self, state, pos, player_color):
        target_row = 9 if player_color == "black" else 1
        path = state.find_shortest_path(pos, target_row)
        return len(path) - 1 if path else float('inf')

    def is_valid_wall_placement(self, block, state):
        """检查挡板放置是否有效，禁止交叉挡板"""
        (x1, y1, d1), (x2, y2, d2) = block
        
        # 检查方向是否一致
        if d1 != d2:
            return False
        
        # 检查是否是连续的格子
        if d1 == 1:  # 横向挡板
            if x1 != x2 or y2 != y1 + 1:
                return False
        else:  # 纵向挡板
            if y1 != y2 or x2 != x1 + 1:
                return False
        
        # 检查是否交叉（X型）放置
        all_blocks = state.state["black_blocks_pos"] + state.state["white_blocks_pos"]
        for b in all_blocks:
            if isinstance(b[0], int):
                bx1, by1, bd1 = b
                bx2, by2, bd2 = b
            else:
                (bx1, by1, bd1), (bx2, by2, bd2) = b
            # 检查交叉：横纵交错
            if d1 == 1 and bd1 == 0:
                # 横向挡板与纵向挡板交叉
                if (bx1 == x1 and by1 == y1) or (bx1 == x2 and by1 == y2):
                    return False
            if d1 == 0 and bd1 == 1:
                if (bx1 == x1 and by1 == y1) or (bx1 == x2 and by1 == y2):
                    return False
        
        return True

    def wall_density_penalty(self, block, all_blocks):
        # 统计同一行/列的挡板数量
        (x1, y1, d1), (x2, y2, d2) = block
        count = 0
        for b in all_blocks:
            if isinstance(b[0], int):
                bx1, by1, bd1 = b
                bx2, by2, bd2 = b
            else:
                (bx1, by1, bd1), (bx2, by2, bd2) = b
            if d1 == 1 and bx1 == x1:  # 横向，统计同一行
                count += 1
            elif d1 == 0 and by1 == y1:  # 纵向，统计同一列
                count += 1
        return count

    def find_best_wall_placement(self, state, player_color, opponent_pos):
        wall_moves = state._generate_all_wall_candidates()
        best_wall = None
        max_opponent_path = -1
        min_my_path_increase = float('inf')
        current_pos = tuple(state.state[f"{player_color}_pos"])
        target_row = 9 if player_color == "black" else 1
        opponent_target = 1 if player_color == "black" else 9
        my_path_before = state.find_shortest_path(current_pos, target_row)
        opponent_path_before = state.find_shortest_path(opponent_pos, opponent_target)

        # 第一优先级：自己路径不变，对手路径变长
        for wall_move in wall_moves:
            block = eval(wall_move["block_position"])
            if not self.is_valid_wall_placement(block, state):
                continue
            new_state = state.apply_move({"type": "put_blocks", "block_position": str(block)})
            my_path_after = new_state.find_shortest_path(current_pos, target_row)
            opponent_path_after = new_state.find_shortest_path(opponent_pos, opponent_target)
            if not my_path_after or not opponent_path_after:
                continue  # 不允许堵死
            my_path_increase = len(my_path_after) - len(my_path_before)
            opponent_path_increase = len(opponent_path_after) - len(opponent_path_before)
            if opponent_path_increase > 0 and my_path_increase == 0:
                if len(opponent_path_after) > max_opponent_path:
                    max_opponent_path = len(opponent_path_after)
                    best_wall = wall_move

        if best_wall is not None:
            return best_wall

        # 第二优先级：对手路径变长，自己路径变长最少
        max_opponent_path = -1
        min_my_path_increase = float('inf')
        for wall_move in wall_moves:
            block = eval(wall_move["block_position"])
            if not self.is_valid_wall_placement(block, state):
                continue
            new_state = state.apply_move({"type": "put_blocks", "block_position": str(block)})
            my_path_after = new_state.find_shortest_path(current_pos, target_row)
            opponent_path_after = new_state.find_shortest_path(opponent_pos, opponent_target)
            if not my_path_after or not opponent_path_after:
                continue
            my_path_increase = len(my_path_after) - len(my_path_before)
            opponent_path_increase = len(opponent_path_after) - len(opponent_path_before)
            if opponent_path_increase > 0:
                if (len(opponent_path_after) > max_opponent_path or
                    (len(opponent_path_after) == max_opponent_path and my_path_increase < min_my_path_increase)):
                    max_opponent_path = len(opponent_path_after)
                    min_my_path_increase = my_path_increase
                    best_wall = wall_move

        return best_wall

    def evaluate_wall(self, state, wall, player_color, opponent_pos):
        opponent_color = "white" if player_color == "black" else "black"
        current_pos = tuple(state.state[f"{player_color}_pos"])
        target_row = 9 if player_color == "black" else 1
        opponent_target = 1 if player_color == "black" else 9
        
        # 获取初始路径
        my_path_before = state.find_shortest_path(current_pos, target_row)
        opponent_path_before = state.find_shortest_path(opponent_pos, opponent_target)
        if not my_path_before or not opponent_path_before:
            print(f"挡板 {wall} 导致路径不可达")
            return float('-inf')
            
        # 创建新状态并放置挡板
        new_state = copy.deepcopy(state)
        wall_double = wall_single_to_double(wall)
        
        # 确保正确添加挡板
        if isinstance(new_state.state[f"{player_color}_blocks_pos"], list):
            new_state.state[f"{player_color}_blocks_pos"].append(wall_double)
        else:
            new_state.state[f"{player_color}_blocks_pos"] = [wall_double]
            
        new_state.state[f"{player_color}_blocks_num"] -= 1
        
        # 计算放置挡板后的路径
        my_path_after = new_state.find_shortest_path(current_pos, target_row)
        opponent_path_after = new_state.find_shortest_path(opponent_pos, opponent_target)
        
        # 验证路径是否可达
        if not my_path_after or not opponent_path_after:
            print(f"放置挡板 {wall} 后路径不可达")
            return float('-inf')
        
        # 计算路径长度变化
        my_path_increase = len(my_path_after) - len(my_path_before)
        opponent_path_increase = len(opponent_path_after) - len(opponent_path_before)
        
        print(f"挡板 {wall} 放置后:")
        print(f"  我方路径长度: {len(my_path_before)} -> {len(my_path_after)} (增加 {my_path_increase})")
        print(f"  对手路径长度: {len(opponent_path_before)} -> {len(opponent_path_after)} (增加 {opponent_path_increase})")
        
        # 基础分数计算
        score = opponent_path_increase * 5 - my_path_increase * 2
        print(f"  基础分数: {score} (对手增加*5 - 我方增加*2)")
        
        # 检查是否阻挡了对手的最短路径
        blocks_shortest_path = False
        if len(opponent_path_before) >= 2:
            for i in range(len(opponent_path_before) - 1):
                p1, p2 = opponent_path_before[i], opponent_path_before[i+1]
                if self._is_wall_between_positions(wall, p1, p2):
                    blocks_shortest_path = True
                    break
        
        # 根据是否阻挡最短路径调整分数
        if blocks_shortest_path:
            score += 15
            print(f"  阻挡对手最短路径: +15")
        else:
            score -= 10
            print(f"  未阻挡对手最短路径: -10")
        
        # 横向挡板加分
        if wall[2] == 1:  # 横向挡板
            score += 8
            print(f"  横向挡板加分: +8")
        
        # 根据路径增加程度调整分数
        if opponent_path_increase > 2:
            score += 10
            print(f"  对手路径显著增加: +10")
        if my_path_increase > 2:
            score -= 15
            print(f"  我方路径显著增加: -15")
            
        print(f"  最终分数: {score}")
        return score

    def _is_wall_between_positions(self, wall, pos1, pos2):
        x1, y1 = pos1
        x2, y2 = pos2
        wx, wy, wd = wall
        # 水平移动
        if x1 == x2 and abs(y2 - y1) == 1:
            if wd == 1 and wx == x1 and wy == min(y1, y2):
                return True
        # 垂直移动
        elif y1 == y2 and abs(x2 - x1) == 1:
            if wd == 0 and wy == y1 and wx == min(x1, x2):
                return True
        return False