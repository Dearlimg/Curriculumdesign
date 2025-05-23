class Quoridor():
    def __init__(self):
        self.player_white = {'name': '', 'pwd': ''}
        self.player_black = {'name': '', 'pwd': ''}
        self.players = {}
        self.player_num = 0
        self.playing = False
        self.now_player = {'name': '', 'color': 'black'}
        self.chess_board = {'black_pos': [1, 5], 'white_pos': [9, 5],
                            'black_blocks_num': 0, 'white_blocks_num': 0,
                            'black_blocks_pos': [], 'white_blocks_pos': []}
        self.winner = ''

    def add_user(self, name, pwd):
        if self.player_num == 0:
            self.player_black = {'name': name, 'pwd': pwd}
            self.now_player = {'name': name, 'color': 'black'}
            self.players = {name: pwd}
            self.player_num = 1
            return 'welcome join, ' + name + ', your color is black'
        elif self.player_num == 1:
            if self.player_black['name'] != name:
                self.player_white = {'name': name, 'pwd': pwd}
                self.players.update({name: pwd})
                self.playing = True
                self.player_num = 2
                return 'welcome join, ' + name + ', your color is white'
            elif self.player_black['name'] == name and self.player_black['pwd'] != pwd:
                return name + ', your password is wrong'

            return 'welcome back, ' + name + ', your color is black'
        else:
            if self.player_black['name'] == name and self.player_black['pwd'] == pwd:
                return 'welcome back, ' + name + ', your color is black'
            elif self.player_white['name'] == name and self.player_white['pwd'] == pwd:
                return 'welcome back, ' + name + ', your color is white'
            elif self.player_black['name'] == name and self.player_black['pwd'] != pwd \
                    or self.player_white['name'] == name and self.player_white['pwd'] != pwd:
                return name + ', your password is wrong'
            else:
                return "we are playing, please try later"


    def move_chess(self, new_pos):
        new_pos = eval(new_pos)
        if self.now_player['color'] == 'black':
            self.chess_board['black_pos'] = new_pos
        else:
            self.chess_board['white_pos'] = new_pos

    def put_blocks(self, block_position):
        block_position = eval(block_position)
        if self.now_player['color'] == 'black':
            self.chess_board['black_blocks_num'] += 1
            self.chess_board['black_blocks_pos'].extend(block_position)
        else:
            self.chess_board['white_blocks_num'] += 1
            self.chess_board['white_blocks_pos'].extend(block_position)

    def play(self, request):
        if request.form['type'] == 'move_chess':
            new_pos = request.form['pos']
            self.move_chess(new_pos)
        elif request.form['type'] == 'put_blocks':
            block_position = request.form['block_position']
            self.put_blocks(block_position)
        self.check_win()
        if self.now_player['color'] == 'black':
            self.now_player = {'name': self.player_white['name'], 'color': 'white'}
        else:
            self.now_player = {'name': self.player_black['name'], 'color': 'black'}

    def check_win(self):
        if self.now_player['color'] == 'black' and self.chess_board['black_pos'][0] == 9 \
                or self.now_player['color'] == 'white' and self.chess_board['white_pos'][0] == 1:
            self.winner = self.now_player['name']

    def end_game(self):
        self.__init__()

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
        score = opponent_path_increase * 5 - my_path_increase * 2

        # 优先考虑直接阻挡对手最短路径的挡板
        if len(opponent_path_before) >= 2:
            for i in range(len(opponent_path_before) - 1):
                p1, p2 = opponent_path_before[i], opponent_path_before[i+1]
                if self._is_wall_between_positions(wall, p1, p2):
                    score += 20  # 大幅加分
                    break

        # 挡板距离对手越近分数越高
        wx, wy, _ = wall
        dist_to_opponent = abs(wx - opponent_pos[0]) + abs(wy - opponent_pos[1])
        score += max(0, 8 - dist_to_opponent)  # 距离越近分数越高

        # 远离对手的挡板分数降低
        if dist_to_opponent > 4:
            score -= 5

        # 如果挡板放置后对手路径增加超过2步，给予额外分数
        if opponent_path_increase > 2:
            score += 5
        
        # 如果挡板放置后自己的路径增加超过2步，降低分数
        if my_path_increase > 2:
            score -= 10
        
        return score
