@echo off
setlocal enabledelayedexpansion

set /p file1=Enter the name of the first file: 
set /p file2=Enter the name of the second file: 
set /p outfile=Enter the name of the output file: 

for %%a in (%file1%) do set file1name=%%~na
for %%a in (%file2%) do set file2name=%%~na

for /f "delims=" %%a in (%file1%) do (
    for /f "delims=" %%b in (%file2%) do (
        echo %%a %file1name%, %%b %file2name% >> %outfile%
    )
)

:end
endlocal