<p align="center">
  <img src="docs/tamatect-flyer.jpg" alt="Tamatect - Your Desktop Companion" width="720">
</p>

<h1 align="center">Tamatect - Your Desktop Companion</h1>
<p align="center">A featured Tamatect experience in this customized DyberPet desktop-pet project.</p>

<p align="center">
  <b>AEC-aware work states</b>: Tamatect responds to Rhino, Revit, and Rhino.Inside activity.<br>
  <b>Accessories and food</b>: equip customizable items and shop for Tamatect's workday favorites.<br>
  <b>Desktop companion care</b>: animations, health, progression, and physics-driven falling items.
</p>

<p align="center">
  <a>
    <img src="https://img.shields.io/github/license/ChaozhongLiu/DyberPet.svg">
  </a>

  <a style="text-decoration:none">
    <img src="https://img.shields.io/github/downloads/ChaozhongLiu/DyberPet/total.svg"/>
  </a>

  <a style="text-decoration:none">
    <img src="https://img.shields.io/badge/python-3.9+-blue.svg" />
  </a>

  <a style="text-decoration:none">
    <img src="https://img.shields.io/badge/DyberPet-v0.11.5-green.svg"/>
  </a>
</p>

<p align="center">
English | <a href="README.md">简体中文</a>
</p>

<p align="center">
  <a href="https://dyberpet.com/">Website</a> |
  <a href="https://github.com/ChaozhongLiu/DyberPet/releases/latest">Try Demo</a> |
  <a href="docs/collection.md">Browse Characters & MODs</a> |
  <a href="docs/art_dev.md">Read MOD Dev Docs</a>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/ChaozhongLiu/DyberPet/main/docs/DyberPet.gif" alt="DyberPet interface demo" width="92%">
</p>

## Why Try DyberPet

- More than a pet overlay: it already works as a full desktop pet app with animation, interaction, progression, and task systems.
- Highly moddable: pets, mini pets, items, food, and sounds can all be extended, with JSON-based configuration that is easy to start with.
- AI is optional, not required: connect LLM features for an assistant-like experience, or use it as a complete desktop pet without AI.

## Project Status

- **Latest version: v0.11.5**, with a packaged Windows build available in [Release](https://github.com/ChaozhongLiu/DyberPet/releases/tag/v0.11.5).
- The repository is still maintained primarily in Chinese, but feedback and bug reports are welcome.
- The LLM-related module is still under active development and is not yet fully open-sourced.
- There are reposted mirrors on CSDN / GitCode that are not affiliated with this project. Please use this GitHub repository as the canonical source.

Please leave a ⭐ **STAR** if you like the project and want to follow future updates.

:octocat: We are actively building out the LLM-related features and would welcome more contributors.  
If you are interested in joining, feel free to [message me](https://space.bilibili.com/39307302).


## Try the Demo
### Windows Users
  Download `Tamatect-Windows-x64.zip` from the latest GitHub Release, extract the **entire** archive to a writable folder, and run `Tamatect.exe`. Do not move the executable by itself; the archive also contains the app resources and runtime files. Save data is created in the `data` folder beside the executable.

### Run from Source (Windows)
  Install Python 3.9, then create an environment and install the pinned dependencies:
  ```
  py -3.9 -m venv .venv
  .\.venv\Scripts\python.exe -m pip install --upgrade pip
  .\.venv\Scripts\python.exe -m pip install -r requirements.txt
  ```
  Run the app from the repository root with `.\.venv\Scripts\python.exe run_DyberPet.py`.
  
### Debug in VS Code
  Open the repository folder, select `.venv\Scripts\python.exe` as the Python interpreter, open `run_DyberPet.py`, and press **F5** using the Python Debugger. For startup errors, run the source command above in the integrated terminal and inspect the traceback. Runtime settings and save data are stored under `data/`.

### Build a Windows Release
  From the repository root, install the requirements above and run:
  ```
  .\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --windowed --name Tamatect --icon "..\Tamatect.ico" --contents-directory . --add-data "..\res;res" --collect-all qfluentwidgets --hidden-import pynput.mouse._win32 --hidden-import pynput.keyboard._win32 --specpath build --workpath build\pyinstaller run_DyberPet.py
  Compress-Archive -Path .\dist\Tamatect\* -DestinationPath .\dist\Tamatect-Windows-x64.zip -Force
  ```
  Upload `dist\Tamatect-Windows-x64.zip` to the GitHub Release. It is an onedir bundle: publish the ZIP, not the EXE alone. The Windows build uses the icon in `Tamatect.ico`.




## User Manual
(Under construction)




## Developer Manual
(English version under construction)



## Acknowledgement
- Pictures in the Demo partially come from [daywa1kr](https://github.com/daywa1kr/Desktop-Cat)
- Animation module reference: [yanji255](https://toscode.gitee.com/yanji255/desktop_pet/)  
- Dragging and falling reference: [WolfChen1996](https://github.com/WolfChen1996/DesktopPet)

