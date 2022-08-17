import re
import os

from classes import menu
from classes import testReport
from classes import cmdArguments

#Global Variables
Report = testReport.TestReport('')

def checkSyntax(htmlLines):
	self_closing_tags = ["area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "path", "source", "track", "wbr", "!", "o:", "if"]
	tags = []
	filtered_tags = []

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
		tags_in_string = re.findall("<[^[>]*>|<.*$", html_string)  # Search all HTML tags
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
			n_open = 0
			n_close = 0
			for i, control_tag in enumerate(control_tag_list):
				if first_tag['name'] == control_tag['name'].replace('/',''):
					if isClosingTag(control_tag['name']):
						if n_open == n_close:
							filtered_tags.pop(i)
							unclosed = False
							break
						n_close = n_close + 1
					else:
						n_open = n_open + 1
				sub_tags_list.append(control_tag)

		while sub_tags_list != []:
			response = findUnclosedTags(sub_tags_list, sub_unclosed_tags)
			sub_tags_list = response[0]
			sub_unclosed_tags = response[1]

		for sub_unclosed_tag in sub_unclosed_tags:
			if not sub_unclosed_tag in unclosed_tag_list:
				unclosed_tags.append(sub_unclosed_tag)
		if unclosed and not first_tag in unclosed_tag_list:
			unclosed_tags.append(first_tag)

		return [filtered_tags, unclosed_tags]

	def findIndentationErrors(tag_list, error_list = [], unclosed_tags = []):
		filtered_tags = []
		for tag in tag_list:
			if not tag in unclosed_tags:
				filtered_tags.append(tag)
		first_tag = filtered_tags[0]
		control_tag_list = filtered_tags[1:]
		sub_tags_list = []
		sub_error_tags = []
		errorList = error_list
		errors = True
		#This function use two indentation criteria:
		#	1) opening tag and closing tag are in the same line
		#	2) opening tag and closing tag are not in the same line but both have the the same indentation.
		filtered_tags.pop(0)
		n_open = 0
		n_close = 0
		for i, control_tag in enumerate(control_tag_list):
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
			if (control_tag['spaces'] <= first_tag['spaces'] and control_tag['tabs'] <= first_tag['tabs']):
					if sub_tags_list != []:
						if sub_tags_list[-1]['line'] != control_tag['line']:
							sub_error_tags.append(('', control_tag))
					elif (first_tag['line'] != control_tag['line']):
						sub_error_tags.append(('', control_tag))

		while sub_tags_list != []:
			response = findIndentationErrors(sub_tags_list, sub_error_tags)
			sub_tags_list = response[0]
			sub_error_tags = response[1]

		for sub_error_tag in sub_error_tags:
			if not sub_error_tag in errorList:
				errorList.append(sub_error_tag)
		if errors and not (first_tag, control_tag) in errorList:
			errorList.append((first_tag, control_tag))

		return [filtered_tags, errorList]

	#Creating tag object List
	for index, line in enumerate(htmlLines):
		tags_in_line = tagFinder(line)
		for tag in tags_in_line:
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
	#Filtering self closing tags
	filtered_tags = filterSelfClosingTags(tags)
	#Finding indentation errors.
	while filtered_tags != []:
		response = findIndentationErrors(filtered_tags, indentation, unclosed)
		filtered_tags = response[0]
		indentation = response[1]
	#Saving Flags
	section_1 = testReport.Section("Unclosed tags")
	section_2 = testReport.Section("Indentation Issues")

	if unclosed == []:
		r = testReport.Result('No unclosed tags were found.', 'success')
		section_1.addResult(r)
	else:
		for error in unclosed:
			r = testReport.Result(f"Unclosed tag found in line {error['line']}. Check the syntax for the <{error['name']}> tag.", 'fail')
			section_1.addResult(r)

	if indentation == []:
		r = testReport.Result('No indentation errors were found.\n\n', 'success')
		section_2.addResult(r)
	else:
		for error in indentation:
			if error[0] == '':
				r = testReport.Result(
					'Indentation error found. Check the syntax for:\n'\
					f"	Tag: <{error[1]['name']}> in line {error[1]['line']}\n", 'fail')
				section_2.addResult(r)
			else:
				r = testReport.Result(
					'Indentation error found. Check the syntax for:\n'\
					f"	Opening tag: <{error[0]['name']}> in line {error[0]['line']}\n"\
					f"	Closing tag: <{error[1]['name']}> in line {error[1]['line']}\n", 'fail')
				section_2.addResult(r)
		comment = testReport.Result(
			'# For further information about the indentation rules which are used by this script, use the following command:\n#\n'\
			'#	 python3 <script-path/checkhtml.py> -h\n','comment')
		section_2.addResult(comment)

	global Report
	Report.addSection(section_1)
	Report.addSection(section_2)

def html(html_path):
    try:
        with open(html_path, "r", encoding="utf-8") as html:
            a = html.readlines()
            return a
    except FileNotFoundError:
        print("🔴 Your input file could not be found.")

def help():
    print("Help")

def processArgs():
	global Report
	cmd = cmdArguments.CmdArgs()
	if not cmd.optionsQty() == 0:
		cmd_opt = cmd.options[0]
	if not cmd.inputsQty() == 0:
		cmd_input = cmd.inputs[0]

	op1 = menu.Option("-h",lambda: help())
	op2 = menu.Option("--help",lambda: help())

	cmdMenu = menu.CommandMenu().addOptions(op1, op2)
	error = ""
	if cmd.isValidInputQty(0,1) and cmd.isValidOptQty(1):
		if cmd.inputsQty() == 0 :
			if cmd.optionsQty() == 0:
				help()
				pass
			elif  cmd_opt.isValidOption("-h", "--help"):
				cmdMenu.ask(cmd_opt.name)
				pass
			else:
				error = "🔴 The option is not valid. Please try [-h, --help]."
		elif  cmd.optionsQty() == 0:
			if cmd_input.isValidInputType(".html"):
				checkSyntax(html(cmd_input.path))
				Report.setName(os.path.split(cmd_input.path)[1])
				Report.print()
				pass
			else:
				error = "🔴 The input is not a HTML file."
	elif not cmd.isValidInputQty(1,1):
		error = "🔴 Only one input is allowed."
	elif not cmd.isValidOptQty(1):
		error = "🔴 Only one option is allowed."
	if error != "":
		print(error)

def main():
	processArgs()

if __name__ == "__main__":
	main()