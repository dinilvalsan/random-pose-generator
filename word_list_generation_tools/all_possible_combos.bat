@echo off
setlocal enabledelayedexpansion

set /p file1=Enter the path of the first file: 
set /p file2=Enter the path of the second file: 
set /p output=Enter the output filename: 

for /f "delims=" %%a in (%file1%) do (
    for /f "delims=" %%b in (%file2%) do (
        echo %%a,%%b >> %output%
    )
)

:end
endlocal