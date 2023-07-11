# GBF Asset Lookup  
Web page to search for GBF assets.  
Click [Here](https://mizagbf.github.io/GBFAL) to access it.  
  
# How-to.  
The project consists of a single HTML, javascript and css files.  
All the work is done via the JSON files loaded by the javascript file.  
Those JSON files are generated and maintained with `parser.py`.  
Do note that using `parser.py` can be time and bandwidth consuming.  
Running it without parameters will give you a list of parameters.  
The most useful ones are:  
- `python parser -run`: It will fetch all new elements and update the JSON accordingly.  
- `python parser -update ELEMENT_ID_1 ELEMENT_ID_2 ... ELEMENT_ID_N`: To update specific elements (for example, characters if they got updated with an uncap). ELEMENT_ID are IDs of the elements to update, for example 3040000000.  
Others parameters are mostly for maintenance or debug purpose.  
Do note than main character classes can be tricky: A class ID must be associated with what I call a keyword, and even sometime weapon files (in case of skins with custom ougis/effects).  
You can run `python parser -job` to search keywords and possible outfit related weapon files.  
`python parser -jobedit` will then give you a menu with various ways to set them to the related class.  