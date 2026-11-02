; Inno Setup betiği. Önce: python -m PyInstaller --noconfirm --onedir --windowed --name PDF_Birlestirici pdf_birlestirici.py
; Sonra: ISCC.exe setup.iss  ->  Output\PDF_Birlestirici_Setup.exe

#define AppVersion "1.2.0"

[Setup]
AppId={{8E3F2A71-5C4B-4D2E-9A6F-1B7C3D9E0F42}
AppName=PDF Birleştirici
AppVersion={#AppVersion}
AppPublisher=Hamza ERYILDIZ
DefaultDirName={autopf}\PDF Birlestirici
DefaultGroupName=PDF Birleştirici
; Yönetici izni istemez, kullanıcının kendi klasörüne kurar
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=Output
OutputBaseFilename=PDF_Birlestirici_Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\PDF_Birlestirici.exe

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\PDF_Birlestirici\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\PDF Birleştirici"; Filename: "{app}\PDF_Birlestirici.exe"
Name: "{group}\{cm:UninstallProgram,PDF Birleştirici}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\PDF Birleştirici"; Filename: "{app}\PDF_Birlestirici.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\PDF_Birlestirici.exe"; Description: "{cm:LaunchProgram,PDF Birleştirici}"; Flags: nowait postinstall skipifsilent
