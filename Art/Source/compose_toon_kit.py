"""Make labeled contact sheets from the actual Blender asset renders."""
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'Art/Previews/ToonKit'
if (OUT/'inventory.json').exists():
    inventory=json.loads((OUT/'inventory.json').read_text())
else:
    inventory=[]
    for path in sorted(OUT.glob('[0-9][0-9]_*.png')):
        i=int(path.name[:2])
        group='Serving' if i<=16 else 'Flavors' if i<=40 else 'Toppings' if 42<=i<=59 else 'Supplies' if i in [41,60,61,62] else 'Vehicles' if 81<=i<=84 else 'Staff' if 85<=i<=88 else 'Furniture' if i in [*range(63,72),76,78,79] else 'Buildings'
        inventory.append({'name':path.stem[3:].replace('_',' '),'group':group,'preview':path.name})
font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',22)
title=ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf',38)
small=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',18)
groups=list(dict.fromkeys(e['group'] for e in inventory))
for group in groups:
    entries=[e for e in inventory if e['group']==group]
    columns=4 if len(entries)>6 else 2
    rows=math.ceil(len(entries)/columns)
    cellw,cellh=440,414
    board=Image.new('RGB',(columns*cellw+48,rows*cellh+150),'#f5f0e7')
    draw=ImageDraw.Draw(board)
    draw.text((28,19),'SCOOP / '+group.upper(),font=title,fill='#51415c')
    draw.text((30,76),'Selected toon style. Real Blender models. Items enlarged individually for review.',font=small,fill='#716678')
    for i,e in enumerate(entries):
        x=24+(i%columns)*cellw;y=124+(i//columns)*cellh
        im=Image.open(OUT/e['preview']).convert('RGB').resize((420,350),Image.Resampling.LANCZOS)
        board.paste(im,(x,y));draw.text((x+9,y+359),e['name'],font=font,fill='#51415c')
    board.save(OUT/(group+'.png'))
# A short overview uses representative models, with links to the complete boards in the index.
names=['Pop up stand','Expanded kiosk shell','12 slot locker','Waffle iron','Two scoop bowl','One swipe scooper','Strawberry tub','Chocolate sauce dispenser','Delivery bike 8 cargo','Ice cream truck','Expert employee','Supplier storefront']
entries=[next(e for e in inventory if e['name']==name) for name in names]
board=Image.new('RGB',(1368,1806),'#f5f0e7');draw=ImageDraw.Draw(board)
draw.text((26,18),'SCOOP / TOON MODEL KIT',font=title,fill='#51415c')
draw.text((28,74),str(len(inventory))+' models and variants / mint, strawberry, vanilla + plum cel shadows',font=small,fill='#716678')
for i,e in enumerate(entries):
    x=24+(i%3)*448;y=120+(i//3)*414
    im=Image.open(OUT/e['preview']).convert('RGB').resize((432,360),Image.Resampling.LANCZOS)
    board.paste(im,(x,y));draw.text((x+8,y+365),e['name'],font=font,fill='#51415c')
board.save(OUT/'ToonKitOverview.png')
print('Contact sheets written:',groups)
