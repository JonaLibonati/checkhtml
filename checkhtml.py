import re
import os
import sys
import json

from inspect import getsourcefile
from os.path import abspath
from classes import menu
from classes import testReport
from classes import cmdArguments
from classes import directory

# Global Variables
__pyPath__ = abspath(getsourcefile(lambda:0)).replace('checkhtml.py','')
__opFlags__ = ''
__opErrors__ = ''

# Tags processor function
def checkSyntax(filePath):
	def isClosingTag(tag_name):
		return tag_name.find("/") != -1

	def isSelfClosingTag(tag):
		response = False
		for self_closing_tag in self_closing_tags:
			if tag['name'].find(self_closing_tag) != -1:
				response = True
		return response

	def filterSelfClosingTags(tag_list):
		filtered_tags = []
		for tag in tag_list:
			if not isSelfClosingTag(tag):
				filtered_tags.append(tag)
		return filtered_tags

	def countSpaces(line):
		i = 0
		for char in line:
			if char == ' ':
				i += 1
			elif char == '	':
				continue
			else:
				break
		return i

	def countTabs(line):
		i = 0
		for char in line:
			if char == '	':
				i += 1
			elif char == ' ':
				continue
			else:
				break
		return i

	def tagFinder(html_string):
		tag_names = []
		tags_in_string = re.findall("<[^>]*>|<.*$", html_string)  # Search all HTML tags
		if tags_in_string != []:
			for tag in tags_in_string:
				tag = tag.split(" ")[0]
				tag_names.append(tag.replace("<","").replace(">",""))
		return tag_names

	def findUnclosedTags(tag_list, unclosed_tag_list = []):
		filtered_tags = tag_list
		first_tag = tag_list[0]
		control_tag_list = tag_list[1:]
		sub_tags_list = []
		sub_unclosed_tags = []
		unclosed_tags = unclosed_tag_list
		unclosed = True

		filtered_tags.pop(0)
		if len(filtered_tags) > 0 and not isClosingTag(first_tag['name']) and not first_tag in unclosed_tag_list:
			# Main loop
			for i, control_tag in enumerate(control_tag_list):
				if first_tag['name'] == control_tag['name'].replace('/',''):
					if isClosingTag(control_tag['name']):
						if (first_tag['spaces'] == control_tag['spaces'] and first_tag['tabs'] == control_tag['tabs']) :
							filtered_tags.pop(i)
							unclosed = False
							break
						""" n_close = n_close + 1 """
					elif (first_tag['spaces'] >= control_tag['spaces'] and first_tag['tabs'] >= control_tag['tabs']) and first_tag['line'] != control_tag['line']:
						break
					""" else:
						n_open = n_open + 1
					sub_tags_list.append(control_tag) """
		""" # Subloop for the nesting tags
		while sub_tags_list != []:
			response = findUnclosedTags(sub_tags_list, sub_unclosed_tags)
			sub_tags_list = response[0]
			sub_unclosed_tags = response[1]
			#print(sub_tags_list)
		# Adding errors comming from the Subloop
		for sub_unclosed_tag in sub_unclosed_tags:
			if not sub_unclosed_tag in unclosed_tag_list:
				unclosed_tags.append(sub_unclosed_tag) """
		# Adding error comming from the main loop
		if unclosed and not first_tag in unclosed_tag_list:
			unclosed_tags.append(first_tag)

		return [filtered_tags, unclosed_tags]

	def findIndentationErrors(tag_list, error_list = [], unclosed_tags = []):
		filtered_tags = []
		sub_tags_list = []
		sub_error_tags = []
		errorList = error_list
		errors = True

		if unclosed_tags != []:
			for tag in tag_list:
				if not tag in unclosed_tags:
					filtered_tags.append(tag)
		else:
			filtered_tags = tag_list
		if filtered_tags == []:
			return [filtered_tags, errorList]

		first_tag = filtered_tags[0]
		control_tag_list = filtered_tags[1:]
		#This function use two indentation criteria:
		#	1) opening tag and closing tag are in the same line
		#	2) opening tag and closing tag are not in the same line but both have the the same indentation.
		filtered_tags.pop(0)
		n_open = 0
		n_close = 0
		control_tag = {}
		# Main loop
		for i, control_tag in enumerate(control_tag_list):
			control_tag = control_tag
			# Conditions when tag names are the same:
			#	1) opening tag and closing tag are in the same line
			#	2) opening tag and closing tag are not in the same line but both have the the same indentation.
			if first_tag['name'] == control_tag['name'].replace('/',''):
				if isClosingTag(control_tag['name']):
					if n_open == n_close:
						if (first_tag['spaces'] == control_tag['spaces'] and first_tag['tabs'] == control_tag['tabs']) or (first_tag['line'] == control_tag['line']):
							errors = False
						filtered_tags.pop(i)
						break
					n_close = n_close + 1
				else:
					n_open = n_open + 1
				sub_tags_list.append(control_tag)
			# Conditions to flag the following indentation errors:
			# 	e.g.
			#		<ul>
			#			<li><h2>example text</h2></li>
			#	<li> (wrong indentation)
			#				<h2>example text</h2>
			#	</li> (wrong indentation)
			#		</ul>
			if (control_tag['spaces'] <= first_tag['spaces'] and control_tag['tabs'] <= first_tag['tabs']):
				if sub_tags_list != []:
					if sub_tags_list[-1]['line'] != control_tag['line']:
						errorList.append(('', control_tag))
				elif (first_tag['line'] != control_tag['line']):
					errorList.append(('', control_tag))

		# Subloop for the nesting tags
		while sub_tags_list != []:
			response = findIndentationErrors(sub_tags_list, sub_error_tags)
			sub_tags_list = response[0]
			sub_error_tags = response[1]
		# Adding errors comming from the Subloop
		for sub_error_tag in sub_error_tags:
			if not sub_error_tag in errorList:
				errorList.append(sub_error_tag)
		# Adding error comming from the main loop
		if control_tag == {}:
			control_tag.update({'name': 'undefined', 'line': 'undefined'})

		if errors and not (first_tag, control_tag) in errorList and first_tag['name'] == control_tag['name'].replace('/',''):
			errorList.append((first_tag, control_tag))

		return [filtered_tags, errorList]

	# -u . To print only unclosed
	def flagUnclosed(unclosed, Report, opErrors = ''):
		section = testReport.Section("Unclosed tags")
		if unclosed == [] and not opErrors == '-e':
			r = testReport.Result('No unclosed tags were found.', 'success')
			section.addResult(r)
		else:
			for error in unclosed:
				r = testReport.Result(f"Unclosed tag found. <{error['name']}> tag in line {error['line']}. {error}", 'fail')
				section.addResult(r)
		if section.results != []:
			Report.addSection(section)

	# -i . To print only indentation
	def flagIndentation(indentation, Report, opErrors = ''):
		section = testReport.Section("Indentation Issues")
		if indentation == [] and not opErrors == '-e':
			r = testReport.Result('No indentation errors were found.\n\n', 'success')
			section.addResult(r)
		else:
			for error in indentation:
				if error[0] == '':
					r = testReport.Result(
						'Indentation error found. Check the syntax for:\n'\
						f"	Tag: <{error[1]['name']}> in line {error[1]['line']}\n", 'fail')
					section.addResult(r)
				else:
					r = testReport.Result(
						'Indentation error found. Check the syntax for:\n'\
						f"	Opening tag: <{error[0]['name']}> in line {error[0]['line']}\n"\
						f"	Closing tag: <{error[1]['name']}> in line {error[1]['line']}\n", 'fail')
					section.addResult(r)
		if section.results != []:
			comment = testReport.Result(
				'# For further information about the indentation rules which are used by this script, use the following command:\n#\n'\
				'#	 python3 <script-path/checkhtml.py> -h\n','comment')
			section.addResult(comment)
			Report.addSection(section)

	#############################################################################################
	Report = testReport.TestReport(f"{filePath}")
	htmlLines = html(filePath)
	self_closing_tags = getSelfClosingTags()
	tags = []
	filtered_tags = []

	#Creating tag object List
	for index, line in enumerate(htmlLines):
		tags_in_line = tagFinder(line)
		control_tag = ''
		for tag in tags_in_line:
			if (control_tag != 'script' and control_tag != 'style') or tag == f'style' or tag == f'script':
				tags.append({ "name": tag, "line": index+1, 'spaces': countSpaces(line), 'tabs': countTabs(line)}) # Append a dictionary { tag, line} in the list.

	#Filtering self closing tags
	filtered_tags = filterSelfClosingTags(tags)
	#List of indentation errors.
	indentation = []
	#List of unclosed tag errors.
	unclosed = []
	#Finding Unclosed tag errors
	while filtered_tags != []:
		response = findUnclosedTags(filtered_tags, unclosed)
		filtered_tags = response[0]
		unclosed = response[1]

	if __opFlags__ == '' or __opFlags__ == '-i':
		#Filtering self closing tags
		filtered_tags = filterSelfClosingTags(tags)
		#Finding indentation errors.
		while filtered_tags != []:
			response = findIndentationErrors(filtered_tags, indentation, unclosed)
			filtered_tags = response[0]
			indentation = response[1]

	#Printing Flag
	if __opFlags__ == '':
		flagUnclosed(unclosed, Report, __opErrors__)
		flagIndentation(indentation, Report, __opErrors__)
	elif __opFlags__ == '-u':
		flagUnclosed(unclosed, Report, __opErrors__)
	elif __opFlags__ == '-i':
		flagIndentation(indentation, Report, __opErrors__)

	if Report.sections != []:
		print(f'{Fore.MAGENTA}------------------------------------------{Style.RESET_ALL}')
		Report.print()
		print(f'{Fore.MAGENTA}------------------------------------------{Style.RESET_ALL}')

def html(html_path):
    try:
        with open(html_path, "r", encoding="utf-8") as html:
            a = html.readlines()
            return a
    except FileNotFoundError:
        print("🔴 Your input file could not be found.")

def toJsonFile(data, path):
    with open(path, 'w') as f:
        f.write(json.dumps(data))


# -h --help. To print a help message.
def help():
	main = (\
		f'\n{Fore.MAGENTA}###### checkhtml.py ######{Style.RESET_ALL}\n\n'\
		'This script is useful for checking the indentation an unclosed tag on a html or jsx.\n\n'\
		'Help index:'\
		)

	def help_run():
		running = (\
			f'{Fore.MAGENTA}## Running the tool ##{Style.RESET_ALL}\n\n'\
			'Running the script by using python3 and the [html-path]:\n'\
			'\n'\
			'	python3 <script-path> <html-path>\n'\
			'\n'\
			'For example, if you are located in the script folder:\n'\
			'\n'\
			'	python3 checkhtml.py <html-path>\n'\
			'\n')

		clean()
		print(running)
		input('Press enter to continue ...')
		help()

	def help_unclosed():
		unclosed = (\
			f'{Fore.MAGENTA}## Unclosed tags ##\n\n{Style.RESET_ALL}'\
			'The tool finds where are located the unclosed tags.\n'\
			'\n'\
			'	By default, the following self-closing tags are pre filtered in order to avoid the flag of the expected unclosed tag:\n'\
			'	* area  * base  * br  * col  * embed  * hr  * img  * input  * link\n'\
			'	* meta  * param  * source  * track  * wbr  * use  * ! (comment)\n')

		clean()
		print(unclosed)
		input('Press enter to continue ...')
		help()

	def help_indentation():
		indentation = (\
			f'{Fore.MAGENTA}## Indentation errors ##{Style.RESET_ALL}\n\n'\
			'This tool use two indentation criteria:\n'\
			'	1) Opening tag and closing tag are in the same line.\n'\
			'	2) Opening tag and closing tag are not in the same line but both have the the same indentation.\n'\
			'	3) The tool is "space" and "tab" sensitive, so it is recommended for the indentation, only use "spaces" or only use "tabs".\n')

		clean()
		print(indentation)
		input('Press enter to continue ...')
		help()

	def help_good_ind():
		indentation = (
			'✅ Examples of Good indentation\n\n'\
			'01--<div><p>content</p></div>\n'\
			'02\n'\
			'03--<div>\n'\
			'04----<p>content</p>\n'\
			'05--</div>\n'\
			'06\n'\
			'07--<div>\n'\
			'08----<p>\n'\
			'09------content\n'\
			'10----</p>\n'\
			'11--</div>\n'\
			'12\n')

		clean()
		print(indentation)
		input('Press enter to continue ...')
		help()

	def help_bad_ind():
		indentation = (
			'❌ Examples of Bad indentation\n\n'\
			'01--<div><p>\n'\
			'02----content</p></div>\n'\
			'03\n'\
			'04----<div>\n'\
			'05----<p>content</p>\n'\
			'06--</div>\n'\
			'07\n'\
			'08--<div>\n'\
			'09----<p>\n'\
			'10------content\n'\
			'11----</p>\n'\
			'12----</div>\n'\
			'13\n')

		clean()
		print(indentation)
		input('Press enter to continue ...')
		help()

	clean()

	op1 = menu.Option('About Running the tool', lambda: help_run())
	op2 = menu.Option('About Unclosed tags', lambda: help_unclosed())
	op3 = menu.Option('About Indentation errors', lambda: help_indentation())
	op4 = menu.Option('Examples of Good indentation', lambda: help_good_ind())
	op5 = menu.Option('Examples of Bad indentation', lambda: help_bad_ind())
	op6 = menu.Option('Exist', lambda: sys.exit())

	menu.NumericMenu(main).addOptions(op1, op2, op3, op4, op5, op6).ask()

# To clean the screan
def clean():
	print('\x1b[2J' + '\x1b[H')

def checkDependency():
	global Fore, Style
	try:
		import colorama
	except (ImportError, ModuleNotFoundError):
		print("colorama library couldn't be found. Installing...")
		os.system("python3 -m pip install colorama")
		import colorama
	from colorama import Fore, Style

def processArgs():
	cmd = cmdArguments.CmdArgs()

	op1 = menu.Option("-h",lambda: help())
	op2 = menu.Option("--help",lambda: help())
	op3 = menu.Option("-a",lambda: addSelfClosingTags(cmd.inputs))
	op4 = menu.Option("-d",lambda: delSelfClosingTags(cmd.inputs))
	op5 = menu.Option("-u",lambda: opFlags("-u"))
	op6 = menu.Option("-i",lambda: opFlags("-i"))
	op7 = menu.Option("-e",lambda: opErros("-e"))

	cmdMenu = menu.CommandMenu().addOptions(op1, op2, op3, op4, op5, op6, op7)
	error = ""
	def opFlags(op):
		global __opFlags__
		__opFlags__ = op
	def opErros(op):
		global __opErrors__
		__opErrors__ = f'{op}'

	if cmd.optionsQty() == 0 and cmd.inputsQty() == 0:
		help()
	elif cmd.optionsQty() == 0:
		e = False
		for input in cmd.inputs:
			if not input.isValidInputType(".html", ".jsx", '.inc', "dir"):
				error = f"🔴 The {input.path} is not a dir, HTML or JSX file."
				e = True
		if e == False:
			manageInputs(cmd.inputs)
	for i, cmd_opt in enumerate(cmd.options):
		if cmd_opt.isValidOption("-h", "--help", "-a", "-d", "-u", "-i", "-e"):
			if cmd_opt.name in ["-a", "-d", "-u", "-i", "-e"] and not cmd.isValidInputQty(1,-1):
				error = "🔴 At least one input is required."
				break
			elif cmd_opt.name in ["-h", "--help", "-a", "-d"]:
				cmdMenu.ask(cmd_opt.name)
				break
			elif cmd_opt.name in ["-u", "-i", "-e"]:
				cmdMenu.ask(cmd_opt.name)
				if i == len(cmd.options) - 1:
					manageInputs(cmd.inputs)
		else:
			print("\n🔴 The option is not valid. Valid options: [-h, --help, -a, -d, -u, -i, -e].")

	if error != "":
		print(error)

def manageInputs(inputs):
	html_jsx_Files = []
	for input in inputs:
		if os.path.isfile(input.path):
			file = directory.File(input.path)
			html_jsx_Files.append(file)
		elif os.path.isdir(input.path):
			dir = directory.Directory(input.path)
			html_jsx_Files.extend(dir.findFilesByExtension(['.html', '.jsx', '.inc']))
	if html_jsx_Files != []:
		for file in html_jsx_Files:
			checkSyntax(file.path)
	else:
		print("🔴 There is not any html or jsx file in the inputs.")

# Getting selfClosing Tags
def getSelfClosingTags():
	with open(f'{__pyPath__}.selfClosingTags.json', 'r') as f:
		self_closing_tags = f.read()
		return json.loads(self_closing_tags)

# -a . To add selfClosing Tags
def addSelfClosingTags(inputs):
	s_tags = getSelfClosingTags()
	for input in inputs:
		if not input.path in s_tags:
			s_tags.append(input.path)
			toJsonFile(s_tags, f'{__pyPath__}.selfClosingTags.json')
			print(f'🟢 "{input.path}" was successfully loaded as a self closing tag.')
		else:
			print(f'🔴 "{input.path}" was already loaded as a self closing tag.')
	print('')

# -d . To delete existing selfClosing Tags
def delSelfClosingTags(inputs):
	s_tags = getSelfClosingTags()
	for input in inputs:
		if input.path in s_tags:
			s_tags.remove(input.path)
			toJsonFile(s_tags, f'{__pyPath__}.selfClosingTags.json')
			print(f'🟢 "{input.path}" was successfully removed as a self closing tag.')
		else:
			print(f'🔴 There is not "{input.path}" saved as as a self closing tag.')
	print('')

def main():
	checkDependency()
	processArgs()

if __name__ == "__main__":
	main()

