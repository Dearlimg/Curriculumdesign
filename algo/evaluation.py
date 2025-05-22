from gamestate.game_state import wall_single_to_double

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

    def find_best_wall_placement(self, state, player_color, opponent_pos):
        wall_moves = state._generate_all_wall_candidates()
        if not wall_moves:
            return None
        best_wall = None
        best_score = float('-inf')
        seen = set()
        extended_positions = state._get_extended_wall_positions()
        
        for wall_move in wall_moves:
            block = eval(wall_move["block_position"])
            wall_tuple = (block[0][0], block[0][1], block[0][2])
            if wall_tuple in seen:
                continue
            seen.add(wall_tuple)
            
            # 检查扩展后的挡板是否与已有挡板重叠
            x, y, d = wall_tuple
            if d == 1:  # 横向挡板
                if (x, y, 1) in extended_positions or (x, y+1, 1) in extended_positions:
                    continue
            else:  # 纵向挡板
                if (x, y, 0) in extended_positions or (x+1, y, 0) in extended_positions:
                    continue
                    
            score = self.evaluate_wall(state, wall_tuple, player_color, opponent_pos)
            if score > best_score:
                best_score = score
                best_wall = wall_move
                
        if best_score > 0 and best_wall is not None:
            # 如果是白棋，放置时x坐标-1
            if player_color == "black":
                block = eval(best_wall["block_position"])
                new_block = ((block[0][0] - 1, block[0][1], 1), (block[1][0] - 1, block[1][1], 1))
                return {"type": "put_blocks", "block_position": str(new_block)}
            return best_wall
        return None

    def evaluate_wall(self, state, wall, player_color, opponent_pos):
        opponent_color = "white" if player_color == "black" else "black"
        current_pos = tuple(state.state[f"{player_color}_pos"])
        target_row = 9 if player_color == "black" else 1
        opponent_target = 1 if player_color == "black" else 9
        my_path_before = state.find_shortest_path(current_pos, target_row)
        opponent_path_before = state.find_shortest_path(opponent_pos, opponent_target)
        if not my_path_before or not opponent_path_before:
            return float('-inf')
            
        # 模拟放置墙
        wall_move = {"type": "put_blocks", "block_position": str(wall_single_to_double(wall))}
        new_state = state.apply_move(wall_move)
        
        # 检查放置挡板后双方是否都有可达路径
        my_path_after = new_state.find_shortest_path(current_pos, target_row)
        opponent_path_after = new_state.find_shortest_path(opponent_pos, opponent_target)
        if not my_path_after or not opponent_path_after:
            return float('-inf')
            
        my_path_increase = len(my_path_after) - len(my_path_before)
        opponent_path_increase = len(opponent_path_after) - len(opponent_path_before)
        
        # 基础分数：对手路径增加越多越好，自己路径增加越少越好
        score = opponent_path_increase * 3 - my_path_increase
        
        # 优先选择横向挡板
        if wall[2] == 1:  # 横向挡板
            score += 5
            
        # 如果挡板直接阻挡了对手的下一步移动，给予更高分数
        if len(opponent_path_before) >= 2:
            p1, p2 = opponent_path_before[0], opponent_path_before[1]
            if self._is_wall_between_positions(wall, p1, p2):
                score += 10
                
        # 如果挡板放置后对手路径增加超过2步，给予额外分数
        if opponent_path_increase > 2:
            score += 5
            
        # 如果挡板放置后自己的路径增加超过2步，降低分数
        if my_path_increase > 2:
            score -= 10
            
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