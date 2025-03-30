# Russian_ebook_build
Reads content of pdf files from Natalia Practical Russian YT channel (NPR), adds stress marks and converts the text into a well formatted e-book (.epub)

## Folder tree
The script is made of 3 Python files: npr_main.py, npr_cover.py, cobraprint.py. All other needed files need to be placed in the subdirectory "Practical_Russian", itself placed in the working directory. When processing a single pdf file, this file needs to be placed in this subdirectory. When processing a bunch of pdf files into an ebook collection, these files need to be placed in a subdirectory of the "Practical_Russian/", named the way one wants the collection to be named, the name containing two or maximum three words (for example: "Russian_Lessons_Intermediate").

Besides the sigle-lesson pdf files (and/or already annotated txt files) and subdirectories with collections, the "Practical_Russian" directory also needs to contain these further subdirectories with the following list of items:
	- **"assets"** sub-directory: 
 			+ *nav.css* (css styles file); 
			+ images *Generic_cover_image.png* and *Natalia_single_lesson.png*; 
   			+ fonts: *Roboto-BlackItalic.ttf*, *Roboto-Black.ttf*, *Sagewold-ZpwvJ.ttf*, *ARIBL0.ttf*, *SagewoldItalic-OGnlA.ttf*, *ComicNeue-BoldItalic.ttf* and *arial.ttf*;

## Source format
This Python Script uses primarily pdf files containing transcripts of lessons by NPR as a text source, it parses the content with all the inevitable flaws that come about when forced to work with the **bloody pdf format**, adds the stress marks to the main body of the text with the help of the online tool at www.russiangram.com (many thanks to its provider) and saves the processed text in a .txt file of the same name as the original pdf.

Once the txt file with stress marks is created, it is possible to forget about the original pdf and continue working just with the txt file, even when running the code repeatedly.

## Mid-step txt-file
Another part of the code then uses this txt file to add further markdown formating, converts the text into html format and then makes it into an ebook.
