import simpy
import random
import pandas as pd

#Class to store global parameter values. We don't create an instance of this
#class - we just refer to the class blueprint itself to access the numbers inside.

#Variables calculated from 1 Jan 2023 - 31 Oct 2024
#emergency procedures - do the same for elective procedures
class g:
    patient_inter_emerg = 720 #2/day
    avg_emergency_ops_per_day = 7
    number_ops_per_emergency_case = 1.3 #excl 2 very big outliers
    #number_of_nurses = 1 ##work these out
    #number_of_doctors = 2 ##work these out
    number_of_sessions_per_day = 7 #avg 8 hrs a day - elective + emerg
    prob_need_emerg_proc = 0.716 
    mean_op_duration_emerg = 145 
    sim_duration = 1440 #minutes in 1 day
    number_of_runs = 30 #number of days
    #how many other patients on trauma caseload?
    #how many died
    
#Class representing patients coming in to the hospital
#Their attributes - ID, op duration time
#The ID is passed in when a new patient is created
class Patient:
    def __init__(self, p_id):
        self.id = p_id
        self.op_duration_time = 0

