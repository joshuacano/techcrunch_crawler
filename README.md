# Techcrunch Crawler

Python script to crawl techcrunch home page

It has been done in Python 3, using the indispensable Beautiful Soup and Requests library.
As well as the grequests library to make asynchronous requests to each page.
The testing was done using the pytest and mock libraries.

## A few notes:
- As standard practice, please use the requirements.txt file to install any dependencies (pip install -r requirements.txt)
- There is a method to clean a url of all arguments after the slash (I.e. ?view=mobile or #comments), hence greatly reducing the number of urls to search. this may or may not want to be done.
- We are only checking distinct url's listed.
- Obviously the program is tightly tied to the current techcrunch layout, any changes to the layout will cause some major issues
- Currently the output is sorted by url, feel free to change this in in the last line of the script.
- I tried to follow pep8 as close as I can. The Test's could certainly be coded more modularly, but I feel like the test code is "good enough" for now.

To call the script, use the following syntax:
```
python3 company_reader/main.py path/to/file.csv
```
or
`python3 company_reader/main.py -h` for a description of the inputs necessary

To run the tests:
`python3 -m pytest tests/main_test.py`
or simply `py.test`