from PIL import Image, ImageDraw, ImageFont

# 生成开屏图
img = Image.new('RGB', (800, 1280), '#66B5FC')
d = ImageDraw.Draw(img)
d.ellipse([250, 400, 550, 700], fill='#FB7299')
try:
    font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 60)
    d.text((400, 550), '币安合约分析', fill='white', anchor='mm', font=font)
except:
    pass
img.save('presplash.png')
print("✓ presplash.png已生成")
