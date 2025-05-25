from gamestate.game_state import wall_single_to_double
import copy

class Evaluator:
    def __init__(self):
        self.directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]  # 右、左、下、上
        self.move_count = 0  # 添加操作计数器
        self.last_positions = []  # 记录最近的位置
        self.max_history = 3  # 记录最近3步的位置

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
            self.move_count += 1
            self.update_position_history(current_pos)
            return {"type": "move_chess", "pos": str(my_path[1]), "move_again": "False"}

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
                
                # 判断是否应该放置挡板
                game_progress = max(my_distance, opponent_distance)
                distance_diff = abs(my_distance - opponent_distance)
                
                # 检查是否在游戏初期（前一步）
                is_early_game = self.move_count < 1
                
                if not is_early_game:  # 只有在非游戏初期才考虑放置挡板
                    # 计算游戏阶段
                    is_mid_game = game_progress >= 4  # 游戏进行到中期
                    is_late_game = game_progress >= 6  # 游戏进行到后期
                    
                    # 1. 对手领先较多（3步以上）或即将到达终点
                    if (opponent_distance < my_distance) or (opponent_distance <= 5 and is_mid_game):
                        should_place_wall = True
                        print("决定放置挡板：对手领先较多或即将到达终点")
                    
                    # 2. 游戏中期，双方步数接近，且剩余挡板充足
                    elif is_mid_game and distance_diff <= 2 and remaining_walls >= 4:
                        should_place_wall = True
                        print("决定放置挡板：游戏中期，双方步数接近")
                    
                    # 3. 游戏后期，对手即将到达终点
                    elif is_late_game and opponent_distance <= 6 and remaining_walls >= 0:
                        should_place_wall = True
                        print("决定放置挡板：游戏后期，对手即将到达终点")
                    
                    # 4. 自己领先较多，且剩余挡板充足
                    elif my_distance < opponent_distance - 3 and remaining_walls >= 4:
                        should_place_wall = True
                        print("决定放置挡板：自己领先较多，且剩余挡板充足")
                    
                    # 5. 检查是否有能显著增加路径差值的挡板位置
                    if not should_place_wall and remaining_walls >= 2:
                        wall_moves = state._generate_all_wall_candidates()
                        for wall_move in wall_moves:
                            try:
                                block = eval(wall_move["block_position"])
                                if not isinstance(block, tuple) or len(block) != 2:
                                    continue
                                    
                                if not self.is_valid_wall_placement(block, state):
                                    continue
                                    
                                new_state = state.apply_move({"type": "put_blocks", "block_position": str(block)})
                                
                                # 获取放置挡板后的最短路径
                                my_path_after = new_state.find_shortest_path(current_pos, target_row)
                                opponent_path_after = new_state.find_shortest_path(opponent_pos, opponent_target)
                                
                                if my_path_after and opponent_path_after:
                                    my_distance_after = len(my_path_after) - 1
                                    opponent_distance_after = len(opponent_path_after) - 1
                                    
                                    # 计算路径差值的变化
                                    distance_diff_before = abs(my_distance - opponent_distance)
                                    distance_diff_after = abs(my_distance_after - opponent_distance_after)
                                    
                                    # 如果路径差值显著增加（>=3）
                                    if distance_diff_after - distance_diff_before >= 3:
                                        should_place_wall = True
                                        print(f"决定放置挡板：可以显著增加路径差值（{distance_diff_before} -> {distance_diff_after}）")
                                        break
                            except Exception as e:
                                print(f"处理挡板时出错: {str(e)}")
                                continue
                    
                    # 6. 确保不会过度使用挡板
                    if should_place_wall and remaining_walls < 2:
                        print("剩余挡板不足，优先移动棋子")
                        should_place_wall = False
                else:
                    print(f"游戏初期（第{self.move_count + 1}步），优先移动棋子")
        print("是否放置挡板", should_place_wall)

        # 4. 如果决定放置挡板，寻找最佳挡板位置
        if should_place_wall:
            wall_move = self.find_best_wall_placement(state, player_color, opponent_pos)
            if wall_move:
                self.move_count += 1
                self.update_position_history(current_pos)
                wall_move["move_again"] = "False"
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
        
        if best_move:
            self.move_count += 1
            self.update_position_history(current_pos)
            best_move["move_again"] = "False"
        return best_move

    def update_position_history(self, pos):
        """更新位置历史"""
        self.last_positions.append(pos)
        if len(self.last_positions) > self.max_history:
            self.last_positions.pop(0)

    def evaluate_move(self, state, move, player_color):
        """评估移动的分数"""
        target_pos = eval(move["pos"])
        current_pos = tuple(state.state[f"{player_color}_pos"])
        opponent_color = "white" if player_color == "black" else "black"
        opponent_pos = tuple(state.state[f"{opponent_color}_pos"])
        target_row = 9 if player_color == "black" else 1

        # 检查移动是否有效
        if not self.is_valid_move(state, current_pos, target_pos):
            return float('-inf')

        # 1. 基础距离评估
        distance_after = self.get_distance_to_target(state, target_pos, player_color)
        distance_before = self.get_distance_to_target(state, current_pos, player_color)
        score = (distance_before - distance_after) * 5
        if distance_after < distance_before:
            score += 3

        # 2. 方向评估
        if (player_color == "black" and target_pos[0] > current_pos[0]) or \
           (player_color == "white" and target_pos[0] < current_pos[0]):
            score += 4

        # 3. 与对手距离评估
        opponent_distance = abs(target_pos[0] - opponent_pos[0]) + abs(target_pos[1] - opponent_pos[1])
        if opponent_distance > 2:
            score += 2

        return score

    def is_valid_move(self, state, current_pos, target_pos):
        """检查移动是否有效"""
        # 检查是否在棋盘范围内
        if not (1 <= target_pos[0] <= 9 and 1 <= target_pos[1] <= 9):
            return False

        # 检查是否是相邻格子
        dx = abs(target_pos[0] - current_pos[0])
        dy = abs(target_pos[1] - current_pos[1])
        if dx + dy != 1:
            return False

        # 检查是否有挡板阻挡
        all_blocks = state.state["black_blocks_pos"] + state.state["white_blocks_pos"]
        for block in all_blocks:
            if isinstance(block[0], int):
                bx1, by1, bd1 = block
                bx2, by2, bd2 = block
            else:
                (bx1, by1, bd1), (bx2, by2, bd2) = block

            # 检查横向挡板
            if bd1 == 1:  # 横向挡板
                if current_pos[0] == target_pos[0] == bx1:
                    if (current_pos[1] == by1 and target_pos[1] == by2) or \
                       (current_pos[1] == by2 and target_pos[1] == by1):
                        return False

            # 检查纵向挡板
            if bd1 == 0:  # 纵向挡板
                if current_pos[1] == target_pos[1] == by1:
                    if (current_pos[0] == bx1 and target_pos[0] == bx2) or \
                       (current_pos[0] == bx2 and target_pos[0] == bx1):
                        return False

        return True

    def get_distance_to_target(self, state, pos, player_color):
        """获取到目标的距离"""
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
        
        # 获取所有可能的最短路径
        my_paths_before = state.find_all_shortest_paths(current_pos, target_row)
        opponent_paths_before = state.find_all_shortest_paths(opponent_pos, opponent_target)
        
        if not my_paths_before or not opponent_paths_before:
            return None
            
        my_path_before = my_paths_before[0]  # 使用任意一条最短路径作为参考
        opponent_path_before = opponent_paths_before[0]

        # 最高级策略：对手路径增加远大于我方路径增加（差值>=3）
        best_advantage_wall = None
        max_path_difference = -1
        max_blocked_paths = 0  # 记录能阻挡的最短路径数量
        
        for wall_move in wall_moves:
            try:
                block = eval(wall_move["block_position"])
                if not isinstance(block, tuple) or len(block) != 2:
                    continue
                    
                if not self.is_valid_wall_placement(block, state):
                    continue
                    
                new_state = state.apply_move({"type": "put_blocks", "block_position": str(block)})
                
                # 获取放置挡板后的所有最短路径
                my_paths_after = new_state.find_all_shortest_paths(current_pos, target_row)
                opponent_paths_after = new_state.find_all_shortest_paths(opponent_pos, opponent_target)
                
                if not my_paths_after or not opponent_paths_after:
                    continue
                
                # 计算路径变化（使用最短路径的长度）
                my_path_increase = len(my_paths_after[0]) - len(my_path_before)
                opponent_path_increase = len(opponent_paths_after[0]) - len(opponent_path_before)
                path_difference = opponent_path_increase - my_path_increase
                
                # 计算这个挡板能阻挡多少条原始最短路径
                blocked_paths = 0
                for path in opponent_paths_before:
                    if self._is_path_blocked_by_wall(path, block):
                        blocked_paths += 1
                
                # 如果对手路径增加比我们多3步以上，记录这个位置
                if path_difference >= 3:
                    print(f"找到优势位置：对手增加{opponent_path_increase}步，我方增加{my_path_increase}步，差值{path_difference}，阻挡{blocked_paths}条最短路径")
                    
                    # 优先选择能阻挡更多最短路径的位置
                    if blocked_paths > max_blocked_paths or \
                       (blocked_paths == max_blocked_paths and path_difference > max_path_difference):
                        max_blocked_paths = blocked_paths
                        max_path_difference = path_difference
                        best_advantage_wall = wall_move
            except Exception as e:
                print(f"处理挡板时出错: {str(e)}")
                continue

        # 如果找到了优势位置，直接返回
        if best_advantage_wall is not None:
            print(f"选择最高级策略：最大路径差值{max_path_difference}，阻挡{max_blocked_paths}条最短路径")
            return best_advantage_wall

        # 第一优先级：自己路径不变，对手路径变长
        for wall_move in wall_moves:
            try:
                block = eval(wall_move["block_position"])
                if not isinstance(block, tuple) or len(block) != 2:
                    continue
                    
                if not self.is_valid_wall_placement(block, state):
                    continue
                    
                new_state = state.apply_move({"type": "put_blocks", "block_position": str(block)})
                my_paths_after = new_state.find_all_shortest_paths(current_pos, target_row)
                opponent_paths_after = new_state.find_all_shortest_paths(opponent_pos, opponent_target)
                
                if not my_paths_after or not opponent_paths_after:
                    continue
                
                my_path_increase = len(my_paths_after[0]) - len(my_path_before)
                opponent_path_increase = len(opponent_paths_after[0]) - len(opponent_path_before)
                
                if opponent_path_increase > 0 and my_path_increase == 0:
                    # 计算这个挡板能阻挡多少条原始最短路径
                    blocked_paths = 0
                    for path in opponent_paths_before:
                        if self._is_path_blocked_by_wall(path, block):
                            blocked_paths += 1
                            
                    if blocked_paths > max_blocked_paths or \
                       (blocked_paths == max_blocked_paths and len(opponent_paths_after[0]) > max_opponent_path):
                        max_blocked_paths = blocked_paths
                        max_opponent_path = len(opponent_paths_after[0])
                        best_wall = wall_move
            except Exception as e:
                print(f"处理挡板时出错: {str(e)}")
                continue

        if best_wall is not None:
            return best_wall

        # 第二优先级：对手路径变长，自己路径变长最少
        max_opponent_path = -1
        min_my_path_increase = float('inf')
        max_blocked_paths = 0
        
        for wall_move in wall_moves:
            try:
                block = eval(wall_move["block_position"])
                if not isinstance(block, tuple) or len(block) != 2:
                    continue
                    
                if not self.is_valid_wall_placement(block, state):
                    continue
                    
                new_state = state.apply_move({"type": "put_blocks", "block_position": str(block)})
                my_paths_after = new_state.find_all_shortest_paths(current_pos, target_row)
                opponent_paths_after = new_state.find_all_shortest_paths(opponent_pos, opponent_target)
                
                if not my_paths_after or not opponent_paths_after:
                    continue
                
                my_path_increase = len(my_paths_after[0]) - len(my_path_before)
                opponent_path_increase = len(opponent_paths_after[0]) - len(opponent_path_before)
                
                if opponent_path_increase > 0:
                    # 计算这个挡板能阻挡多少条原始最短路径
                    blocked_paths = 0
                    for path in opponent_paths_before:
                        if self._is_path_blocked_by_wall(path, block):
                            blocked_paths += 1
                            
                    if blocked_paths > max_blocked_paths or \
                       (blocked_paths == max_blocked_paths and 
                        (len(opponent_paths_after[0]) > max_opponent_path or
                         (len(opponent_paths_after[0]) == max_opponent_path and my_path_increase < min_my_path_increase))):
                        max_blocked_paths = blocked_paths
                        max_opponent_path = len(opponent_paths_after[0])
                        min_my_path_increase = my_path_increase
                        best_wall = wall_move
            except Exception as e:
                print(f"处理挡板时出错: {str(e)}")
                continue

        return best_wall

    def _is_path_blocked_by_wall(self, path, wall):
        """检查挡板是否阻挡了给定路径"""
        for i in range(len(path) - 1):
            p1, p2 = path[i], path[i+1]
            if self._is_wall_between_positions(wall, p1, p2):
                return True
        return False

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
        opponent_path_after = new_state.find_all_shortest_paths(opponent_pos, opponent_target)
        
        # 验证路径是否可达
        if not my_path_after or not opponent_path_after:
            print(f"放置挡板 {wall} 后路径不可达")
            return float('-inf')
        
        # 计算路径长度变化
        my_path_increase = len(my_path_after) - len(my_path_before)
        opponent_path_increase = len(opponent_path_after[0]) - len(opponent_path_before)
        
        print(f"挡板 {wall} 放置后:")
        print(f"  我方路径长度: {len(my_path_before)} -> {len(my_path_after)} (增加 {my_path_increase})")
        print(f"  对手路径长度: {len(opponent_path_before)} -> {len(opponent_path_after[0])} (增加 {opponent_path_increase})")
        
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
        """检查挡板是否在两个位置之间"""
        x1, y1 = pos1
        x2, y2 = pos2
        
        # 解包挡板数据
        try:
            if isinstance(wall, tuple) and len(wall) == 2:
                (wx1, wy1, wd1), (wx2, wy2, wd2) = wall
                # 使用第一个挡板段的方向
                wd = wd1
                wx = wx1
                wy = wy1
            else:
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
        except Exception as e:
            print(f"挡板数据格式错误: {wall}, 错误: {str(e)}")
            return False