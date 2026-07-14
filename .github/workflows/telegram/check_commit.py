import sys
import json

def main():
    if len(sys.argv) < 2:
        print("false")
        return
        
    target_url = sys.argv[1].strip()
    try:
        data = json.load(sys.stdin)
        # Kiểm tra xem link ROM có nằm trong commit message nào không
        found = any(target_url in c.get('commit', {}).get('message', '') for c in data if isinstance(c, dict))
        print('true' if found else 'false')
    except Exception:
        print('false')

if __name__ == '__main__':
    main()
