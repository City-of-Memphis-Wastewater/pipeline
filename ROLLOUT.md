# Rollout, setup, etc.
It is recommended to use **pyenv** for setting your Python version and generating virtual environment, though this is optional. To benefit from pyproject.toml rollout for this project, **Poetry** is entirely necessary for installing requirements.

### Why pyenv?
Because venv and virtualenv are too confusing, and pyenv is not. With pyenv, it is easy to run many projects at once, with different requirements for each. 
You only need to install pyenv once on you system, and then you use it to access different versions of Python.

#### Note to noobs (I was one once): 
I proimse that you want to generate virtual environments; You do not want to install special requirements to your system version of Python.

### Why Poetry?
**Poetry** is my favorite dependency management tool. It is very easy. You only need to install it once. **Poetry** also has the benefit of generating a directory-specific virtual environment.

## Use pyenv to set your Python version 
(3.11.9 or other 3.11.xx).
### Install pyenv
How to install pyenv-win (https://github.com/pyenv-win/pyenv-win)
```
Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/pyenv-win/pyenv-win/master/pyenv-win/install-pyenv-win.ps1" -OutFile "./install-pyenv-win.ps1"; &"./install-pyenv-win.ps1"
```
It is worth it to make the pyenv command persistent in PowerShell, by editing the $profile file to include something like:
```
$env:PYENV = "$HOME\.pyenv\pyenv-win"
$env:PYENV_ROOT = "$HOME\.pyenv\pyenv-win"
$env:PYENV_HOME = "$HOME\.pyenv\pyenv-win"
$env:Path += ";$env:PYENV\bin;$env:PYENV\shims"
	
# Initialize pyenv
#$pyenvInit = & $env:PYENV_HOME\bin\pyenv init --path
#Invoke-Expression $pyenvInit

# Manually set up the pyenv environment
function Invoke-PyenvInit {
    # Update PATH to include pyenv directories
    $pyenvShims = "$env:PYENV\shims"
    $pyenvBin = "$env:PYENV\bin"
    $env:PATH = "$pyenvBin;$pyenvShims;$env:PATH"
}

# Initialize pyenv
Invoke-PyenvInit
```
How to install pyenv on linux (https://github.com/pyenv/pyenv)
```
curl -fsSL https://pyenv.run | bash
```
To make the pyenv command persistent in the Bourne Again SHell, edit ~/.bashrc to include something like:
```
export Path="$HOME/.local/bin:$PATH"
export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init - bash)"
```
### Post-install, leverage the benefits of pyenv
Install Python 3.11.9 using pyenv:
```
# pyenv install --list # See all Python versions able with pyenv.
pyenv install 3.11.9
# pyenv global 3.11.9 # to set your current directory version
```
## Use Poetry to run deploy the requirements for this project 
How to install poetry (https://github.com/python-poetry/poetry)
```
#Remove-Item Alias:curl # Solution to common PowerShell issue 
curl -sSL https://install.python-poetry.org | python3
# Alternatively: 
// pip install poetry
# Or, even:
// pyenv exec pip install poetry
```
## Git clone pipeline, open source
```
git clone https://github.com/City-of-Memphis-Wastewater/pipeline.git
cd pipline
pyenv local 3.11.9 # to set your current directory version
```
Explicitly set poetry to use the local pyenv version.
```
poetry python list
# You'll see something like this:
>> 3.13.2  CPython        System  C:/Users/<user>/.pyenv/pyenv-win/versions/3.13.2/python3.13.exe
>> 3.13.2  CPython        System  C:/Users/<user>/.pyenv/pyenv-win/versions/3.13.2/python313.exe
>> 3.13.2  CPython        System  C:/Users/<user>/.pyenv/pyenv-win/versions/3.13.2/python3.exe
>> 3.13.2  CPython        System  C:/Users/<user>/.pyenv/pyenv-win/versions/3.13.2/python.exe
>> 3.11.9  CPython        System  C:/Users/<user>/.pyenv/pyenv-win/versions/3.11.9/python3.11.exe
>> 3.11.9  CPython        System  C:/Users/<user>/.pyenv/pyenv-win/versions/3.11.9/python311.exe
>> 3.11.9  CPython        System  C:/Users/<user>/.pyenv/pyenv-win/versions/3.11.9/python3.exe
>> 3.11.9  CPython        System  C:/Users/<user>/.pyenv/pyenv-win/versions/3.11.9/python.exe
# Copy and paste ~any~ of the comparable paths to pyenv 3.11.9 ...
poetry use C:\Users\<user>\.pyenv\pyenv-win\versions\3.11.9\python.exe
```
Pull the requirements from the pyproject.toml file for packagage installation.
```
poetry install 
# This is where the magic happens.
# When in doubt, run this again. 
# Sometimes it doesn't take until you use "poetry run python".
```