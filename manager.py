from database import SQL_Server
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import timedelta, datetime
from itertools import combinations
import configparser 
# authentication from doctor
class Manager():
    def __init__(self):
        self.sql_server = SQL_Server()
        self.config = configparser.ConfigParser()
        self.config.read('config.cfg')
        self.DISTANCE_BETWEEN = int(self.config.get('ConfigInfo', 'DISTANCE_BETWEEN'))
        self.DAYS_BETWEEN = int(self.config.get('ConfigInfo', 'DAYS_BETWEEN'))
        self.INTERVAL_WAIT = float(self.config.get('ConfigInfo', 'INTERVAL_WAIT'))
    
    def appendUserInteractions(self):
        all_users = self.sql_server.return_allUsers()
        for current_user,other_user in list(combinations(all_users, 2)):                
            if self.sql_server.potential_interaction(self.DISTANCE_BETWEEN, current_user, other_user):
                for date in self.sql_server.similar_dates(current_user, other_user):
                    if not self.sql_server.retrieve_specific_interaction(current_user, other_user, date) and (datetime.now() - self.sql_server.stringToDatetime(date)) < timedelta(days=self.DAYS_BETWEEN):
                        print(f"True Interaction between {current_user} and {other_user} on {date}")
                        self.sql_server.insert_interactions(current_user, other_user, date)
                        self.sql_server.insert_interactions(other_user, current_user, date)
            else:
                print(f"No Interaction between {current_user} and {other_user}")
        
    def possiblity_Affected(self, affectedVictim):
        possible_interactions = (self.sql_server.find_allInteractions(affectedVictim))
        for person in possible_interactions:
            with open("victims.txt", "a+") as myfile:
                existing_users = open('victims.txt').read().splitlines()
                if not person in existing_users:
                    print("Notify personell " + person)
                    myfile.write(f"{person}\n")

    def retrieveVictims(self):
        all_users = self.sql_server.return_allUsers()
        return [potential_victim for potential_victim in all_users if self.sql_server.checkVirusState(potential_victim, True)]
    
    def automate_manager(self):
        print("\nDatabase Manager has started\n")
        self.appendUserInteractions()
        affected_individuals = self.retrieveVictims()
        if len(affected_individuals) > 0:
            for individual in affected_individuals:
                self.possiblity_Affected(individual)
        print("\nDatabase Manager has ended\n")
        
manager   = Manager()
"""
scheduler = BlockingScheduler()
scheduler.add_job(manager.automate_manager, 'interval', hours=manager.INTERVAL_WAIT)
scheduler.start()
"""
manager.automate_manager()
