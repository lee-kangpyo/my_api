import codecs

data = open('goals.py', 'rb').read()
decoded = data.decode('cp949', errors='replace')
lines = decoded.split('\r\n')
for i, line in enumerate(lines):
    if 'tags=' in line and 'SmallStep' in line:
        lines[i] = '    tags=["SmallStep - 목표 관리"]'
        print(f'Fixed line {i+1}')
result = '\r\n'.join(lines)
open('goals.py', 'w', encoding='utf-8').write(result)
print('Done')