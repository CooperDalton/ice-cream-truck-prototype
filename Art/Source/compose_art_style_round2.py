"""Label the eight Blender renders for direct comparison."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

folder=Path(__file__).resolve().parents[2]/'Art/Previews/ArtStyleRound2'
font=Path('C:/Windows/Fonts')
regular=ImageFont.truetype(str(font/'segoeui.ttf'),25)
small=ImageFont.truetype(str(font/'segoeui.ttf'),21)
heading=ImageFont.truetype(str(font/'segoeuib.ttf'),40)
label=ImageFont.truetype(str(font/'segoeuib.ttf'),29)
sheet=Image.new('RGB',(1840,3340),'#f5f1e9')
draw=ImageDraw.Draw(sheet)
draw.text((35,25),'Soft or cel? / Shop and serving props',font=heading,fill='#382f42')
draw.text((35,86),'Four more objects in each style. Same colors and camera angles.',font=regular,fill='#675d6a')
for column,(style,title) in enumerate([('Soft','A / Soft toy town'),('Cel','B / Cel cartoon')]):
    x=35+column*895
    draw.text((x,142),title,font=label,fill='#382f42')
    for row,(file,title) in enumerate([('Stand','Ice cream stand'),('Waffle_iron','Waffle iron'),('Serving_bowl','Serving bowl'),('Scooper','Scooper')]):
        y=202+row*770
        draw.text((x,y),title,font=regular,fill='#675d6a')
        render=Image.open(folder/f'{style}_{file}.png').convert('RGB').resize((875,700),Image.Resampling.LANCZOS)
        sheet.paste(render,(x,y+38))
draw.text((35,3290),'Blender material studies. Game art and gameplay remain unchanged.',font=small,fill='#675d6a')
sheet.save(folder/'SoftVsCel_Props.png')
print(folder/'SoftVsCel_Props.png')
