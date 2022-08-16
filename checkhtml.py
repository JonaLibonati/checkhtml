import re

from classes import menu
from classes import testReport
from classes import cmdArguments

#Global Variables
Report = testReport.TestReport('')

def checkSyntax(htmlLines):
	self_closing_tags = ["base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr", "!", "o:", "if", "path"]
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
			else:
				break
		return i

	def countTabs(line):
		i = 0
		for char in line:
			if char == '	':
				i += 1
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


	def findUnclosedTags(errorList, unclosed_tag_list = []):
		error_list = errorList
		first_error = errorList[0]
		control_error_list = errorList[1:]
		sub_error_list = []
		sub_unclosed_tags = []
		unclosed_tags = unclosed_tag_list
		unclosed = True

		error_list.pop(0)
		if len(error_list) > 0 and not isClosingTag(first_error['name']) and not first_error in unclosed_tag_list:
			n_open = 0
			n_close = 0
			for i, control_error in enumerate(control_error_list):
				if first_error['name'] == control_error['name'].replace('/',''):
					if isClosingTag(control_error['name']):
						if n_open == n_close:
							error_list.pop(i)
							unclosed = False
							break
						n_close = n_close + 1
					else:
						n_open = n_open + 1
				sub_error_list.append(control_error)

		while sub_error_list != []:
			response = findUnclosedTags(sub_error_list, sub_unclosed_tags)
			sub_error_list = response[0]
			sub_unclosed_tags = response[1]

		for sub_unclosed_tag in sub_unclosed_tags:
			if not sub_unclosed_tag in unclosed_tag_list:
				unclosed_tags.append(sub_unclosed_tag)
		if unclosed and not first_error in unclosed_tag_list:
			unclosed_tags.append(first_error)

		return [error_list, unclosed_tags]

	def findIndentationErrors(tag_list, unclosed_tags, error_list = []):
		filtered_tags = tag_list
		first_tag = tag_list[0]
		control_tag_list = tag_list[1:]
		errorList = error_list
		error_exist = True
		#This function use two indentation criteria:
		#	1) opening tag and closing tag are in the same line
		#	2) opening tag and closing tag are not in the same line but both have the the same indentation.
		filtered_tags.pop(0)
		for i, control_tag in enumerate(control_tag_list):
			if isClosingTag(first_tag['name']):
				break
			elif first_tag['name'] == control_tag['name'].replace('/',''):
				if first_tag['spaces'] == control_tag['spaces'] and first_tag['tabs'] == control_tag['tabs'] and isClosingTag(control_tag['name']):
					filtered_tags.pop(i)
					error_exist = False
					break
				elif first_tag['spaces'] >= control_tag['spaces'] and first_tag['tabs'] >= control_tag['tabs'] and first_tag['line'] != control_tag['line'] and not isClosingTag(control_tag['name']):
					break

		if error_exist and not first_tag in unclosed_tags:
			errorList.append(first_tag)

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
		response = findIndentationErrors(filtered_tags, unclosed, indentation)
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
			r = testReport.Result(f"Indentation errors found in line {error['line']}. Check the syntax for the <{error['name']}> tag.", 'fail')
			section_2.addResult(r)
		comment = testReport.Result(
			'\n=============================================\n'\
			'\nThis tool use two indentation criteria:\n'\
			'1) opening tag and closing tag are in the same line.\n'\
			'2) opening tag and closing tag are not in the same line but both have the the same indentation.\n\n'\
			'✅ Examples of Good indentation\n'\
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
			'12\n\n'\
			'❌ Examples of Bad indentation\n'\
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
			'13\n\n'\
			,'comment')
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
	global Report
	processArgs()
	#Report.setName(os.path.split(dm_path)[1])
	Report.print()

if __name__ == "__main__":
	main()