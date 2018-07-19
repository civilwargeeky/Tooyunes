rmdir %userprofile%\Desktop\TESTSS /S /Q
python setup.py py2exe --debug
mkdir %userprofile%\Desktop\TESTSS
xcopy build %userprofile%\Desktop\TESTSS /Y /E /I /F
xcopy lib %userprofile%\Desktop\TESTSS\lib /Y /E /I /F
xcopy src\img %userprofile%\Desktop\TESTSS\img /Y /E /I /F
xcopy src\resources %userprofile%\Desktop\TESTSS\resources /Y /E /I /F
copy version.txt %userprofile%\Desktop\TESTSS\version.txt /Y
cd /d %userprofile%\Desktop\TESTSS
main.exe
pause