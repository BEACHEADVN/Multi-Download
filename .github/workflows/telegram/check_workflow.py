import sys
import json

def main():
    if len(sys.argv) < 2:
        print("false")
        return
        
    target_url = sys.argv[1].strip()
    try:
        data = json.load(sys.stdin)
        runs = data.get('workflow_runs', [])
        duplicate = False
        
        for r in runs:
            title = r.get('display_title', '')
            status = r.get('status', '')
            conclusion = r.get('conclusion', '')
            
            # Nếu link ROM xuất hiện trong tiêu đề chạy của build.yml
            if target_url in title:
                # Chặn nếu đã chạy thành công HOẶC đang xếp hàng / đang chạy
                if (status == 'completed' and conclusion == 'success') or status in ['in_progress', 'queued']:
                    duplicate = True
                    break
                    
        print('true' if duplicate else 'false')
    except Exception:
        print('false')

if __name__ == '__main__':
    main()
