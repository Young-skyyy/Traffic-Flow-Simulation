import zipfile, os

src = r'd:\文旅局数据\文旅局\火塘民谣 三人行电竞\咸丰县智慧旅游应用数据收集清单-文旅局上报数据-火塘民谣三人行电竞.xlsx'
out_dir = r'd:\文旅局数据\文旅局\火塘民谣 三人行电竞\提取图片'
os.makedirs(out_dir, exist_ok=True)

with zipfile.ZipFile(src, 'r') as z:
    for name in z.namelist():
        if name.startswith('xl/media/') and not name.endswith('/'):
            fname = os.path.basename(name)
            out_path = os.path.join(out_dir, fname)
            data = z.read(name)
            with open(out_path, 'wb') as f:
                f.write(data)
            print(f'已保存: {fname} ({len(data)} bytes)')

print(f'\n路径: {out_dir}')
