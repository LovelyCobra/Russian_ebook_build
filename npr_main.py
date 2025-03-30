import os, re, pymupdf, markdown, io
from markdown.extensions.tables import TableExtension
from cobraprint import col, style, cur_forward
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
from npr_cover import create_cover, image_html
from ebooklib import epub
from bs4 import BeautifulSoup
from datetime import datetime
from tqdm import tqdm
from pathlib import Path

foot_links = "\n\n---\n\nMore video and audio materials about Russian language and Russia here:\n\n[YouTube](https://www.youtube.com/@practicalrussian), [Patreon](https://www.patreon.com/practicalrussian), [Boosty](https://boosty.to/practicalrussian)\n\nGet my latest book with [Short Stories!](https://ko-fi.com/practicalrussian/shop)\n\nJoin my FREE channel on [Telegram](https://t.me/practical_russian)\n\nListen to other episodes on the [Podcast](https://podcast.ru/1717882716)\n\nIf you feel like, you can [Support me](https://ko-fi.com/practicalrussian) and my work, I would be very grateful! 💛"

root_dir = "Practical_Russian/"

###############################
# A bunch of helper functions #
###############################
def ebook_corebuild(title, html_chapters, color_index):
        
    # Create an EPUB book
    book = epub.EpubBook()
    
    # Metadata
    # Required
    book.set_identifier(f'npr2ebook_{datetime.now().strftime("%Y%m%d%H%M%S")}')
    book.set_title(title)
    book.set_language("ru")
    # Optional
    book.add_author("Natalia")
    book.add_metadata('DC', 'publisher', 'Amethyst Publishing')
    book.add_metadata('DC', 'description', 'Trascript of lesson(s) from Natalia Practical Russian')
    
    # Add stylesheet
    with open(os.path.join(f'{root_dir}assets/', "nav.css").replace('\\', '/'), "r", encoding="utf-8") as f:
        css_content = f.read()
        style = epub.EpubItem(uid="style", file_name="style/nav.css", media_type="text/css", content=css_content)
        book.add_item(style)
    
    toc_items = []
    
    # Adding chapters and images
    for chapt in html_chapters:
        soup = BeautifulSoup(chapt, features='lxml')
        titl =  "".join(char for char in soup.h1.text if char.isalnum() or char in (' ', '-', '_', '.'))
        # adding chapter
        ch = epub.EpubHtml(title=titl, file_name=f'{titl}.xhtml', content=chapt)
        ch.add_item(style)
        book.add_item(ch)
        toc_items.append(ch)
        
        # adding image if available
        image = soup.find('img')
        if image:
            image_path = image['src']
            image_name = os.path.basename(image_path)
            # print(f"\n{col.GREY}{image_path}{col.END}")
            with open(root_dir + image_path, 'rb') as img_file:
                # Create an EpubItem for the image.
                img_item = epub.EpubItem(
                    uid=image_name, 
                    file_name=f'images/{image_name}', 
                    media_type='image/png', 
                    content=img_file.read()
                )
                book.add_item(img_item)    
        
    ################
    # Adding COVER #
    ################
    if len(html_chapters) == 1:
        single_chapter = True
        cover_file = create_cover(title, single_chapter)
    else:
        single_chapter = False
        cover_file = create_cover(title, single_chapter, color_index)
    with Image.open(cover_file) as img:
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG', quality=95)
        img_bytes = img_bytes.getvalue()

    # Create cover
    cover_image = epub.EpubCover(uid='cover-image', file_name='images/cover.jpg')
    cover_image.content = img_bytes
    book.add_item(cover_image)

    # Create cover page
    cover_xhtml = epub.EpubCoverHtml(image_name=cover_image.file_name)
    cover_xhtml.add_item(style)
    book.add_item(cover_xhtml)
    
    
    # SET Table of Contents
    book.toc = tuple([cover_xhtml] + toc_items)
    
    # add navigation files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    
    if len(html_chapters) == 1:
        book.spine = ['cover'] + toc_items
    else:
        book.spine = ['cover', 'nav'] + toc_items
        
    # This guide is for some mysterious reason necessary for the cover to be displayed at the beginning instead of the end of the book!!!
    book.guide = [{'type': 'cover', 'href': cover_xhtml.file_name, 'title': 'Cover'}]
        
    # create epub file
    safe_filename = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
    filename =f"{safe_filename}.epub"
    
    try:
        epub.write_epub(root_dir + filename, book, {})
        print(f"{col.SEP}{col.GREY}The Russian lesson(s) has/have been processed\n   and the annotated transcript saved as {col.GREEN}{filename}{col.GREY}\n      in the curent working directory, in the subdirectory {col.BLUE}\"{root_dir}\"{col.END}.{col.SEP}")
        
    except Exception as e:
        print(f"Exception has occured: {e}")

def txt2md_compiler(processed_txt):
    '''"processed_txt" is text with stress markings and vocabulary tabel added,
    with vocabulary words set in bold, but without main title and subtitle marked '''
    
    text = re.sub("^\n*", '', processed_txt)
    # setting title and subtitle
    text_md = "# " + text.replace("ТРАНСКРИПЦИЯ", "### ТРАНСКРИПЦИЯ")
    first_line = re.search("^.*?\n", text_md).group()
    # dividing the 1st line into title and subtitle if possible
    separators = [" - ", "_ ", "! ", "? ", "Russian"]
    title = ""
    for sep in separators:
        if sep in first_line:
            tit_subtit = first_line.split(sep)
            title = tit_subtit[0][2:]
            subtitle = tit_subtit[1].strip()
            if sep == "! ": add = "!"
            elif sep == "? ": add = "?"
            else: add = ""
            text_md = text_md.replace(first_line, tit_subtit[0] + add + "\n## *" + subtitle + "*")
            # text_md = re.sub(first_line.replace('?', '\?'), tit_subtit[0] + add + "\n## *" + subtitle + "*", text_md, 1)
            break
    if not title: title = first_line[2:]
            
    text_html = markdown.markdown(text_md, extensions=[TableExtension()])
    
    return title, text_html

def pdf_tables_processor(pdf_filepath):
    doc = pymupdf.open(pdf_filepath)
    tbls = doc[0].find_tables()
    
    root_dir = os.path.dirname(pdf_filepath)
     
    # tabs = "\n\n---\n\n"
    bold_words = []
    tbls_cont = []
    for tab in tbls.tables:
        # tabs += f"{tab.to_markdown()}\n\n---\n\n"
        tbls_cont.extend(tab.extract())
        bold_list = [item[0].split(' - ') for item in tab.extract()]
        bold_words.extend(bold_list)
    
    # Pythonic way to flatten 2-D list
    bold_words = [word for sublist in bold_words for word in sublist]
    # List of words to set in bold
    words_in_bold = []
    for word in bold_words:
        word = re.sub("\s?\(.*\)\s?", '', word, flags=re.DOTALL)
        word = re.sub("\d+\.\s*", '', word, flags=re.DOTALL)
        words_in_bold.append(word)
        
    tab_md = "\n\n---\n\n### СЛОВА И ФРАЗЫ\n\n|     |\n| :------------- |\n"
    for russ_eng_pair in tbls_cont:
        tab_md += f"| **{russ_eng_pair[0].replace('\n', '')}**<br>*{russ_eng_pair[1].replace('\n', '')}* |\n"
    
    return tab_md, words_in_bold


#########################################################################
# Extracting content of Practical Russian pdf & pre_editing it somewhat #
#########################################################################

def pdf_extract(pdf_filepath):
    pdf_filename = os.path.basename(pdf_filepath)
    pdf_rootpath = os.path.dirname(pdf_filepath)
    txt_filename = pdf_filename.replace('.pdf', '.txt')
    
    # If the txt file with stress marks has already been generated this snippet will bypass the rest of the function
    if txt_filename in os.listdir(pdf_rootpath):
        with open(os.path.join(pdf_rootpath, txt_filename).replace('\\', '/'), 'r', encoding='utf-8') as f:
            text = f.read()
        return text, pdf_filepath
    
    doc = pymupdf.open(pdf_filepath)
    text = ""
    links = []
    for i in range(doc.page_count):
        text += doc.load_page(i).get_text()
        links_on_page = doc[i].get_links()
        for link in links_on_page:
            if link not in links: links.append(link)
    
    heading = re.search(r"^.*?\n", text)
    if heading:
        heading = heading.group()
        text = re.sub(heading, '\n', text)
    
    text = re.sub("\.\s\n\d\s\n", "\.\n", text) # removing page numbers and extra line breaks that come with them
    text = re.sub("\n\d\s\n", " ", text)
    text = text.replace('  ', ' ')
    
    tab_md, words_in_bold = pdf_tables_processor(pdf_filepath)
    
    # Setting the main vocabulary in bold
    for word in words_in_bold:
        if len(word) > 5:
            text = text.replace(f' {word} ', f' **{word}** ')
    
    # Replacing tables pdf-mess on the 1st page with correct table markdown 
    text = re.sub("(Video:.*?\n).*?ТРАНСКРИПЦИЯ", r"\n\n\1\nТРАНСКРИПЦИЯ", text, flags=re.DOTALL)
    text = re.sub("ТРАНСКРИПЦИЯ", f"{tab_md}\nТРАНСКРИПЦИЯ", text)
    # and adding video thumb as a link if available in images subdirectory
    img_filename = pdf_filename.replace('.pdf', '.png')
    if img_filename in os.listdir(f"{root_dir}images"):
        video_html = image_html(f"images/{img_filename}", links[1]['uri'])
        text = re.sub("Video:\s", f"{video_html}\n\nVideo: ", text)
        
    
    # Linking YouTube video
    first_link = re.search("Video:\s.*?\n", text)
    if first_link:
        link_txt = first_link.group()[7:-1]
        string_to_replace = first_link.group()
        text = text.replace(string_to_replace, f"Video: [{link_txt.strip()}]({links[1]['uri']})")
    
    # Separating paragraphs with an empty line for the markdown to see them
    lines = text.split('\n')
    for line in lines:
        if len(line) < 55 and line.endswith('.'):
            text = text.replace(line, line + "\n")
            
    # Adding footlinks
    if re.search("Outro\s", text):
        text = re.sub("Outro\s.*$", foot_links, text, flags=re.DOTALL)
    else:
        text = re.sub("More video and audio materials.*$", foot_links, text, flags=re.DOTALL)
        
    return text, pdf_filepath

##############################################
# Adding stress markings to the Russian text #
##############################################
def stress_adder(text, pdf_filepath, use_txt=True):
    text = text.strip()
    
    # Isolating the middle part for annotation
    intro_body = text.split("ТРАНСКРИПЦИЯ")
    body_footlinks = intro_body[1].split("\n\n---\n\n")
    russtxt_body = body_footlinks[0]
    save_as = pdf_filepath.replace('.pdf', '.txt')
    save_as_filename = os.path.basename(save_as)
    save_as_root = os.path.dirname(save_as)
    
    # If the file has already been processed and annotated text already saved, 
    # this snippet will simply read the result from the txt file and return it;
    # so the rest of the function will not be executed. If this is not desired for a single txt file, 
    # then the relevant previous txt file needs to be removed from the appropriate directory! 
    # If all txt files need to be processed again, then the 'use_txt' needs to be set 'False'
    if save_as_filename in os.listdir(save_as_root) and use_txt:
        with open(save_as, 'r', encoding='utf-8') as f:
            processed_txt = f.read()
            return processed_txt
    
    # Limiting the length of the inserted text at one go (3000 characters)
    txt_paragraphs = russtxt_body.split("\n")
    section_to_upload = txt_paragraphs.pop(0)
    current_par_number = len(txt_paragraphs)
    print(f"{col.SEP}{col.GREY}The processed file: {col.GREEN}{os.path.basename(pdf_filepath)}\n")
    print(f"{col.GREY}The number of paragraphs to be annotated: {col.RED}{current_par_number}{col.SEP}")
    processed_txt_container = ""
    
    while current_par_number > 0:
        # Initialize the browser (using Chrome in this example)
        driver = webdriver.Chrome()
        
        try:
            # Adding paragraphs one by one untill limit exceeded, then pasting the portion in the input field
            while len(section_to_upload) < 3000 and current_par_number > 0:
                section_to_upload = "\n".join((section_to_upload, txt_paragraphs.pop(0)))
                current_par_number -= 1
            print(f"\n{col.GREY}Number of unprocessed paragraphs: {col. BLUE}{current_par_number}{col.END}")
                    
            # Navigate to the website that performs the annotation
            driver.get("https://russiangram.com/")  # adjust the URL if needed

            # Wait until the input field is loaded (you might need to adjust the locator)
            input_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "MainContent_UserSentenceTextbox"))  # use the actual ID or another selector
            )

            # Clear the field and paste the text
            input_field.clear()
            input_field.send_keys(section_to_upload)

            # Option 1: Click the Annotate button (adjust the locator as necessary)
            annotate_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "MainContent_SubmitButton"))  # use the actual ID or another selector
            )
            annotate_button.click()

            # Option 2 (alternative): Send Ctrl+Enter to trigger annotation
            # input_field.send_keys(Keys.CONTROL, Keys.ENTER)
            
            # Wait until the value of the input field changes from the original text
            annotated_text = WebDriverWait(driver, 15).until(
            lambda d: d.find_element(By.ID, "MainContent_UserSentenceTextbox").get_attribute("value") != text)

            # Once the condition is met, retrieve the updated value
            annotated_text = driver.find_element(By.ID, "MainContent_UserSentenceTextbox").get_attribute("value")
            
            processed_txt_container += annotated_text
            section_to_upload = ""
            print("Length of the processed text:", f"{col.GREEN}{len(processed_txt_container)} characters{col.END}")
            
        finally:
            # Close the browser
            driver.quit()
            
    processed_txt = intro_body[0] + "\n\nТРАНСКРИПЦИЯ\n\n" + processed_txt_container + "\n\n---\n\n" + body_footlinks[1]
    
    # Saving a pre-processed text with stress markings in a txt file; this is not a complete markdown yet
    with open(save_as, 'w', encoding='utf-8') as f:
        f.write(processed_txt)
    
    print(f"\n\n{col.RED}The given Russian text has been processed via www.russiangram.com!{col.END}{col.SEP}")
            
    return processed_txt

# Helper function: meant to be run independetly to generate the annotated txt files for bunch of pdfs;
# or can be also used as a part of lectures_aggregator() if the second parameter in it is set False
def aggr_stress_adder(directory, using_txts=True):
    pdf_list = [file for file in os.listdir(directory) if file.endswith('.pdf')]
    txtfiles_cont_list = []
    for file in tqdm(pdf_list, desc="PDF files processing:", ascii=True, colour='green'):
        txt_filename = file.replace('.pdf', '.txt')
        filepath = os.path.join(directory, file).replace('\\', '/')
        txt_filepath = filepath.replace('.pdf', '.txt')
        if txt_filename not in os.listdir(directory) or not using_txts:
            text, pdf_filepath = pdf_extract(filepath)
            processed_txt = stress_adder(text, pdf_filepath, using_txts)
            with open(txt_filepath, 'w', encoding='utf-8') as f:
                f.write(processed_txt)
            txtfiles_cont_list.append(processed_txt)
        else:
            with open(txt_filepath, 'r', encoding='utf-8') as f:
                txtfiles_cont_list.append(f.read())
            
    return txtfiles_cont_list

################################################################
# Processing the annotated single transcription into an E_Book #
################################################################
def ebook_build(ready_txt, color_index):
    
    title, text_html = txt2md_compiler(ready_txt)
    
    ebook_corebuild(title, [text_html], color_index)
        
        
#########################################################################
# Collecting annotated transcripts in a single directory into one ebook #
#########################################################################
'''This function uses contents of txt files that have already been processed
by stress_adder() in advance. This approach has the advantage of allowing to do
some editing of those texts beforehand. Also the automatic adding of the stress markings
via www.russiangram.com regularly failes due to issues with internet connection, 
and therefore is better done in advance of aggreagation. Since the content of the txt files 
is treated as markdown, the single "\n"s (new line) do not result in new lines in the ebook. Therefore no 
need to edit faulty, irregular single new lines that often come out of pdf processing.'''

def lectures_aggregator(directory, color_index, using_txts=True):
    textbook_title = os.path.basename(directory).replace('_', ' ')
    chapt_htmls = []
    
    if not using_txts:
        txts_cont_list = aggr_stress_adder(directory, using_txts)
        for txt in txts_cont_list:
            tit, text_html = txt2md_compiler(txt)
            chapt_htmls.append(text_html)
    else:
        chapt_filenames = [file for file in os.listdir(directory) if file.endswith('.pdf')]
        for pdf in tqdm(chapt_filenames, desc="Processing txt files:", ascii=True, colour='yellow'):
            txt_filename = pdf.replace('.pdf', '.txt')
            if  txt_filename not in os.listdir(directory):
                pdf_filepath = os.path.join(directory, pdf).replace('\\', '/')
                txt, pdf_filepath = pdf_extract(pdf_filepath)
                processed_text = stress_adder(txt, pdf_filepath)
                tit, text_html = txt2md_compiler(processed_text)
                chapt_htmls.append(text_html)
            else:
                txt_filepath = os.path.join(directory, txt_filename).replace('\\', '/')
                # print(f"{col.SEP}{txt_filepath}{col.SEP}")
                with open(txt_filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tit, text_html = txt2md_compiler(content)
                    chapt_htmls.append(text_html)
            
    ebook_corebuild(textbook_title, chapt_htmls, color_index)


# ------------------------------------------------------------------ #
            
if __name__ == '__main__':
    
    # Creating needed directories in the current working folder in the case they have not been created already
    os.makedirs("Practical_Russian", exist_ok=True)
    os.makedirs("Practical_Russian/assets", exist_ok=True)
    os.makedirs("Practical_Russian/images", exist_ok=True)
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Command line user interface communication
    
    fork = input(f"{col.RED}PRACTICAL RUSSIAN STRESS MARKINGS ADDER AND EBOOK GENERATOR\n\n{col.GREY}W E L C O M E  to the processor of the Practical Russian lessons.\n\nThe subdirectory {col.YELLOW}Practical_Russian{col.GREY} have been created for you in your current working directory \nin which you need to place pdf files of those lessons \nthat you wish to process separately. \n\nHere you also need to place subdirectories containing pdf files of those lessons \nyou wish to process into a single ebook collection. \n\nFurther {col.CYAN}assets{col.GREY} and {col.CYAN}images{col.GREY} subdirectories have been created here. \n\nIn {col.WHITE}assets{col.GREY} you need to place a square shaped image named {col.YELLOW}'Generic_cover_image.png'{col.GREY} you want to be used \nas a part of the cover for your ebook. \n\nThe subdirectory {col.WHITE}images{col.GREY} is for thumbnails of the videos, if you wish them to be included in the ebook. \nThey are optional and need to be given the same names as the corresponding pdf files have, with '.png' endings.{col.SEP}Choose one of the actions bellow by typing the appropriate number and pressing {col.WHITE}'Enter'{col.GREY}:\n\n{col.GREEN}1 - {col.GREY}Processing one pdf file of a Russian lecture into an annotated ebook.\n{col.GREEN}2 - {col.GREY}Preparing a txt-file-collection of several Russian lectures by adding stress marks first \n{cur_forward(4)}with the option of their further editing.\n{col.GREEN}3 - {col.GREY}Aggregating several Russian lessons into one annotated ebook collection, \n{cur_forward(4)}either with or without previous stress markings addition.\n{col.GREEN}4 - {col.GREY}End the program.\n\n{col.WHITE}Add your choise {col.GREY}(as a number 1, 2, 3 or 4){col.WHITE} here and press {col.GREY}'Enter'{col.WHITE}: {col.RED}")
    
    color_index = 0
    
    while fork != '4':
        if fork not in ('1', '2', '3', '5', '6'):
            fork = input(f"\n{col.RED}WRONG INPUT!!! Try again: {col.RED}")
            
        elif fork == '1':
            pdf_filename = input(f"\n{col.GREY}Save the pdf file of the lesson you wish to annotate and make into an ebook \nin the {col.CYAN}Practical_Russian{col.GREY} subdirectory.\n\nThen input the full name of your pdf file here and press {col.YELLOW}Enter{col.GREY}: {col.RED}")
            pdf_filepath = "Practical_Russian/" + pdf_filename
            txt_filename = pdf_filename.replace('.pdf', '.txt')
            if txt_filename not in os.listdir("Practical_Russian"):
                text, pdf_filepath = pdf_extract(pdf_filepath)
                stressed_txt = stress_adder(text, pdf_filepath)
            else:
                with open("Practical_Russian/" + txt_filename, 'r', encoding='utf-8') as f:
                    stressed_txt = f.read()
            ebook_build(stressed_txt, color_index)
            
            fork = input(f"{col.GREY}How do you wish to proceed from here? ({col.GREEN}1{col.GREY} - one pdf file processing; {col.GREEN}2{col.GREY} - aggregate stress adding; {col.GREEN}3{col.GREY} - aggregate lectures' collection; {col.GREEN}4{col.GREY} - END ?): {col.RED}")
            
        elif fork == '2':
            directory = input(f"\n{col.GREY}Save all the pdf files you wish to include in the collection \nin one subdirectory of the  {col.CYAN}Practical_Russian{col.GREY} directory. \nYou need to name this directory the same way you want to name the collection, \nwith words (two or three) separated by '_' instead of a simple space ' '.\n\nThen input the name of that subdirectory here and press {col.WHITE}Enter{col.GREY}: {col.RED}")
            aggr_stress_adder("Practical_Russian/" + directory)
            
            fork = input(f"\n{col.GREY}Do you wish to proceed to create the ebook from annotated texts? If yes, type {col.RED}Y{col.GREY} and press the {col.WHITE}Enter{col.GREY}. \nBefore you do that, you can edit the text files in the collection subdirectory.\nIf no, then type {col.RED}N{col.GREY} and press the {col.WHITE}Enter{col.GREY}: {col.RED}").upper()
            
            if fork == "Y":
                lectures_aggregator("Practical_Russian/" + directory, color_index)
                color_index += 1
            elif fork == "N":
                fork = "4"
        
        elif fork == '3':
            directory = input(f"\n{col.GREY}All pdf files with lessons' transcriptions need to be saved in one subdirectory \nof the {col.WHITE}Practical_Russian{col.GREY} directory. This subdirectory needs to be named after the intended name of the collection, \nwith words {col.WHITE}(two or three){col.GREY} separated by {col.MAGENTA}'_'{col.GREY} instead of just space ' '. \n\nIf you wish to include thumbnails of the lessons' YouTube videos, \nyou need to save them as {col.WHITE}.png{col.GREY} files in {col.YELLOW}Practical_Russian/images{col.GREY} subdirectory. \n{col.RED}These png files need to have the same names as pdf files containing the lessons' transcriptions!!!{col.WHITE}\n\nWhen all is ready, type the name of the subdirectory with the relevant pdf files and press {col.GREY}Enter{col.WHITE}: {col.RED}")
            
            lectures_aggregator("Practical_Russian/" + directory, color_index)
            
            color_index += 1
            fork = input(f"{col.GREY}How do you wish to proceed from here? ({col.GREEN}1{col.GREY} - one pdf file processing; {col.GREEN}2{col.GREY} - aggregate stress adding; {col.GREEN}3{col.GREY} - aggregate lectures' collection; {col.GREEN}4{col.GREY} - END ?): {col.RED}")
            
        # Processing all collections in a bulk
        elif fork == '5':
            color_index = 0
            subdir_list = [item for item in os.listdir("Practical_Russian") if os.path.isdir(f"Practical_Russian/{item}") and item not in ('assets', 'images', 'style')]
            for collection in tqdm(subdir_list, desc="Processing collections:", ascii=True, colour='green'):
                lectures_aggregator("Practical_Russian/" + os.path.basename(str(collection)), color_index)
                color_index += 1
            fork = input(f"{col.GREY}How do you wish to proceed from here? ({col.GREEN}1{col.GREY} - one pdf file processing; {col.GREEN}2{col.GREY} - aggregate stress adding; {col.GREEN}3{col.GREY} - aggregate lectures' collection; {col.GREEN}4{col.GREY} - END ?): {col.RED}")
            
        # Processing all pre-processed single lessons in a bulk
        elif fork == '6':
            pdf_list = [item for item in os.listdir("Practical_Russian") if item.endswith('.txt')]
            for file in tqdm(pdf_list, desc="Processing pdf files:", ascii=True, colour='blue'):
                txt_filepath = "Practical_Russian/" + file
                with open(txt_filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                ebook_build(content, color_index)
            
            fork = input(f"{col.GREY}How do you wish to proceed from here? ({col.GREEN}1{col.GREY} - one pdf file processing; {col.GREEN}2{col.GREY} - aggregate stress adding; {col.GREEN}3{col.GREY} - aggregate lectures' collection; {col.GREEN}4{col.GREY} - END ?): {col.RED}")
            
            
    print(f"{col.SEP}{col.MAGENTA}{style.undr}A  F E W   U S E F U L   T I P S :{col.END}{col.WHITE}\n\n1. {col.GREY}Internet connection is needed for actions numbered {col.YELLOW}1, 2 a 3{col.GREY} as long as\n   txt files with added stress marks have not been created.\n   After that internet is not needed to run those actions repeatedly.\n{col.WHITE}2. {col.GREY}It is recommended to run the action number {col.YELLOW}2{col.GREY} first to create txt files\n   with already annotated text (text with stress marks added by www.russiangram.com).\n   Then some minimal editing of those texts is recommendable, before proceeding\n   with the action number {col.YELLOW}3{col.GREY}.\n{col.WHITE}3. {col.GREY}When editing the txt files with stress marks, keep in mind\n   that the text is then treated as a markdown, therefore there is no need\n   to worry about messy single linebreaks, because those are ignored\n   when converting the text into html format needed for the generation of the ebook.\n{col.WHITE}4. {col.GREY}Besides the {col.YELLOW}'Generic_cover_image.png'{col.GREY} image needed for the generation of the ebook cover,\n   the {col.WHITE}'Practical_Russian/assets'{col.GREY} subdirectory also needs to contain these\n   {style.it}'Cyrillic-enabled'{col.END}{col.GREY} fonts: {col.CYAN}Roboto-BlackItalic.ttf, Roboto-Black.ttf, Sagewold-ZpwvJ.ttf, ARIBL0.ttf, SagewoldItalic-OGnlA.ttf\nComicNeue-BoldItalic.ttf {col.GREY}and {col.CYAN}arial.ttf.{col.SEP}")
            