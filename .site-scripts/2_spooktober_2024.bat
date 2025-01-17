@echo off
:: Prompt the user for input
set /p movie_name=Enter the name of the movie: 
set /p day=Enter the day: 

:: Run the Python script with the user input
python spooktober.py "%movie_name%" "%day%"

:: Pause to keep the command window open after execution
pause