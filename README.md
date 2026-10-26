# museum-hcde310

This repository contains files that explore the Art Institute of Chicago's API to collect data on at least 40 artworks to select the 12 best artworks that pertain to the theme of "food". We will utilize AI tools such as Claude to help form this project, AI usage and other information regarding AI influence on the project can be found in "ai_log.md".
We prompted the AI with the exercise instructions to create our files.

get_data.py is our original file which collects data from API requests through the AIC's API.

cleaned.py is the cleaned up and tidied version of get_data.py.

lastly, make_exhibit.py reads the json file created by cleaned.py and uses the data to make an HTML file which can be opened in a browser to display the final exhibit, displaying 12 photos related to "food" in art.