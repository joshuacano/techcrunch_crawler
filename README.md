Python script to crawl techcrunch home page

It has been done in Python3, using the indispensable Beautiful Soup and Requests library.
As well as the grequests library to make asynchronous requests to each page.
The testing was done using pytest.

A few notes:
- There is a method to clean a url of all arguments after the slash. this may or may not want to be done.
- We are only storing distinct url's listed.
- Obviously the program is tightly tied to the current techcrunch layout, any changes to the layout will probably cause some major issues
- Currently the output is sorted by url, feel free to change this in in the last line of the script.

To call the script use the following syntax:
```python3 company_reader/main.py path/to/file.csv```

To run the tests:
```python3 -m pytest -s tests/main_test.py```
