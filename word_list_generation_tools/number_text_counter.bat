@echo off
set /p start=Enter start number: 
set /p end=Enter end number: 
set /p step=Enter step size: 
set /p text=Enter text to append: 
set /p output=Enter output filename: 

for /L %%i in (%start%, %step%, %end%) do (
    echo %%i %text% >> %output%
)