import sys
dirs = sys.modules["__main__"].dirs

def launch(txt,tokens):
	# Multi-line input is considered as source code
	# Single-line input is considered as a filename
	import subprocess
	if txt.count('\n')>1:
		inputData = txt
	else:
		inputFile = txt.strip()%(dirs)
		inputData = open(inputFile).read()
	try:
		child = subprocess.Popen(tokens,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	except:
		return "Sorry! Cannot execute command: "+str(tokens)
	out,err = child.communicate(input=bytearray(inputData,"utf-8"))
	if err: 
		print("Sorry!",err)
		return err
	return out.decode('utf-8')

def dotdot(txt): 	return launch(txt,["dot","-Tsvg"])
def plantuml(txt):  return launch(txt,["java","-jar","%(sys)s/plugins/plantuml.jar"%(dirs),"-tsvg","-pipe"])
