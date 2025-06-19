import wikipedia
import sys
#Search
def searchWikipedia(term):
	pageIds = wikipedia.search(term) #Search wikipedia
	pages = [] #create empty list
	for pageId in pageIds:
		try:
			page = wikipedia.page(pageId) #Get page
			pages.append(page) #Add page to the list
		except:
			print("Oups: could not parse the page:", pageId) #prints a warning
			pass
	if len(pages) >= 0:
		for page in pages:
			print("title: " + page.title + " URL: " + page.url + " Content: " +
page.content)
	else:
		return "No results!" #no results available
arguments = "".join(sys.argv[1:])
searchWikipedia(arguments)
