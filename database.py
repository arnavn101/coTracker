import dataset, configparser, sqlite3
from math import radians, cos, sin, asin, sqrt
import os, time, re
from datetime import datetime, timedelta

class SQL_Server():

    def __init__(self):
        self.init_database()
        self.config = configparser.ConfigParser()
        self.config.read('config.cfg')
        self.TIME_INTERACTIONS = int(self.config.get('ConfigInfo', 'TIME_INTERACTIONS'))
        
    def init_database(self):
        self.db = dataset.connect('sqlite:///pythonsqlite.db', )
        
    def close_database(self):
        self.db.close()

    def save_database(self):
        self.db.commit()
        
    def insert_informaton(self, unique_identifier, location, current_date):
        (self.db[unique_identifier]).insert(dict(location=location, interactions=None, hasVirus=None, current_date=current_date))

    def insert_interactions(self, unique_identifier, interaction_identifier, date_interaction):
        (self.db[unique_identifier]).insert(dict(location=None, interactions=interaction_identifier, hasVirus=None, date_interaction=date_interaction))

    def hasVirus(self, unique_identifier):
        (self.db[unique_identifier]).insert(dict(location=None, interactions=None, hasVirus=True))

    def checkVirusState(self, unique_identifier, value):
        boolean = False
        if(len(list(self.db[unique_identifier].find(hasVirus=value))) > 0):
            boolean = True
        return boolean
        # False refers to No Virus & True refers to Virus

    def find_allInteractions(self, unique_identifier):
        possible_interactions = []
        for row in self.db[unique_identifier]:
            if row['interactions'] != None:
                possible_interactions.append(row['interactions'])
        return possible_interactions
    
    def find_allLocations(self, unique_identifier):
        possible_locations = []
        for row in self.db[unique_identifier]:
            if row['location'] != None:
                possible_locations.append(row['location'])
        return possible_locations
    
    def find_allDates(self, unique_identifier):
        possible_dates = []
        for row in self.db[unique_identifier]:
            if row['current_date'] != None:
                possible_dates.append(row['current_date'])
        return possible_dates
    
    def haversine(self, lon1, lat1, lon2, lat2):
        """
        Calculate the great circle distance between two points 
        on the earth (specified in decimal degrees)

        input : str(lat,lon)
        """
        # convert decimal degrees to radians 
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

        # haversine formula 
        dlon = lon2 - lon1 
        dlat = lat2 - lat1 
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a)) 
        r = 6371 # Radius of earth in kilometers. Use 3956 for miles
        return (c * r)*1000

    def locations_distance(self, location_1, location_2):
        location_1 = (location_1.split(","))
        location_2 = (location_2.split(","))
        return self.haversine(float(location_1[0]), float(location_1[1]), float(location_2[0]), float(location_2[1]))

    def retrieve_specific_interaction(self, unique_identifier, unique_identifier_2, date_interaction):
        return len(list(self.db[unique_identifier].find(interactions=unique_identifier_2, date_interaction=date_interaction))) > 0

    def retrieve_date_interaction(self,unique_identifier, unique_identifier_2):
        list_interaction = ((self.db[unique_identifier].find(interactions=unique_identifier_2)))
        dates_interaction = []
        for individual_interaction in list_interaction:
            date_interaction = self.stringToDatetime(individual_interaction['date_interaction'])
            if (datetime.now() - date_interaction) < timedelta(days=15):
                dates_interaction.append((date_interaction))
        return (max(dates_interaction))

    def return_infected_interaction(self, unique_identifier):
        infected_interactions = []
        date_infectedInteractions = {}
        for interaction in self.find_allInteractions(unique_identifier):
            if self.checkVirusState(interaction, True):
                infected_interactions.append(interaction)
        for interaction in infected_interactions:
            #print(f"Infected Interaction with {interaction}")
            date_infectedInteractions[interaction] = (self.retrieve_date_interaction(unique_identifier, interaction))
        if len(date_infectedInteractions) > 0:
            return max(date_infectedInteractions.keys(), key=(lambda key: date_infectedInteractions[key]))
        return None

    def dateTimetoString(self, datetimeDate):
        return datetimeDate.strftime('%d %B %Y')

    def users_proximity(self, unique_identifier, unique_identifier_2):
        locations_user  = self.find_allLocations(unique_identifier)
        locations_user2 = self.find_allLocations(unique_identifier_2)
        return [self.locations_distance(u1, u2) for u1 in locations_user for u2 in locations_user2]
    
    def stringToDatetime(self, stringDate):
        return datetime.strptime(stringDate, '%Y-%m-%d %H:%M:%S.%f')

    def similar_dates(self,unique_identifier, unique_identifier_2):
        dates_unique_identifier, dates_unique_identifier_2 = self.find_allDates(unique_identifier), self.find_allDates(unique_identifier_2) 
        return [self.average_date(date1, date2) for date1 in dates_unique_identifier for date2 in dates_unique_identifier_2 if (self.stringToDatetime(date1) - self.stringToDatetime(date2)) < timedelta(minutes=self.TIME_INTERACTIONS)]
    
    def average_date(self, date1, date2):
        date1, date2 = self.stringToDatetime(date1), self.stringToDatetime(date2)
        if date1 > date2:
            duration = date1 - date2
            return str(date1 + duration/2)
        elif date2 > date1:
            duration = date2 - date1
            return str(date2 + duration/1)
        return str(date1)
    
    def view_information_user(self, unique_identifier):
        return list(self.db[unique_identifier].all())

    def return_allUsers(self):
        return self.db.tables
    
    def potential_interaction(self, distance, unique_identifier, unique_identifier_2):
        dates_similarity = self.similar_dates(unique_identifier, unique_identifier_2)
        if len(dates_similarity) > 0:  
            return min(self.users_proximity(unique_identifier, unique_identifier_2)) < distance
        return False 
        # False refers to No interaction & True refers Yes interaction
