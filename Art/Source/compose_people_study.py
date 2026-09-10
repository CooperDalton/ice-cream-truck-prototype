import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'Art/Previews/PeopleStudy'
entries=json.loads((OUT/'inventory.json').read_text())
directions=list(dict.fromkeys(e['direction'] for e in entries))
title=ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf',42)
font=ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf',27)
small=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',21)
board=Image.new('RGB',(1856,1350),'#f5f0e7');draw=ImageDraw.Draw(board)
draw.text((28,18),'SCOOP / NEW PEOPLE',font=title,fill='#51415c')
draw.text((30,76),'Four different silhouettes. Staff above, customers below. Actual Blender models.',font=small,fill='#716678')
for x,name in enumerate(directions):
    draw.text((34+x*456,120),name,font=font,fill='#51415c')
    for row,role in enumerate(['Staff','Customer']):
        entry=next(e for e in entries if e['direction']==name and e['role']==role)
        im=Image.open(OUT/entry['preview']).convert('RGB').resize((440,533),Image.Resampling.LANCZOS)
        board.paste(im,(24+x*456,166+row*569))
board.save(OUT/'PeopleComparison.png')
print('People comparison saved')
