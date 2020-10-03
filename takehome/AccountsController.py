
from datetime import datetime, timedelta

class AccountsController(object):
    #Creates an object to access user account limits and payments
    #This will return jsons of whether or not to accept an users deposit

    def __init__(self):
        
        #Initialize limits for deposits and accounts_json
        #accounts_json keys -> 'customer_id'
        #accounts_json will record user transaction limits

        self.accounts_json = {}
        self.daily_deposit_limit = 5000
        self.weekly_deposit_limit = 20000
        self.daily_loads = 3

    def processUserLoad(self, customer_json):
        #The main function for processing deposit attempts
        #Does a check if customer_id is an integer string
        #Then runs all the checks for daily load quota, daily amount deposit quota,
        #weekly amount deposit quota, and then updates accounts_json records if successful

        customer_id = customer_json['customer_id']
        load_id = customer_json['id']
        load_amount = self.convertLoadAmountToNum(customer_json['load_amount'])
        date_time = customer_json['time']
        response_json = {'id' : load_id, 'customer_id' : customer_id, 'accepted' : True}
        
        if not self.checkCustomerID(customer_id):
            response_json['accepted'] = False
            return response_json

        if customer_id not in self.accounts_json:
            self.addNewUser(customer_id)

        last_load_date = self.checkLastLoad(customer_id)
        num_days_difference, diff_week_check = self.compareLoadDates(customer_id, last_load_date, date_time)

        #Reset amounts used before running check if the last deposit was 
        self.checkImplementResets(customer_id, num_days_difference, diff_week_check)

        #Check boolean if we are going over daily deposit amount
        if not self.compareDailyDollarAmount(customer_id, load_amount):
            response_json['accepted'] = False
            return response_json
        
        #Check boolean if we have done too many deposits today
        if not self.compareDailyLoadAmounts(customer_id):
            response_json['accepted'] = False
            return response_json

        #Check boolean if we are going over weekly deposit amount
        if not self.compareWeeklyDollarAmount(customer_id, load_amount):
            response_json['accepted'] = False
            return response_json
        
        self.updateUserRecords(customer_id, date_time, load_id, load_amount)
        return response_json



    def addNewUser(self, customer_id):
        #Initializes a new user in the accounts_json
        #accounts_json[customer_id] keys -> 'last_load_date' -> str
        #                                   'current_weekly_deposit_amount' -> float
        #                                   'current_daily_deposit_amount' -> float
        #                                   'current_daily_loads' -> int
        #                                   'load_ids' -> list

        self.accounts_json[customer_id] = {'last_load_date': '', 'current_weekly_deposit_amount' : 0, 
                                            'current_daily_deposit_amount' : 0, 
                                            'current_daily_loads' : 0, 'load_ids' : []}

    def compareLoadDates(self, customer_id, last_load_date, current_load_date):
        """We need to truncate the dates to midnight as its about checking if the load dates
        are on different days rather than just 24 hours. This also applies for the weekly truncate
        as it's not about being in a 7-day rolling interval but being in a different week
        truncated on mondays.
        
        We return the amount of days difference between last deposit and current attempt and also
        a boolean if it's a different week"""

        if last_load_date == '':
            self.updateUserLastLoadDate(customer_id, current_load_date)
            last_load_date = current_load_date   

        current_time = self.processDate(current_load_date)
        last_load_time = self.processDate(last_load_date)

        current_time_trunc = datetime(current_time.year, current_time.month, current_time.day)
        last_load_time_trunc = datetime(last_load_time.year, last_load_time.month, last_load_time.day)

        last_load_time_trunc_weekly = last_load_time_trunc - timedelta(days = last_load_time_trunc.weekday())
        if (current_time_trunc - last_load_time_trunc_weekly).days >= 7:
            diff_week_check = True
        else:
            diff_week_check = False

        num_days_difference = (current_time_trunc - last_load_time_trunc).days
        
        return num_days_difference, diff_week_check           

    def compareDailyDollarAmount(self, customer_id, current_deposit) -> bool:
        #The check if current deposit plus daily deposits already used is higher than weekly limit

        current_dollar_quota = self.daily_deposit_limit - self.checkDailyAmountDeposited(customer_id)
        if current_deposit <= current_dollar_quota:
            return True
        else:
            return False

    def compareDailyLoadAmounts(self, customer_id) -> bool:
        #The check if we have space for one more deposit in our daily load quota

        current_daily_load_quota = self.daily_loads - self.checkDailyLoadsDone(customer_id)
        if current_daily_load_quota >= 1:
            return True
        else:
            return False

    def compareWeeklyDollarAmount(self, customer_id, current_deposit) -> bool:
        #The check if current deposit plus weekly deposits already used is higher than weekly limit

        current_dollar_quota = self.weekly_deposit_limit - self.checkWeeklyAmountDeposited(customer_id)
        if current_deposit <= current_dollar_quota:
            return True
        else:
            return False

    def updateUserRecords(self, customer_id, load_date, load_id, deposit_amount):
        #This function just updates all user records in accounts_json for the successful deposit

        self.updateUserLastLoadDate(customer_id, load_date)
        self.updateUserWeeklyDepositAmount(customer_id, deposit_amount)
        self.updateUserDailyDepositAmount(customer_id, deposit_amount)
        self.updateLoads(customer_id, load_id)

    def updateUserLastLoadDate(self, customer_id, load_date):
        #Checks if this is the first deposit record then replaces
        #Also double checks if the new date is after the old one before replacing the last load date

        if self.accounts_json[customer_id]['last_load_date'] == '':
            self.accounts_json[customer_id]['last_load_date'] = load_date

        elif self.processDate(load_date) >= self.processDate(self.accounts_json[customer_id]['last_load_date']):
            self.accounts_json[customer_id]['last_load_date'] = load_date

        else:
            return {'status' : 'error', 'reason' : 'load date was given non-chronologically'}
        
        return {'status' : 'success', 'reason' : ''}

    def updateUserWeeklyDepositAmount(self, customer_id, deposit_amount):
        #Double check if the deposit amount is too high
        #If not, adds to the current weekly deposit amount used so far

        if deposit_amount <= self.weekly_deposit_limit:
            self.accounts_json[customer_id]['current_weekly_deposit_amount'] += deposit_amount
        else:
            return {'status' : 'error', 'reason' : 'deposit amount received was higher than weekly quota'}
        
        return {'status' : 'success', 'reason' : ''}
    
    def updateUserDailyDepositAmount(self, customer_id, deposit_amount):
        #Double check if the deposit amount is too high
        #If not, adds to the current daily deposit amount used so far

        if deposit_amount <= self.daily_deposit_limit:
            self.accounts_json[customer_id]['current_daily_deposit_amount'] += deposit_amount
        else:
            return {'status' : 'error', 'reason' : 'deposit amount received was higher than daily quota'}
        
        return {'status' : 'success', 'reason' : ''}

    def updateLoads(self, customer_id, load_id):
        #Double check if the current_daily_loads is being bypassed
        #Update the daily load counts if a deposit succeeds

        if self.accounts_json[customer_id]['current_daily_loads'] >= 3:
            return {'status' : 'error', 'reason' : 'current daily loads is already at 3 or more'}
        else:
            self.accounts_json[customer_id]['current_daily_loads'] += 1
            self.accounts_json[customer_id]['load_ids'].append(load_id) 
        
        return {'status' : 'success', 'reason' : ''}

    def checkImplementResets(self, customer_id, num_days, diff_week_check):
        #The first check is for daily resets if the last deposit was on another day
        #The second check is if the last deposit was in another week truncated on mondays

        if num_days >= 1:
            self.resetDailyAmountDeposited(customer_id)
            self.resetDailyLoadsDone(customer_id)
        
        if diff_week_check:
            self.resetWeeklyAmountDeposited(customer_id)
        

    def resetDailyAmountDeposited(self, customer_id):
        self.accounts_json[customer_id]['current_daily_deposit_amount'] = 0

    def resetWeeklyAmountDeposited(self, customer_id):
        self.accounts_json[customer_id]['current_weekly_deposit_amount'] = 0

    def resetDailyLoadsDone(self, customer_id):
        self.accounts_json[customer_id]['current_daily_loads'] = 0   

    def convertLoadAmountToNum(self, load_amount) -> float:
        #converts the currency string '$343.43' into float
        return float(load_amount[1:])

    def processDate(self, date_time) -> datetime:
        #processes date_time into datetime object for manipulation
        return datetime.strptime(date_time, "%Y-%m-%dT%H:%M:%SZ")
    
    def checkLastLoad(self, customer_id) -> str:
        #check last deposit date of user
        return self.accounts_json[customer_id]['last_load_date']

    def checkWeeklyAmountDeposited(self, customer_id) -> float:
        #check the current weekly amount user has used
        return self.accounts_json[customer_id]['current_weekly_deposit_amount']

    def checkDailyAmountDeposited(self, customer_id) -> float:
        #check the current daily amount user has used
        return self.accounts_json[customer_id]['current_daily_deposit_amount']

    def checkDailyLoadsDone(self, customer_id) -> int:
        return self.accounts_json[customer_id]['current_daily_loads']

    def checkLoadIDs(self, customer_id) -> list:
        #Pull record of load_ids in the form of list
        #Ie. ['34', '54656', ...]
        return self.accounts_json[customer_id]['load_ids']

    def checkCustomerID(self, customer_id) -> bool:
        #This checks if we were given a integer string for customer_id
        return str.isdigit(customer_id)
    
    

    
    