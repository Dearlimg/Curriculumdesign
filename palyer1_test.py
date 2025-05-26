import requests
import json


def join_game(url, userdata):
    url = url + '/join_game'
    response = requests.post(url, data=userdata)
    print(response.text)
    return response.text


def play_chess(url, userdata, chessdata):
    url = url + '/play_chess'
    data = userdata.copy()
    data.update(chessdata)
    response = requests.post(url, data=data)
    print(response.text)
    return response.text


def get_chessboard(url):
    url = url + '/get_chessboard'
    response = requests.get(url)
    chessboard = json.loads(response.text)
    print(response.text)
    return chessboard['chessboard']


def get_now_player_and_color(url):
    url = url + '/get_now_player_and_winner'
    response = requests.get(url)
    now_player_and_color = json.loads(response.text)
    print(response.text)
    return now_player_and_color


if __name__ == '__main__':
    url = 'http://127.0.0.1:5100'
    userdata = {'name': '小李', 'pwd': '123456'}

    # 两个玩家的名字应该不同
    while True:
        join_game(url, userdata)

        # 获取游戏是否进行中，当前玩家的姓名和颜色信息
        now_player_and_color = get_now_player_and_color(url)

        # 获得棋盘信息
        chessboard = get_chessboard(url)

        chessdata = {'type': 'move_chess', 'pos': '(2,5)', 'move_again': 'False'}
        # # 当type为move_chess时，进行移动棋子操作
        # # 当且仅当移动的目的位置是对方棋子位置，可以再次移动，move_again为True，否则为False
        # # pos为最终的棋子位置
        # chessdata = {'type': 'put_blocks', 'block_position': '((6, 7, 1), (6, 8, 1))'}
        # # 当type为put_blocks时，在block_position中填入两格挡板的位置，挡板只能是横放或竖放，占据1*2或2*1格,最后一个1表示横向的挡板，纵向挡板为0
        play_chess(url, userdata, chessdata)
