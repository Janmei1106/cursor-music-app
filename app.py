from flask import Flask, request, jsonify, send_from_directory
import pandas as pd
import os
from datetime import datetime
import json

app = Flask(__name__, static_url_path='')

# 確保上傳目錄存在
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 資料庫檔案路徑
DB_FILE = os.path.join(UPLOAD_FOLDER, 'music_database.xlsx')
MOOD_HISTORY_FILE = os.path.join(UPLOAD_FOLDER, 'mood_history.json')

# 初始化心情歷史記錄
if not os.path.exists(MOOD_HISTORY_FILE):
    with open(MOOD_HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f, ensure_ascii=False)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/upload_excel', methods=['POST'])
def upload_excel():
    try:
        if 'file' not in request.files:
            return jsonify({'error': '沒有檔案'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '沒有選擇檔案'}), 400
        
        # 儲存並讀取 Excel 檔案
        file.save(DB_FILE)
        df = pd.read_excel(DB_FILE)
        
        # 驗證必要欄位
        required_columns = ['歌名', '歌手', '情緒', '語言', '點閱率', 'YouTube連結']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return jsonify({'error': f'缺少必要欄位：{", ".join(missing_columns)}'}), 400
        
        # 將資料轉換為字典列表
        songs = df.to_dict('records')
        return jsonify({'message': '檔案上傳成功', 'songs': songs})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_songs', methods=['GET'])
def get_songs():
    try:
        if not os.path.exists(DB_FILE):
            return jsonify({'error': '尚未上傳音樂資料庫'}), 404
        
        df = pd.read_excel(DB_FILE)
        songs = df.to_dict('records')
        return jsonify(songs)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/save_mood', methods=['POST'])
def save_mood():
    try:
        mood_data = request.json
        mood_data['date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 讀取現有記錄
        with open(MOOD_HISTORY_FILE, 'r', encoding='utf-8') as f:
            mood_history = json.load(f)
        
        # 添加新記錄
        mood_history.insert(0, mood_data)
        
        # 儲存更新後的記錄
        with open(MOOD_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(mood_history, f, ensure_ascii=False, indent=2)
        
        return jsonify({'message': '心情記錄已儲存'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_mood_history', methods=['GET'])
def get_mood_history():
    try:
        with open(MOOD_HISTORY_FILE, 'r', encoding='utf-8') as f:
            mood_history = json.load(f)
        return jsonify(mood_history)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/update_song_rating', methods=['POST'])
def update_song_rating():
    try:
        rating_data = request.json
        
        with open(MOOD_HISTORY_FILE, 'r', encoding='utf-8') as f:
            mood_history = json.load(f)
        
        if mood_history:
            latest_mood = mood_history[0]
            if 'songRatings' not in latest_mood:
                latest_mood['songRatings'] = []
            
            # 檢查是否已經有這首歌的評分
            existing_rating = next(
                (r for r in latest_mood['songRatings'] if r['songName'] == rating_data['songName']),
                None
            )
            
            if existing_rating:
                existing_rating['rating'] = rating_data['rating']
            else:
                latest_mood['songRatings'].append(rating_data)
            
            with open(MOOD_HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(mood_history, f, ensure_ascii=False, indent=2)
        
        return jsonify({'message': '歌曲評分已更新'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 