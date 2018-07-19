;My Installer for the GenerateHeader.py setup

; This was taken from the example page of fileread
#define FileHandle
#sub ProcessFileLine
  #define public _VERSION FileRead(FileHandle)
#endsub
#for {FileHandle = FileOpen("version.txt"); \
  FileHandle && !FileEof(FileHandle); ""} \
  ProcessFileLine
#if FileHandle
  #expr FileClose(FileHandle)
#endif
#pragma message "Displaying File Version"
#pragma message _VERSION


[Setup]
AppName="Music Downloader"
AppVersion={#_VERSION}
DefaultDirName={userdesktop}\Tooyunes
DisableProgramGroupPage=yes
Compression=lzma2                                                                             
OutputBaseFilename=Tooyunes_v{#_VERSION}
SolidCompression=yes
Uninstallable=no
OutputDir="release"
SetupIconFile="src\img\installer.ico"

[Files]
Source: "build\*"; DestDir: "{app}"; Flags: recursesubdirs
Source: "lib\*"; DestDir: "{app}\lib"; Flags: recursesubdirs
Source: "src\img\*"; DestDir: "{app}\img"
; We will ship the version with this file, so we can test on the first running if we need to update
Source: "version.txt"; DestDir: "{app}"

[Icons]
Name: "{userdesktop}\Tooyunes"; FileName: "{app}\main.exe"; WorkingDir: "{app}"; IconFilename: "{app}\img\mainIcon.ico" 
; Name: "{userdesktop}\Music Folder"; Filename: "{app}\code\Music";
; Name: "{userdesktop}\Scripts Folder"; Filename: "{app}\code\Scripts";