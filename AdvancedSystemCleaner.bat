@echo off
REM ===================================================================
REM Advanced System Cleaner and Optimizer for Windows
REM Author: [Your Name]
REM Description: Cleans and optimizes Windows systems safely and efficiently.
REM License: Open Source
REM ===================================================================

:: Variables
SET LOGFILE=%TEMP%\SystemCleaner_Log_%DATE:~10,4%%DATE:~4,2%%DATE:~7,2%.txt

:: Check for Administrator privileges
NET SESSION >NUL 2>&1
IF %ERRORLEVEL% NEQ 0 (
    ECHO.
    ECHO *** This script must be run as an Administrator. Exiting. ***
    ECHO.
    PAUSE
    EXIT /B
)

:: Start Logging
ECHO Advanced System Cleaner Log - %DATE% %TIME% > "%LOGFILE%"
ECHO ========================================================== >> "%LOGFILE%"
ECHO.

:: 1. Create a System Restore Point
ECHO Creating System Restore Point...
ECHO Creating System Restore Point... >> "%LOGFILE%"
WMIC.exe /Namespace:\\root\default Path SystemRestore Call CreateRestorePoint "Before System Cleaning", 100, 7
ECHO Restore Point Created. >> "%LOGFILE%"
ECHO.

:: 2. Clean Temporary Files and Folders
ECHO Cleaning Temporary Files and Folders...
ECHO Cleaning Temporary Files and Folders... >> "%LOGFILE%"
DEL /F /S /Q "%TEMP%\*">> "%LOGFILE%" 2>&1
DEL /F /S /Q "C:\Windows\Temp\*">> "%LOGFILE%" 2>&1
FOR /D %%p IN ("%TEMP%\*.*") DO RMDIR "%%p" /S /Q>> "%LOGFILE%" 2>&1
ECHO Temporary Files Cleaned. >> "%LOGFILE%"
ECHO.

:: 3. Repair System Files
ECHO Repairing System Files...
ECHO Repairing System Files... >> "%LOGFILE%"
sfc /scannow >> "%LOGFILE%" 2>&1
ECHO SFC Scan Completed. >> "%LOGFILE%"
ECHO.

ECHO Restoring Health with DISM...
DISM /Online /Cleanup-Image /RestoreHealth >> "%LOGFILE%" 2>&1
ECHO DISM Restore Completed. >> "%LOGFILE%"
ECHO.

:: 4. Disable Unnecessary Startup Programs
ECHO Disabling Unnecessary Startup Programs...
ECHO Disabling Unnecessary Startup Programs... >> "%LOGFILE%"
:: List of programs to disable
SET PROGRAMS_TO_DISABLE=\
"Adobe Reader Synchronizer" \
"OneDrive" \
"Skype"

FOR %%A IN (%PROGRAMS_TO_DISABLE%) DO (
    REG ADD "HKLM\Software\Microsoft\Windows\CurrentVersion\Run" /V %%~A /T REG_SZ /D "" /F >> "%LOGFILE%" 2>&1
    REG ADD "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /V %%~A /T REG_SZ /D "" /F >> "%LOGFILE%" 2>&1
)
ECHO Startup Programs Disabled. >> "%LOGFILE%"
ECHO.

:: 5. Adjust Visual Effects for Best Performance
ECHO Adjusting Visual Effects for Best Performance...
ECHO Adjusting Visual Effects for Best Performance... >> "%LOGFILE%"
REG ADD "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects" /V VisualFXSetting /T REG_DWORD /D 2 /F >> "%LOGFILE%" 2>&1
ECHO Visual Effects Adjusted. >> "%LOGFILE%"
ECHO.

:: 6. Perform Malware Scan with Windows Defender
ECHO Performing Malware Scan...
ECHO Performing Malware Scan... >> "%LOGFILE%"
"%ProgramFiles%\Windows Defender\MpCmdRun.exe" -Scan -ScanType 2 >> "%LOGFILE%" 2>&1
ECHO Malware Scan Completed. >> "%LOGFILE%"
ECHO.

:: 7. Defragment and Optimize Drives
ECHO Defragmenting and Optimizing Drives...
ECHO Defragmenting and Optimizing Drives... >> "%LOGFILE%"
for /f "skip=1 tokens=1,*" %%i in ('wmic logicaldisk where "drivetype=3" get deviceid') do (
    if not [%%i]==[] (
        ECHO Optimizing Drive %%i... >> "%LOGFILE%"
        defrag %%i /H /U /V >> "%LOGFILE%" 2>&1
    )
)
ECHO Drive Optimization Completed. >> "%LOGFILE%"
ECHO.

:: 8. Update System
ECHO Updating Windows...
ECHO Updating Windows... >> "%LOGFILE%"
powershell.exe -Command "Install-WindowsUpdate -AcceptAll -AutoReboot" >> "%LOGFILE%" 2>&1
ECHO Windows Update Initiated. >> "%LOGFILE%"
ECHO.

:: 9. Completion Message
ECHO.
ECHO ==========================================================
ECHO   System Cleaning and Optimization Complete!
ECHO   Please review the log file for details:
ECHO   %LOGFILE%
ECHO ==========================================================
ECHO.
PAUSE

:: Open Log File
START NOTEPAD "%LOGFILE%"
EXIT
