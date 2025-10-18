# -*- coding: utf-8 -*-
import csv
import json
from datetime import datetime
import os

# --- 檔案設定 ---
# 優先嘗試載入此檔案 (如果存在的話)
JSON_SOURCE_FILE = 'history_data.json'
# CSV 檔案 (作為備用來源，如果 JSON 檔案不存在或載入失敗)
CSV_ASC_FILE = '今彩539_2025_update.csv'
CSV_DRAW_FILE = '今彩539_2025_update_f.csv'

# HTML 模板檔案名稱
HTML_TEMPLATE_FILE = 'historical_matrix.html'

# --- 輔助函式：根據您的 CSV 格式將日期轉換為星期幾 (中文) ---
def get_day_of_week(date_str):
    try:
        # 假設日期格式是 "2025/1/11" 或 "1/11"
        if len(date_str.split('/')) == 2:
            # 這裡假設年份為 2025，因為 JSON 輸出格式為 MM/DD
            full_date_str = f"2025/{date_str}" 
        else:
            full_date_str = date_str
            
        date_obj = datetime.strptime(full_date_str, '%Y/%m/%d')
        weekday = date_obj.weekday()  # 0=星期一, 6=星期日
        days = ['一', '二', '三', '四', '五', '六', '日']
        return days[weekday]
    except Exception:
        return ''

# --- 1. 數據處理與載入 ---
def process_and_load_data():
    data = []

    # 優先嘗試從現有的 history_data.json 載入數據
    if os.path.exists(JSON_SOURCE_FILE):
        try:
            with open(JSON_SOURCE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"成功載入數據：{JSON_SOURCE_FILE} (共 {len(data)} 筆)。")
                return data
        except Exception as e:
            print(f"錯誤：載入 {JSON_SOURCE_FILE} 時發生錯誤: {e}。將嘗試從 CSV 轉換。")
    
    # 如果找不到 history_data.json，或載入失敗，則執行 CSV 轉換流程
    print("未找到或無法載入 JSON 數據，開始執行 CSV 轉換流程...")
    
    asc_data = {}
    
    # 讀取大小順序 CSV
    try:
        with open(CSV_ASC_FILE, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None) # 跳過標題行
            for row in reader:
                if len(row) >= 6:
                    date_full = row[0].strip()
                    asc_numbers = [int(n.strip()) for n in row[1:6] if n.strip().isdigit()]
                    
                    try:
                        # 從完整日期中提取 YYYY/MM/DD
                        parts = date_full.split('/')
                        if len(parts) == 3:
                            year = parts[0]
                            month_day = f"{parts[1]}/{parts[2]}"
                        else: # 處理只有 MM/DD 的情況
                            year = "2025" 
                            month_day = date_full
                            
                        period_date = datetime.strptime(f"{year}/{month_day}", '%Y/%m/%d').strftime('%Y%m%d')
                        period = f"D{period_date}"
                        
                        asc_data[date_full] = {
                            'period': period,
                            'date': month_day, # 輸出格式為 MM/DD
                            'day': get_day_of_week(date_full),
                            'asc': asc_numbers
                        }
                    except Exception as date_e:
                         print(f"警告：處理日期 {date_full} 失敗: {date_e}")

    except FileNotFoundError:
        print(f"錯誤：找不到檔案 {CSV_ASC_FILE}。無法生成數據。")
        return []
    except Exception as e:
        print(f"讀取 {CSV_ASC_FILE} 時發生致命錯誤: {e}")
        return []

    # 讀取落球順序 CSV
    try:
        with open(CSV_DRAW_FILE, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None) # 跳過標題行
            for row in reader:
                if len(row) >= 6:
                    date_full = row[0].strip()
                    draw_numbers = [int(n.strip()) for n in row[1:6] if n.strip().isdigit()]
                    
                    if date_full in asc_data:
                        asc_data[date_full]['draw'] = draw_numbers
    except FileNotFoundError:
        print(f"警告：找不到檔案 {CSV_DRAW_FILE}。將只使用大小順序數據。")
        pass
    except Exception as e:
        print(f"讀取 {CSV_DRAW_FILE} 時發生錯誤: {e}")
        pass

    final_data = []
    for date_full, data in asc_data.items():
        if 'draw' in data and len(data['asc']) == 5 and len(data['draw']) == 5:
            final_data.append(data)
    
    # 確保數據從最新到最舊排列
    final_data.sort(key=lambda x: x['period'], reverse=True)

    print(f"已從 CSV 轉換並合併數據，總計 {len(final_data)} 筆。")
    return final_data

# --- 2. 數據嵌入與 HTML 生成 ---
def generate_html_report(data):
    # 這是 Python 腳本中唯一生成報告的函式
    if not data:
        print("警告：數據為空，生成的報告將是空白表格。")
        json_data_str = '[]'
    else:
        # 將數據轉換為 JSON 字串，並適當格式化以便嵌入
        json_data_str = json.dumps(data, indent=4, ensure_ascii=False)

    try:
        with open(HTML_TEMPLATE_FILE, 'r', encoding='utf-8') as f:
            html_template = f.read()
        
        # 將 JSON 數據替換到 HTML 模板的指定位置
        output_html = html_template.replace('<!-- JSON_DATA_PLACEHOLDER -->', f'const HISTORY_DATA = {json_data_str};')

        # 寫入最終的 HTML 檔案
        # 覆蓋 historical_matrix.html 以實現更新，或者寫入一個新的報告檔案
        output_filename = 'latest_lottery_report.html'
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(output_html)
            
        print("\n--- 成功完成 ---")
        print(f"數據已成功處理，並嵌入到檔案中：{output_filename}")
        print("-------------------")
        
    except FileNotFoundError:
        print(f"錯誤：找不到 HTML 模板檔案 {HTML_TEMPLATE_FILE}。")
    except Exception as e:
        print(f"生成 HTML 報告時發生錯誤: {e}")

# --- 主程式執行區塊 ---
if __name__ == '__main__':
    processed_data = process_and_load_data()
    generate_html_report(processed_data)
