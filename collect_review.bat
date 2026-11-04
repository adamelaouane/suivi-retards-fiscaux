
@echo off

(
echo ========================================
echo PROJECT STRUCTURE
echo ========================================
tree app /F

echo.
echo ========================================
echo ALL PROJECT SOURCE FILES
echo ========================================

for /R app %%F in (*.py *.html *.css *.js) do (
    echo.
    echo ========================================
    echo FILE: %%F
    echo ========================================
    type "%%F"
)

echo.
echo ========================================
echo ROOT CONFIGURATION
echo ========================================

for %%F in (requirements.txt run.py README.md .gitignore alembic.ini) do (
    if exist "%%F" (
        echo.
        echo ========================================
        echo FILE: %%F
        echo ========================================
        type "%%F"
    )
)

) > project_review.txt 2>&1

echo.
echo Review file created successfully!
pause
