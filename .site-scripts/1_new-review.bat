@echo off
:: Prompt the user for input
set /p movie_name=Enter the name of the movie: 

:: Run the Python script with the user input
python new-review.py "%movie_name%"

:: Pause to keep the command window open after execution
pause