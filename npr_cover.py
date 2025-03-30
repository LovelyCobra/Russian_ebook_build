from PIL import Image, ImageDraw, ImageFont
from cobraprint import col
import os, re

# A few helper functions and global variables
def image_html(img_src, video_href):
    html_string = f'<div><a href="{video_href}"><img src="{img_src}" /></a></div>'
    return html_string
    

def paste_position(pasted_img, center_target_position):
    (w, h) = pasted_img.size
    (x, y) = center_target_position
    return (x - w//2, y - h//2)

cover_colors = ['#003B0F', # dark green
                '#780000', # dark red
                '#63ADAA', # lighter green blue
                '#6C6C6C', # lighter grey
                '#9F7F55', # chocolate brown
                '#DB8113', # lighter orange
                '#0E5855', # deep green_blue
                '#313131', # darker grey
                '#311A00', # darker brown
                '#1B005C'  # dark blue
                ] # , 

root_dir = "Practical_Russian/"

###################
# COVER GENERATOR #
###################
def create_cover(title, single_chapter=False, color_index=0):
    
    safe_name = "".join(char for char in title if char.isalnum() or char in ('_', " ", '-', '.'))
    save_as = f"{root_dir}assets/{safe_name}_cover.png"
    
    # image = Image.open("image.jpg")
    if single_chapter:
        center_img = f"{root_dir}assets/Natalia_single_lesson.png"
        overall_color = '#908E7C' # darker beige
    else:
        center_img = f"{root_dir}assets/Generic_cover_image.png"
        overall_color = cover_colors[color_index%10]
        
    
    cover = Image.new('RGB', (1600, 2600), overall_color)
    cover_img = Image.open(center_img)
    logo_img = Image.open(f'{root_dir}assets/Amethyst.png').resize((80, 80))
    cov_img = cover_img.resize((1600, int(1600*cover_img.size[1]/cover_img.size[0])))
    cover.paste(cov_img, (0, 600), mask=cov_img)
    cover.paste(logo_img, paste_position(logo_img, (795, 2550)), mask=logo_img)
    
    # Create font objects for authors and subtitles
    try:
        if single_chapter:
            upper_title_font = ImageFont.truetype(f"{root_dir}assets/SagewoldItalic-OGnlA.ttf", size=130)
            lower_title_font = ImageFont.truetype(f"{root_dir}assets/Sagewold-ZpwvJ.ttf", size=240)
        else:
            upper_title_font = ImageFont.truetype(f"{root_dir}assets/Roboto-BlackItalic.ttf", size=130)
            lower_title_font = ImageFont.truetype(f"{root_dir}assets/Roboto-Black.ttf", size=240)
        author_font = ImageFont.truetype(f"{root_dir}assets/ARIBL0.ttf", size=170)
        subtitle_font = ImageFont.truetype(f"{root_dir}assets/ComicNeue-BoldItalic.ttf", size=110)
        src_font_left = ImageFont.truetype(f"{root_dir}assets/arial.ttf", size=67)
        src_font_right = ImageFont.truetype(f"{root_dir}assets/arial.ttf", size=67)
        
    except Exception as e:
        print(f"Font loading error: {e}")
        title_font = ImageFont.load_default()
        author_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        
    # Add writings (title, subtitle, author, publisher)
    title = title.split()
    if len(title) == 3:
        title_upper = title[0] + " " + title[1]
        title_lower = title[2]
    elif len(title) == 2:
        title_upper = title[0]
        title_lower = title[1]
    elif len(title) == 4:
        title_upper = title[0] + " " + title[1]
        title_lower = title[2] + " " + title[3]
    elif len(title) == 5:
        title_upper = title[0] + " " + title[1] + " " + title[2]
        title_lower = title[3] + " " + title[4]
    elif len(title) == 6:
        title_upper = title[0] + " " + title[1] + " " + title[2]
        title_lower = title[3] + " " + title[4] + " " + title[5]
    elif len(title) == 1:
        title_upper = title[0]
        title_lower = ""
        
    author = "Natalia"
    subtitle = "Practical Russian"
    
    draw = ImageDraw.Draw(cover)
    draw.text((800, 270), title_upper, fill='white', anchor='mm', font=upper_title_font)
    draw.text((800, 440), title_lower, fill='white', anchor='mm', font=lower_title_font)
    draw.text((800, 2150), author, fill='yellow', anchor='mm', font=author_font)
    draw.text((800, 2320), subtitle, fill='white', anchor='mm', font=subtitle_font)
    draw.text((615, 2550), "Amethyst", fill='beige', anchor='mm', font=src_font_left)
    draw.text((990, 2550), "Publishing", fill='beige', anchor='mm', font=src_font_right)
    # alternative publisher's color: #76ABB1
    
    
    cover.save(save_as)
    if not single_chapter:
        cover.show()
    return save_as


    
if __name__ == '__main__':
    
    for i in range(10):
        save_as = create_cover("Вылетело из головы", False, i)
    
    #Вылетело из головы, Russian Phrases Advanced
    
    #Tried colors: #AF0000 ... darker orange 6E4009 287F7F