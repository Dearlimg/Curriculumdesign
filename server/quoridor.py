

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
