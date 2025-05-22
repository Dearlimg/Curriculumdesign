# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

# 桌游 Quoridor “步步为营” 对战设计
# 游戏的规则：
# 一个9X9或者7X7的棋盘（用7X7主要是降低算法复杂度）
# 一方位于棋盘上方中间格子，一方位于棋盘下方的中间格子
# 游戏的目的就是将己方的棋子，走到对方出发的那一行。
# 比如你是从底部出发，你就是走到最上一行（只要走到那一行即可，不管是这行的哪一格）
# 以下是规则：
# 1、行棋过程中，双方各执10块挡板，挡板用于阻拦对手前进。
#   挡板有横有竖，阻挡时的唯一规则就是，你不能围个圈把对方堵死。
# 2、每一个回合，玩家都可以控制棋子移动（可以向上下左右四个方向移动，每次移动一格，只要移动的方向上没有挡板）或放置挡板（与行棋二者择其一，挡板也只能一回合放置一块）。
#   挡板横跨（或竖跨）两个格子，放下后即无法收回。
# 3、如果你正在移动棋子，并且棋子下一步正好是对方棋子的位置，则可以再走一步（只能行棋不能放置挡板）


from flask import Flask, request, render_template, session, redirect, url_for, jsonify

from server.quoridor import *

# from datetime import timedelta

now_user = []
player_user = []
now_play = []

app = Flask("Quoridor")
app.config['SECRET_KEY'] = 'your_secret_key_here21461027450912385'
gaming = Quoridor()


@app.route('/join_game', methods=("POST",))
def add_player():
    # 玩家可以通过request.post(url,userdata)加入游戏
    name = request.form['name'].strip()
    pwd = request.form['pwd']
    message = gaming.add_user(name, pwd)
    if gaming.playing:
        session['color'] = 'white'
        gaming.playing = True
    else:
        session['color'] = 'black'
    session['chess_board'] = gaming.chess_board
    # print(gaming.playing)
    return message


@app.route('/get_chessboard')
def get_chessboard():
    # 玩家可以通过request.get(url)获取棋盘信息
    chessboard = gaming.chess_board
    return jsonify(chessboard=chessboard)


@app.route('/get_now_player_and_winner')
def get_now_player():
    # 玩家可以通过request.get(url)获取棋当前玩家姓名、当前玩家颜色，胜利者姓名，当前游戏是否开始等信息
    # print(gaming.chess_board)
    return jsonify(now_player=gaming.now_player['name'], now_color=gaming.now_player['color'], winner=gaming.winner,
                   playing=str(gaming.playing))



@app.route('/play_chess', methods=("POST",))
def play_chess():
    # 为了便于同学们进行调试，删除了play_chess中的校验代码和计时代码
    # 实际流程为：
    # 1、校验玩家的账号密码是否匹配
    # 2、校验游戏是否开始
    # 3、校验玩家是否是当前玩家
    # 4、校验玩家的操作时间是否满足要求
    # 5、校验玩家的操作是否合法
    # 6、执行下棋操作

    gaming.play(request)
    return "wait for your opponent"



@app.route('/quit')
def quit_game():
    gaming.__init__()
    root_url = url_for('root_web')
    return redirect(root_url)


@app.route('/')
def root_web():
    return render_template("quoridor.html")


if __name__ == '__main__':
    app.jinja_env.auto_reload = True

    app.run(host='0.0.0.0', port=5100)
