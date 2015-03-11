# Intern Developer Project
# Back up 4

# using python wrapper for Twitter API from https://github.com/bear/python-twitter
import twitter, string, time, os, json
from Tkinter import *
from eventBasedAnimationClass import EventBasedAnimationClass

class MyButton(object):

    def __init__(self, width, height, x, y, text, command):
        self.width = width
        self.height = height
        self.text = text
        self.x = x
        self.y = y
        self.command = command
        self.fill = "white"
        self.textColor = "black"


    # x and y is the center
    def draw(self, canvas): 

        canvas.create_rectangle(self.x-self.width/2.0, self.y-self.height/2.0, self.x+self.width/2.0, self.y+self.height/2.0, fill=self.fill)
        canvas.create_text(self.x, self.y, text=self.text, fill=self.textColor)

    def highlight(self, canvas, x, y):
        if self.collidePoint(x, y):
            self.fill = "black"
            self.textColor = "white"
        else:
            self.fill = "white"
            self.textColor = "black"
            

    def collidePoint(self, x, y):
        leftBound = self.x - self.width/2.0
        rightBound = self.x + self.width/2.0
        upperBound = self.y - self.height/2.0
        lowerBound = self.y + self.height/2.0

        return leftBound <= x <= rightBound and upperBound <= y <= lowerBound

    def click(self, x, y):
        if self.collidePoint(x, y):
            self.command()
            return True
        return False

    def setText(self, text):
        self.text = text

class TwitterAnalysis(EventBasedAnimationClass):

    def __init__(self):
        keys = TwitterAnalysis.readFile("password.txt").split("\n")
        self.api = twitter.Api(consumer_key=keys[0], 
                  consumer_secret=keys[1], 
                  access_token_key=keys[2], 
                  access_token_secret=keys[3])
        super(TwitterAnalysis, self).__init__(1000, 500)

    # from class notes
    @staticmethod
    def writeFile(filename, contents, mode="wt"):
        with open(filename, mode) as fout:
            fout.write(contents)

    # from class notes
    @staticmethod
    def readFile(filename, mode="rt"):
        with open(filename, mode) as fin:
            return fin.read()

    @staticmethod
    def getCommonWords():
        # words taken from https://www.englishclub.com/vocabulary/
        words = TwitterAnalysis.readFile("commonWords.txt")
        words = words.split("\n")
        words = set(words)
        return words

    def initVariables(self):
        self.wordCounts = dict()
        self.mostCommonSource = dict()
        self.user = self.numFriends = self.numFollowers = None
        self.since_id = None
        self.statuses = []
        self.statusUpdates = []
        self.tweets = []
        self.activeTimes = [0]*24 # 24 hours in a day
        self.numLinks = self.numTweets = 0
        self.topWordsNum = 10 # default is top ten words
        self.topAppsNum = 1 # default is top app
        self.userString = "" # for collecting user's keystrokes
        self.sourcesString = ""
        self.wordsString = ""
        self.start = self.error = True
        self.results = self.search = False
        self.graph = False
        self.drawApp = False
        self.drawWords = False
        self.commonWords = TwitterAnalysis.getCommonWords()

    def initGraphics(self):

        self.topMargin = 80
        self.margin = 50
        self.cx = self.width/2.0
        self.cy = self.height/2.0
        self.canvas.bind("<Motion>", lambda event: self.onMouseMotionWrapper(event))
        self.printables = set(string.printable)
        self.whitespaces = set(string.whitespace)

    def initButtons(self):
        self.searchButton = MyButton(width=50, height=20, text="Search", 
            x=self.cx, y=self.cy+self.margin, command=self.searchWrapper)
        self.timesGraphButton = MyButton(width=230, height=80, text="", 
            x=self.width/4.0, y=self.cy + self.margin, command=self.graphWrapper)
        self.mostFreqWordButton = MyButton(width=230, height=80, text="",
            x=self.cx, y=self.cy + self.margin, command=self.mostFreqWordWrapper)
        self.mostCommonAppButton = MyButton(width=230, height=80, text="",
            x=3*self.width/4.0, y=self.cy + self.margin, command=self.mostCommonAppWrapper)
        self.searchAgainButton = MyButton(x=self.cx, y=self.topMargin, 
            command=self.initVariables, width=100, height=20, text="Search Again")
        self.returnToResultsButton = MyButton(x=self.width - self.margin, y=self.margin/2.0,
            width=100, height=20, text="Return to Results", command=self.returnToResults)
        self.refreshTweetsButton = MyButton(x=self.cx-120, y=self.topMargin,
            command=self.updateTweets, width=100, height=20, text="Refresh Data")
        self.saveDataButton = MyButton(x=self.cx+120, y=self.topMargin,
            command=self.saveData, width=100, height=20, text="Save Data")

    def updateTweets(self):
        self.getTweetUpdates()
        self.loopThroughStatuses(self.statuses)

    def initAnimation(self):
        self.initVariables()
        self.initGraphics()
        self.initButtons()    

    def returnToResults(self):
        self.graph = False
        self.drawApp = False
        self.drawWords = False            

    def onMouseMotionWrapper(self, event):
        self.onMouseMotion(event)
        self.redrawAll()

    def onMouseMotion(self, event):

        (x, y) = (event.x, event.y)
        if self.start:
            self.searchButton.highlight(self.canvas, x, y)
        elif self.results: 
            self.timesGraphButton.highlight(self.canvas, x, y)
            self.searchAgainButton.highlight(self.canvas, x, y)
            self.mostCommonAppButton.highlight(self.canvas, x, y)
            self.mostFreqWordButton.highlight(self.canvas, x, y)
            self.returnToResultsButton.highlight(self.canvas, x, y)
            self.refreshTweetsButton.highlight(self.canvas, x, y)
            self.saveDataButton.highlight(self.canvas, x, y)

    def graphWrapper(self): self.graph = True

    def mostFreqWordWrapper(self): self.drawWords = True

    def mostCommonAppWrapper(self): self.drawApp = True

    def drawPrelimResults(self):
        user = "%s" % self.user.screen_name
        self.canvas.create_text(self.cx, self.margin, text=user, font="Georgia 20 bold")
        
        basicInfo = "\t  User id: %d \n\t  Friends: %d \n\t  Followers: %d \n" % (self.user.id, self.numFriends, self.numFollowers)
        linkRatio = "Ratio of tweets with links to total tweets: %d:%d\n" % self.getLinkRatio()
        self.canvas.create_text(self.cx, self.topMargin+2*self.margin, text=basicInfo+linkRatio, font="Georgia 16")
        self.searchAgainButton.draw(self.canvas)
        self.timesGraphButton.draw(self.canvas)
        self.mostCommonAppButton.draw(self.canvas)
        self.mostFreqWordButton.draw(self.canvas)
        self.refreshTweetsButton.draw(self.canvas)
        self.saveDataButton.draw(self.canvas)

    def saveData(self):

        basicUserData = {"username": self.user.screen_name, "user_id": self.user.id, 
        "friends_count": self.numFriends, "followers_count": self.numFollowers,
        "links_count": self.numLinks, "active_times": self.activeTimes,
        "most_common_sources": self.mostCommonSource, "word_counts": self.wordCounts,
        "top_ten_words": self.topNWords()[0]}
        data = json.dumps(basicUserData)
        path = "Twitter Data" + os.sep + "%sData.txt" % self.user.screen_name
        if not(os.path.exists("Twitter Data")):
            os.makedirs("Twitter Data")
        TwitterAnalysis.writeFile(path, data)
        print "Data saved!"


    def topNWordsString(self):
        words, freqs = self.topNWords()
        res = ""
        for i in xrange(len(words), 0, -1):
            res += "%d.) %s - %d\n" % (len(words) - i + 1, words[i-1], freqs[i-1])
        return res

    def topNAppsString(self, sources, freqs):
        # words, freqs = self.topNApps()
        res = ""
        for i in xrange(len(sources), 0, -1):
            res += "%d.) %s - %d\n" % (len(sources) - i + 1, sources[i-1], freqs[i-1])
        return res

    # implement getting real time updates
    def getTweetUpdates(self): 

        newStatuses = []
        user = self.user.screen_name
        maxID = None
        while True:

            statuses = self.api.GetUserTimeline(screen_name=user, max_id=maxID, since_id=self.since_id)
            newStatuses += statuses
            if len(statuses) == 0:
                break
            maxID = statuses[-1].id - 1
        self.statuses = newStatuses + self.statuses
        self.numTweets = len(self.statuses)
        self.statusUpdates = newStatuses

    # given user which is a string; can either be numerical ID/screenname 
    # maxID (int) is the tweet ID of the lowest tweet 
    def getTweets(self):

        maxID = None
        user = self.user.screen_name
        while True:
            
            statuses = self.api.GetUserTimeline(screen_name=user, max_id=maxID)
            self.statuses += statuses
            if len(statuses) == 0:
                break
            for s in statuses:
                self.tweets.append(s.text)
            maxID = statuses[-1].id - 1

        self.since_id = self.statuses[0].id
        
        self.numTweets = len(self.statuses)

    def getWordFrequency(self):
        
        for tweet in self.tweets:
            tweet = tweet.lower().split() # make everything lowercase and split by word
            if tweet[0] == "rt": continue
            for word in tweet: 
                # excluding common prepositions, conjunctions and pronouns
                if word in self.commonWords: continue 
                elif word in self.wordCounts:
                    self.wordCounts[word] += 1
                else:
                    self.wordCounts[word] = 1

    @staticmethod
    def insert(freq, freqs, word, words):

        i = 0
        while (i < len(freqs) and freqs[i] < freq):
            i += 1
        newFreqs = freqs[:i] + [freq] + freqs[i:]
        newFreqs = newFreqs[1:]
        newWords = words[:i] + [word] + words[i:]
        newWords = newWords[1:]
        return newFreqs, newWords

    def topNWords(self):

        self.getWordFrequency()
        # words, freqs = self.topN(self.wordCounts, self.topWordsNum)
        # print "top 10 words"
        # return words, freqs
        words = [0]*self.topWordsNum
        freqs = [0]*self.topWordsNum
        minCount = 0
        for word in self.wordCounts:
            freq = self.wordCounts[word]
            if freq > minCount:
                freqs, words = TwitterAnalysis.insert(freq, freqs, word, words)
                minCount = min(freqs)
        return words, freqs

    def sortApps(self):

        n = len(self.mostCommonSource)
        sources = [0]*n
        freqs = [0]*n
        for source in self.mostCommonSource:
            freq = self.mostCommonSource[source]
            freqs, sources = TwitterAnalysis.insert(freq, freqs, source, sources)
        return sources, freqs

    # returns bool- user was found or not
    def setUser(self, user):

        try:
            if not(user[0].isdigit()):
                self.user = self.api.GetUser(screen_name=user)
            else:
                self.user = self.api.GetUser(user_id=int(user))
            
            self.numFriends = self.user.friends_count
            self.numFollowers = self.user.followers_count
            name = self.user.screen_name
            return True
        except:
            self.userString = ""
            return False

    def getActiveTimes(self, tweet):
        timeStamp = tweet.created_at
        time = timeStamp.split()[3]
        hour = int(time.split(":")[0])
        hour -= 5 # convert to EST
        if hour < 0 : hour = hour + 24 # account for wrap around
        self.activeTimes[hour] += 1

    # add the total number of links or just that its there?
    def countLinks(self, tweet):
        self.numLinks += len(tweet.urls)

    def getSources(self, tweet):
        source = tweet.GetSource().split(">") # gets rid of left chunk
        source = source[1].split("<") # gets rid of right chunk
        source = source[0].split("\\")
        source = source[0]
        if source in self.mostCommonSource:
            self.mostCommonSource[source] += 1
        else:
            self.mostCommonSource[source] = 1

    def getMostCommonSource(self):

        sources, freqs = self.sortApps()
        self.sourcesString = self.topNAppsString(sources, freqs)
        mostCommon = sources[-1]
        return mostCommon

    def drawWordList(self):

        text = "Top 10 Words Used"
        subheading = "Excludes common prepositions, pronouns, conjunctions, and interrogatives"
        self.canvas.create_text(self.cx, self.topMargin, text=subheading, font="Georgia 10")
        self.canvas.create_text(self.cx, self.margin, text=text, font="Georgia 20")
        self.canvas.create_text(self.cx, self.cy, text=self.wordsString, font="Georgia 12")
        self.returnToResultsButton.draw(self.canvas)

    def drawSources(self):

        text = "All Sources Used for Tweeting"
        self.canvas.create_text(self.cx, self.margin, text=text, font="Georgia 20")
        self.canvas.create_text(self.cx, self.cy - self.topMargin, text=self.sourcesString, font="Georgia 12")
        self.returnToResultsButton.draw(self.canvas)

    def getLinkRatio(self):
        
        gcd = 1
        a = self.numLinks
        b = self.numTweets
        while (b > 0): (a, b) = (b, a%b)
        return (self.numLinks/a, self.numTweets/a)

    def loopThroughStatuses(self, statuses):

        numHours = 24
        self.activeTimes = [0]*numHours
        self.numLinks = 0
        for tweet in statuses:
            self.getActiveTimes(tweet)
            self.countLinks(tweet)
            self.getSources(tweet)
        self.mostActive()
        self.mostFreqs()
    
    def mostFreqs(self):

        #getting most frequently used words
        mostFreq, freqs = self.topNWords()
        text = "Most Common Word Used: \n\t%s" % mostFreq[-1]
        self.mostFreqWordButton.setText(text)
        self.wordsString = self.topNWordsString()

        #getting most freqently used apps
        mostCommonSource = self.getMostCommonSource()
        text = "Most Common App Used to Tweet: \n\t%s" % mostCommonSource
        self.mostCommonAppButton.setText(text)     

    # gets index of max; index represents starting hour for hour long range
    def mostActive(self): 
        maxTweetsPerHr = max(self.activeTimes)
        mostActive = self.activeTimes.index(maxTweetsPerHr)
        text = "Most Active Time Range (EST): \n\t%d:00 - %d:00" % (mostActive, (mostActive + 1) % 24)
        self.timesGraphButton.setText(text)
        return text
 
    def xAxis(self, startx, starty):

        lengthx = self.width - 1.5*self.margin
        xaxis = self.canvas.create_line(startx, starty, startx + lengthx, starty, width=3)
        numHours = 24
        incrementx = lengthx/(1.0*numHours + 1)
        startx = startx + incrementx
        for i in xrange(numHours):
            self.canvas.create_line(startx, starty, startx, starty + 5)
            label = "%d:00" % (i)
            self.canvas.create_text(startx, starty + 5, text=label, anchor=N, font="Georgia 8")
            startx += incrementx   

        self.canvas.create_text(self.cx, self.height - self.margin/2.0, text="Time (EST)", font="Georgia 10") 

        return incrementx

#fix this
    def yAxis(self, startx, starty):

        maxTweetsPerHr = max(self.activeTimes)
        numSteps = 10
        incrementVal = float(maxTweetsPerHr)/numSteps
        # rounds the number up to the nearest multiple of five
        incrementVal = (int(incrementVal/5) + 1)*5
        lengthy = self.height - self.margin - self.topMargin
        incrementy = 1.0*lengthy/numSteps
        label = 0

        yaxis = self.canvas.create_line(startx, starty, startx, starty - lengthy, width=3)
        self.canvas.create_text(startx, starty - lengthy - 5, text="Number of Tweets", anchor=SW, font="Georgia 10")

        for i in xrange(numSteps):
            self.canvas.create_line(startx, starty, startx - 5, starty)
            self.canvas.create_text(startx - 5, starty, text=str(label), anchor=E, font="Georgia 10")
            starty -= incrementy
            label += incrementVal

        return incrementy, incrementVal

    def drawPoints(self, startx, starty, incrementx, incrementy, incrementVal):

        numHours = 24
        r = 2
        startx += incrementx
        for i in xrange(numHours):
            label = "%d" % self.activeTimes[i]
            y = starty - (1.0*self.activeTimes[i]/incrementVal)*incrementy
            self.canvas.create_rectangle(startx - r, y - r, startx + r, y + r, fill="black")
            self.canvas.create_text(startx, y, text=label, anchor=S, font="Georgia 10")
            startx += incrementx

    def drawActiveTimesGraph(self):

        self.canvas.create_text(self.cx, self.margin, text="Cumulative Tweets Per Hour", font="Georgia 16")
        startx = self.margin
        starty = self.height - self.margin
        incrementx = self.xAxis(startx, starty)
        incrementy, incrementVal = self.yAxis(startx, starty)
        self.drawPoints(startx, starty, incrementx, incrementy, incrementVal)
        self.returnToResultsButton.draw(self.canvas)

    def onMousePressed(self, event):
        x, y = event.x, event.y
        if self.start:
            self.searchButton.click(x, y)    
        elif self.results:
            self.searchAgainButton.click(x, y)
            self.timesGraphButton.click(x, y)
            self.returnToResultsButton.click(x, y)
            self.refreshTweetsButton.click(x, y)
            self.saveDataButton.click(x, y)
            self.mostCommonAppButton.click(x, y)
            self.mostFreqWordButton.click(x, y)

    def onKeyPressed(self, event): 

        if (event.char in self.printables) and not(event.char in self.whitespaces):
            self.userString += event.char
        elif event.keysym == "BackSpace":
            self.userString = self.userString[:-1]
        elif event.keysym == "Return":
            self.searchWrapper()

    def drawStartScreen(self): 

        self.canvas.create_text(self.cx, self.margin, text="Twitter Data", font="Georgia 20 bold")
        self.canvas.create_text(self.cx, self.topMargin, 
            text="Obtain general statistics of a Twitter user", font="Georgia 12")
        self.canvas.create_text(self.cx, self.cy - self.margin, 
            text="Please enter a username or user id: ", font="Georgia 20")
        self.canvas.create_text(self.cx, self.cy, text=self.userString, font="Georgia 14")        
        self.searchButton.draw(self.canvas)

    def searchWrapper(self):
        self.error = self.setUser(self.userString)
        if self.error:
            self.search = True
            self.start = False
            self.redrawAll()
            time.sleep(2)
            self.getTweets()
            self.loopThroughStatuses(self.statuses)
            self.search = False
            self.results = True

    def redrawAll(self):

        self.canvas.delete(ALL)
        if self.start:
            self.drawStartScreen()
            if not(self.error):
                self.canvas.create_text(self.cx, self.margin, text="User not found, please try again")
        elif self.search:
            print "Please wait while tweets are being processed..."
            self.canvas.create_text(self.cx, self.cy, text="Please wait while tweets are being processed...", font="Georgia 16")
        elif self.graph:
            self.drawActiveTimesGraph()
        elif self.drawApp:
            self.drawSources()
        elif self.drawWords:
            self.drawWordList()
        elif self.results:
            self.drawPrelimResults()

def twitterAnalysis():
    app = TwitterAnalysis()
    app.run()

twitterAnalysis()
