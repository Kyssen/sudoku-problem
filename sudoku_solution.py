import copy
import time

M = 9
max = 0
start_time = time.time()

# whenever an impossible board state is reached, this error is raised
class ImpossibleSetup(Exception):
    pass

class Board:
    def __init__(self,b,isGrey,greyIndexes,isPurple,greys,purples):
        '''
        b stores the actual sudoku board with 0s for blank spots
        isGrey and isPurple are 9x9 lookup tables for whether or not a square is a part of a grey/purple line. 0 means it is not a part of one, a value of n for n>0 means that it is part of the line that has index n-1 in the list greys/purples
        greyIndexes is another lookup table for the greys. Since the order of the squares in the grey lines matters, squares which are part of grey lines store the index at which they are found in the list greys
        greys is a list of lines. Each line is a list of coordinates.
        purples is a list of lines. Each line is a set of coordinates
        p is a 9x9 lookup table for the "little numbers". At each coordinate it stores a set of numbers from 1 to 9, the possible numbers that can go in that square
        '''
        self.b = b #board
        self.M = len(b)
        self.isGrey = isGrey
        self.greyIndexes = greyIndexes
        self.isPurple = isPurple
        self.greys = greys
        self.purples = purples
        self.p = [] #possibilities
        for i in range(self.M):
            self.p.append([])
            for j in range(self.M):
                self.p[i].append({k for k in range(1,self.M+1)})
        self.updatePossibilities()

    def updatePossibilities(self):
        '''
        This function is just to update self.p when a Board is first created. It goes through the elements of self.b and re-adds them using the addNumber method 
        '''
        for i in range(self.M):
            for j in range(self.M):
                if self.b[i][j]!=0:
                    key = self.b[i][j]
                    self.b[i][j] = 0
                    self.addNumber(key,i,j)

    def removePossibility(self,key,row,col):
        '''
        Removes key from the little number possibilities of (row,col)
        '''
        if self.b[row][col]==0 and key in self.p[row][col]:
            self.p[row][col].remove(key)

    def checkPossibility(self,key,row,col):
        '''
        To be called asap after removePossibility. It checks if removing the possibility resulted in an error or more progress that can be made. It is a separate method because we need to remove the possibilities of a whole row/column/3x3square before we can start adding new numbers
        '''
        if self.b[row][col]==0 and key in self.p[row][col]:
            if len(self.p[row][col])==0:
                raise ImpossibleSetup
            if len(self.p[row][col])==1:
                (k,)=self.p[row][col]
                self.addNumber(k,row,col)

    def addNumber(self,key,row,col):
        '''
        Adds a new number into the board, it updates possibilities and adds new numbers automatically and recursively
        '''

        # if we attempt to override a nonempty key with a new value then there is an error
        if self.b[row][col] != 0:
            if self.b[row][col] != key:
                raise ImpossibleSetup
            return
        
        self.b[row][col] = key
        # removes the possibilities from the rows,columns, and 3x3squares
        for i in range(self.M):
            self.removePossibility(key,row,i)
            self.removePossibility(key,i,col)
        for i in range(row-(row%3),row-(row%3)+3):
            for j in range(col-(col%3),col-(col%3)+3):
                self.removePossibility(key,i,j)
        for i in range(self.M):
            self.checkPossibility(key,row,i)
            self.checkPossibility(key,i,col)
        for i in range(row-(row%3),row-(row%3)+3):
            for j in range(col-(col%3),col-(col%3)+3):
                self.checkPossibility(key,i,j)

        # if it is part of a grey square, it adds a number to its counterpart square
        if self.isGrey[row][col]!=0:
            g = self.isGrey[row][col]-1
            line = greys[g]
            mirrorIndex = len(line)-self.greyIndexes[row][col]-1
            mirrorRow,mirrorCol = line[mirrorIndex]
            self.addNumber(key,mirrorRow,mirrorCol)
        # if it is part of a purple square, it updates the line to make sure nothing impossible has happened and to remove impossible possibilities
        elif self.isPurple[row][col]!=0:
            p = self.isPurple[row][col]-1
            line = purples[p]
            for r,c in line:
                if self.b[r][c] != 0 and (r!=row or c!=col):
                    if self.b[r][c]==key or self.b[r][c]<=key-len(line) or self.b[r][c]>=key+len(line):
                        raise ImpossibleSetup
                else:
                    for i in range(0,key-len(line)+1):
                        self.removePossibility(i,r,c)
                    for i in range(key+len(line),self.M):
                        self.removePossibility(i,r,c)
                    for i in range(0,key-len(line)+1):
                        self.checkPossibility(i,r,c)
                    for i in range(key+len(line),self.M):
                        self.checkPossibility(i,r,c)

    def checkGroup(self,group):
        '''
        given a group (either a row column or 3x3 square), it checks if any of the numbers from 1-9 have only ONE possible square they can go in. If so, we add that number
        '''
        for num in range(1,10):
            l = []
            for i in group:
                if self.b[i[0]][i[1]]==num:
                    l.append(i)
            if len(l)==1:
                self.addNumber(num,l[0][0],l[0][1])

    def check(self):
        '''
        runs checkGroup on every group
        '''
        for i in range(self.M):
            self.checkGroup([(i,j) for j in range(self.M)])
            self.checkGroup([(j,i) for j in range(self.M)])
        for i in range(3):
            for j in range(3):
                group = []
                for k in range(i*3,i*3+3):
                    for l in range(j*3,j*3+3):
                        group.append((k,l))
                self.checkGroup(group)

    def recurse(self,level,greysLeft):
        '''
        The primary recursion that solves the sudoku. Returns a solved board

        level is the level of recursion, only for debugging
        greysLeft is a boolean that stores whether or not there are empty squares that are part of grey lines remaining
        '''

        # addNumber already gets rid of obvious pathways like if a number only has 1 possibility left or if a number is part of a line. This helps get rid of some more obvious pathways
        self.check()
        self.debug(level)

        # we will look for a square to start guessing from. To choose the optimal square, we find a square that is part of a grey line with the minimal number of possibilities
        min = 100
        minCoords = (0,0)
        if greysLeft:
            for i in self.greys:
                for r,c in i:
                    if self.b[r][c]==0 and len(self.p[r][c])<min:
                        min = len(self.p[r][c])
                        minCoords = (r,c)
            if min==100:
                # if we run out of grey squares, set this to false
                greysLeft = False
        # if there are no more grey squares, look for the square with the minimal possibilities. Ties are broken by whether or not a square is purple
        if not greysLeft:
            for i in range(self.M):
                for j in range(self.M):
                    if self.b[i][j]==0:
                        if len(self.p[i][j])<min or (len(self.p[i][j])==min and self.isPurple[i][j]!=0):
                            min = len(self.p[i][j])
                            minCoords = (i,j)

        # if no minimum is found, the board is solved and we return it
        if min==100:
            return self.b
        
        # our square to guess from is stored in minCoords. For every possibility, we create a new Board, assume the possibility is correct, and recurse again
        for k in self.p[minCoords[0]][minCoords[1]]:
            testBoard = copy.deepcopy(self)
            try:
                testBoard.addNumber(k,minCoords[0],minCoords[1])
                return testBoard.recurse(level+1,greysLeft)
            except ImpossibleSetup:
                pass
        # if no possibilities worked, this is an impossible setup
        raise ImpossibleSetup

    def debug(s,level):
        global max
        global start_time
        if level>max:
            max = level
            print("new maximum",max,(time.time() - start_time))

        if level<11:
            print("level",level,(time.time() - start_time))
        with open("output.txt","a") as f:
            f.write(f"{str(level)}\n")
            for i in s.b:
                f.write(f"{str(i)}\n")
            f.write("\n")
        '''
        for i in s.isGrey:
            print(i)
        print()
        for i in s.isPurple:
            print(i)
        print()
        for i in s.greyIndexes:
            print(i)
        print()
        for i in s.p:
            for j in i:
                print(j,end="\t")
            print()'''

# reading the input
board = []
greyBoard = []
greyIndexes = []
purpleBoard = []
greys = []
purples = []
for i in range(M):
    greyBoard.append([0]*M)
    greyIndexes.append([0]*M)
    purpleBoard.append([0]*M)
with open("input.txt","r") as f:
    for i in range(M):
        line = f.readline()[:-1].split(" ")
        board.append([int(i) for i in line])
    nums = f.readline().split(" ")
    numGrey = int(nums[0])
    numPurple = int(nums[1])
    for i in range(numGrey):
        coords = f.readline().split(" ")
        greys.append([])
        for j in range(len(coords)):
            c = coords[j].split(",")
            row = int(c[0])
            col = int(c[1])
            greyBoard[row][col] = i+1
            greys[i].append((row,col))
            greyIndexes[row][col] = j
    for i in range(numPurple):
        coords = f.readline().split(" ")
        purples.append(set())
        for j in coords:
            c = j.split(",")
            row = int(c[0])
            col = int(c[1])
            purpleBoard[row][col] = i+1
            purples[i].add((row,col))
            
s = Board(board,greyBoard,greyIndexes,purpleBoard,greys,purples)
with open("output.txt","w") as f:
    f.write("")

# main function run
print(s.recurse(0,True))

