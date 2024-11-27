import simpy
import random
import pandas as pd

#Class to store global parameter values. We don't create an instance of this
#class - we refer to the class blueprint itself to access the numbers inside.

#Variables calculated from 1 Jan 2023 - 31 Oct 2024
#emergency procedures - do the same for elective procedures
class g:
    patient_inter_emerg = 720 #2/day
    avg_emergency_ops_per_day = 7
    number_ops_per_emergency_case = 1.3 #excl 2 very big outliers
    #number_of_nurses = 1 ##work these out
    number_of_doctors = 2 ##work these out
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

#Model class
class Model:
    # Constructor to set up the model for a run.  We pass in a run number when
    # we create a new model.
    def __init__(self, run_number):
        # Create a SimPy environment in which everything will live
        self.env = simpy.Environment()

    # Create a patient counter (which we'll use as a patient ID)
        self.patient_counter = 0

    # Create our resources
        self.sessions = simpy.Resource(self.env, 
            capacity=g.number_of_sessions_per_day)
        self.doctor = simpy.Resource(self.env, capacity=g.number_of_doctors) 

    # Store the passed in run number
        self.run_number = run_number

    # Create a new Pandas DataFrame that will store some results against
        # the patient ID (which we'll use as the index).
        self.results_df = pd.DataFrame()
        self.results_df["Patient ID"] = [1]
        self.results_df["Duration of Op"] = [0.0]
        self.results_df.set_index("Patient ID", inplace=True)

    # Create an attribute to store the mean queuing times across this run of
        # the model
        self.mean_duration_time = 0

        