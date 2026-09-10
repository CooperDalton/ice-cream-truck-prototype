"""Arrange the rendered 3D studies into one comparison sheet."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parents[2]
folder = root / 'Art/Previews/ArtStyleReview'
font_dir = Path('C:/Windows/Fonts')
regular = lambda size: ImageFont.truetype(str(font_dir / 'segoeui.ttf'), size)
bold = lambda size: ImageFont.truetype(str(font_dir / 'segoeuib.ttf'), size)
width, margin, gap = 2840, 40, 16
cell_w, cell_h = 678, 565
sheet = Image.new('RGB', (width, 2040), '#f5f1e9')
draw = ImageDraw.Draw(sheet)
draw.text((margin, 28), 'Ice cream tycoon / art studies', font=bold(46), fill='#382f42')
draw.text((margin, 94), 'Same assets and camera views. Three possible directions for the game.', font=regular(27), fill='#675d6a')
columns = [
    ('Original', 'Current models', 'The existing cottage, maple tree, and tub.'),
    ('Soft', 'A / Soft toy town', 'Round forms, curved eaves, soft highlights.'),
    ('Cel', 'B / Cel cartoon', 'Three light bands and a thin plum outline.'),
    ('Painted', 'C / Painted storybook', 'A leaning roof and broad color variation.'),
]
for i, (style, title, description) in enumerate(columns):
    x = margin + i * (cell_w + gap)
    draw.text((x, 155), title, font=bold(31), fill='#382f42')
    draw.text((x, 201), description, font=regular(23), fill='#675d6a')
    for j, kind in enumerate(['Cottage', 'Tree', 'Tub']):
        y = 250 + j * (cell_h + 8)
        render = Image.open(folder / f'{style}_{kind}.png').convert('RGB')
        render = render.resize((cell_w, cell_h), Image.Resampling.LANCZOS)
        sheet.paste(render, (x, y))
draw.text((margin, 1980), 'Blender material studies. The game still uses its existing art and shaders.', font=regular(25), fill='#675d6a')
sheet.save(folder / 'ArtStyleComparison.png')
print(folder / 'ArtStyleComparison.png')
