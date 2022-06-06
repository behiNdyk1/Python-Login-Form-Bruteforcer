# Python-Login-Form-Bruteforcer
Python script to bruteforce login forms

## Usage
The usage is very simple, you need to pass the url containing the target form, an username and a password list and an error message to avoid.
`./script.py --url http://target.com/login -U username.lst -P password.lst --error_msg "Login fail"`

Of course, there are optional parameters, like:
-f: Exits when a valid combination is found.
-vv: Verbose mode.
--javascript: Renders javascript if the target is using js to create forms.
-u: Rotate users rather than passwords.
