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
        
        if file and allowed_file(file.filename):
            # 儲存檔案
            filepath = os.path.join(UPLOAD_FOLDER, 'music_database.xlsx')
            file.save(filepath)
            
            # 讀取Excel檔案
            df = pd.read_excel(filepath)
            
            # 轉換為JSON格式
            data = df.to_dict(orient='records')
            
            return jsonify({
                'message': '檔案上傳成功',
                'data': data
            })
            
        return jsonify({'error': '不支援的檔案類型'}), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ['xlsx', 'xls']

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
        nickname = request.args.get('nickname')
        
        if os.path.exists(MOOD_HISTORY_FILE):
            with open(MOOD_HISTORY_FILE, 'r', encoding='utf-8') as f:
                history = json.load(f)
                
                if nickname:
                    history = [entry for entry in history if entry.get('nickname') == nickname]
                
                return jsonify(history)
        return jsonify([])
    
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

def static_files(filename):
    return send_from_directory('.', filename)

@app.route('/clear_history', methods=['POST'])
def clear_history():
    try:
        password = request.json.get('password')
        
        if password != '931106':
            return jsonify({'error': '密碼錯誤'}), 403
        
        # 清空歷史記錄
        with open(MOOD_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False)
        
        return jsonify({'message': '歷史記錄已清空'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
