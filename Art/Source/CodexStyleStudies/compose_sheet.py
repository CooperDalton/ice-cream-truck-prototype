"""Lay out the actual Blender renders; no synthetic replacement imagery."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'Art/Previews/CodexStyleStudies'
names=['A_candy','B_facet','C_comic','D_vinyl','E_retro','F_gummy','G_clay','H_ps1','I_paper','J_voxel']
font=ImageFont.truetype('/usr/share/fonts/noto/NotoSans-Bold.ttf',36)
small=ImageFont.truetype('/usr/share/fonts/noto/NotoSans-Regular.ttf',18)
sheet=Image.new('RGB',(1968,3410),'#18212a'); draw=ImageDraw.Draw(sheet)
draw.text((32,22),'SCOOP CREW / TEN ART DIRECTIONS',font=font,fill='#fff2d9')
draw.text((34,77),'Original Blender models  /  Player + zombie + scoop pistol in every style',font=small,fill='#b7c7cc')
for i,name in enumerate(names):
    im=Image.open(OUT/(name+'.png')).convert('RGB')
    if name=='H_ps1': im.resize((1440,960),Image.Resampling.NEAREST).save(OUT/'H_ps1_display.png')
    thumb=im.resize((944,630),Image.Resampling.NEAREST if name=='H_ps1' else Image.Resampling.LANCZOS)
    sheet.paste(thumb,(32+(i%2)*960,122+(i//2)*650))
sheet.save(OUT/'00_All_Styles.jpg',quality=95)
print(OUT/'00_All_Styles.jpg')
