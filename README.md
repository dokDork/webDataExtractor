# webDataExtractor
[![License](https://img.shields.io/badge/license-MIT-_red.svg)](https://opensource.org/licenses/MIT)  
<img src="https://raw.githubusercontent.com/dokDork/webDataExtractor/refs/heads/main/images/webDataExtractor.jpg" width="250" height="250">  

## Description
**webDataExtractor** explores all the web pages of a specific web site and extract from them: emails, Usernames, HTML comments, Telephone number and Links.

## Example Usage
 ```
python webDataExtractor.py https://www.mySite.htb 1
 ``` 
<img src="https://raw.githubusercontent.com/dokDork/webDataExtractor/refs/heads/main/images/01.jpg">  
and this is a possible result:
<img src="https://raw.githubusercontent.com/dokDork/webDataExtractor/refs/heads/main/images/02.jpg">  

## Command-line parameters
```
python webDataExtractor.py <target url> [<level>]
```

| Parameter | Description                          | Example       |
|-----------|--------------------------------------|---------------|
| `target url`      | URL from which we pretend to extract data (emails, username, etc) | `https://www.mySite.htb`|
| `level`      | level at which to stop scanning pages. If not specified the entire site will be scanned | `1`|
  
## How to install it on Kali Linux (or Debian distribution)
It's very simple  
```
cd /opt
```
```
pip install beautifulsoup4
```
```
git clone https://github.com/dokDork/webDataExtractor.git
```
