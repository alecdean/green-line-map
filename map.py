import mbtaAPI
import util

from var import *

class Map(object):
    def __init__(self):
        self.stops = Stops()
        self.trains = {}

    def tick(self):
        self.trains = Trains()

        self.trains.update(self.stops.stops)

    def textMap(self):

        def marker(i):
            if self.trains.get(i) and len(self.trains.get(i)):
                flags = [False, False]
                for t in self.trains.get(i):
                    flags[t.direction] = True
                if flags[0] and flags[1]:
                    return 'X' if self.stops.get(i) else 'x'
                elif flags[0]:
                    return '(' if self.stops.get(i) else '<'
                else:
                    return ')' if self.stops.get(i) else '>'
            if self.stops.get(i):
                return 'o'
            else:
                return '-'

        return "GreenLine - C" + ' ' + ''.join(map(marker, range(TOTAL_NUM_PIXELS)))


class Stop(object):
    def __init__(self, id, name, location):
        self.name = name
        self.location = location
        self.pixelLocation = -1
        self.id = id

    def __str__(self):
        return '{'+self.name+', '+str(self.pixelLocation)+'}'
        

class Stops(object):
    def __init__(self):
        self.stops = {}
        self.pixelList = []
        for i in range(TOTAL_NUM_PIXELS):
            self.pixelList.append([])

        resp = mbtaAPI.getStops()['data']
        for stop in resp:
            lat = stop['attributes']['latitude']
            lon = stop['attributes']['longitude']
            loc = (lat, lon)
            stopObj = Stop(stop['id'], stop["attributes"]['name'], loc)
            self.stops[stop['id']] = stopObj

        totalDist = 0
        for i in range(len(STOP_LIST)-1):
            stopA = self.stops[STOP_LIST[i]]
            stopB = self.stops[STOP_LIST[i+1]]
            totalDist += util.distTwoPoints(stopA.location, stopB.location)

        for i in range(len(STOP_LIST)-1):
            stopA = self.stops[STOP_LIST[i]]
            stopB = self.stops[STOP_LIST[i+1]]
            dist = util.distTwoPoints(stopA.location, stopB.location)

            if i == 0:
                stopA.pixelLocation = 0

            pixDist = round(TOTAL_NUM_PIXELS * dist / totalDist)
            stopB.pixelLocation = stopA.pixelLocation + pixDist

            if stopB.pixelLocation == TOTAL_NUM_PIXELS:
                stopB.pixelLocation -= 1

            self.pixelList[stopB.pixelLocation].append(stopB)

    def __str__(self):
        res = ""
        for stop in self.stops:
            res += str(self.stops[stop])+'\n'
        return res

    def get(self, i):
        return self.pixelList[i]

            
class Train(object):
    def __init__(self, location, direction):
        self.location = location
        self.direction = direction
        self.prev = ""
        self.next = ""

    def __str__(self):
        return "{"+str(self.location)+', '+str(self.direction)+', '+str(self.prev)+', '+str(self.next)+'}'


class Trains(object):
    def __init__(self):
        self.trains = {}
        self.pixelList = []
        for i in range(TOTAL_NUM_PIXELS):
            self.pixelList.append([])

    def __str__(self):
        res = ""
        for t in self.trains:
            res += str(self.trains[t]) + '\n'

        for p in self.pixelList:
            res += str(p)
        return res

    def getPrediction(self, id):
        resp = mbtaAPI.getPrediction(id)
        l = []
        for train in resp['data']:  
            l.append(train['attributes']['arrival_time'])
        print(l)
        return l
    
    def update(self, stops):
        resp = mbtaAPI.getTrains()['data']
        self.pixelList = []
        for i in range(TOTAL_NUM_PIXELS):
            self.pixelList.append([])
        
        for train in resp:
            lat = train['attributes']['latitude']
            lon = train['attributes']['longitude']
            loc = (lat, lon)
            status = train['attributes']['current_status']

            t = Train(loc, train['attributes']['direction_id'])
            self.trains[train['id']] = t

        for train in self.trains:
            closest = ("", "")
            minDist = 10000
            for i in range(len(STOP_LIST)-1):
                t = self.trains[train]
                stopA = stops[STOP_LIST[i]]
                stopB = stops[STOP_LIST[i+1]]
                distToSegment = util.distPointLine(t.location, stopA.location, stopB.location)

                if distToSegment < minDist:
                    minDist = distToSegment
                    # closest = (stopA, stopB) if t.direction == 1 else (stopB, stopA)
                    closest = (stopA, stopB)

            t.prev = closest[0]
            t.next = closest[1]

        for train in self.trains:
            prevStop = self.trains[train].prev.location
            nextStop = self.trains[train].next.location
            distPrev = util.distTwoPoints(self.trains[train].location, prevStop)
            # distNext = util.distTwoPoints(self.trains[train].location, self.trains[train].next)
            distSegment = util.distTwoPoints(nextStop, prevStop)

            prevPixel = self.trains[train].prev.pixelLocation
            nextPixel = self.trains[train].next.pixelLocation
            segmentPixels = nextPixel - prevPixel
            pixel = round(segmentPixels * distPrev / distSegment) + prevPixel

            if pixel >= TOTAL_NUM_PIXELS:
                pixel = TOTAL_NUM_PIXELS - 1

            self.pixelList[pixel].append(self.trains[train])


    def get(self, i):
        return self.pixelList[i]