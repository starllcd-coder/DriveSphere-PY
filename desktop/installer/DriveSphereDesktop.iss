#define MyAppName "DriveSphere Desktop"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Deedarian Software Solutions"
#define MyAppExeName "DriveSphereDesktop.exe"
#define MyAppIcon "..\drivesphere_desktop\assets\images\logo.ico"

[Setup]
AppId={{D8A1C1E8-8A81-4F86-88D7-2A4A623D8D42}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\DriveSphere Desktop
DefaultGroupName=DriveSphere Desktop
DisableProgramGroupPage=yes
OutputDir=..\releases\1.0.0
OutputBaseFilename=DriveSphereDesktop-1.0.0-setup
Compression=lzma2
LZMAUseSeparateProcess=yes
LZMADictionarySize=32768
SolidCompression=yes
WizardStyle=modern
SetupIconFile={#MyAppIcon}
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop icon"; GroupDescription: "Additional icons:"

[Files]
Source: "..\..\dist\DriveSphereDesktop\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "__pycache__\*;*.pyc;*.pyo;*.log;*.tmp;*.bak"
Source: "..\..\dist\DriveSphereBackend\*"; DestDir: "{app}\DriveSphereBackend"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "__pycache__\*;*.pyc;*.pyo;*.log;*.tmp;*.bak;*.sqlite3;media\*"

[Icons]
Name: "{autoprograms}\DriveSphere Desktop"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\DriveSphere Desktop"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch DriveSphere Desktop"; Flags: nowait postinstall skipifsilent
