"""
Flow pathway for emergency arrivals.

TODO: Write copyright header here
"""

import simpy
import random
import pandas as pd
import matplotlib.pyplot as plt


class g:
    """
    Variables calculated from 1 Jan 2023 - 31 Oct 2024
    emergency procedures - do the same for elective procedures
    everything in minutes.
    Op info excludes day surgery (only Rugby, UH)
    """
    patient_inter_emerg = 1440 / 2 #2/day
    patient_inter_planned = 1440 / 19 #19/day comp+canc
    avg_emergency_ops_per_day = 5
    avg_elective_ops_per_day = 17
    number_ops_per_emergency_case = 1.3 #excl 2 very big outliers
    #number_of_nurses = 1 # TODO: work these out
    number_of_doctors = 2 # TODO: work these out
    #number_of_4_hour_slots = 14
    #number_of_sessions_per_day = 7 #avg 8 hrs a day - elective + emerg
    avg_num_trauma_emerg_sessions_per_day = 12 #full day lists
    avg_num_elective_sessions_per_day = 30 #25 full day; 5 half day lists
    prob_need_emerg_proc = 0.716 
    mean_op_duration_emerg = 174
    mean_op_duration_elective = 143
    avg_turnaround_time = 30 
    sim_duration = 1440 #minutes in 1 day
    number_of_runs = 30 #number of days
    #how many other patients on trauma caseload?
    #how many died
    current_wait_list = 3527
    


class Patient:
    """
    Class representing patients coming in to the hospital.
    
    Their attributes - ID, op duration time
    The ID is passed in when a new patient is created
    """
    def __init__(self, p_id, type):
        self.id = p_id
        self.type = type
        self.wait_time_for_slot = 0.0
        self.priority = 0


class Model:
    """
    Define a model object to simulate trauma arrivals.

    Model simulation times should be in minutes.

    :param run_number: Used to track what run of the model we are doing.
    """
    def __init__(self, run_number):
        """Initialise self."""
        # Create a SimPy environment in which everything will live
        self.env = simpy.Environment()

        # Create a patient counter (which we'll use as a patient ID). This is 
        # before splitting into those who need specific attention
        self.patient_counter = 0

        # Create our resources
        self.operation_4_hour_slots = simpy.PriorityResource(
            self.env, 
            #capacity=g.number_of_4_hour_slots
            capacity = (g.avg_num_trauma_emerg_sessions_per_day/2) + 
            g.avg_num_elective_sessions_per_day
        )
        # self.doctor = simpy.Resource(self.env, capacity=g.number_of_doctors) 

        # # Store the passed in run number
        # self.run_number = run_number

        # # Create a new Pandas DataFrame that will store some results against
        # # the patient ID (which we'll use as the index).
        # self.results_df = pd.DataFrame()
        # self.results_df["Patient ID"] = [1]
        # #self.results_df["Duration of Op"] = [0.0]
        # self.results_df["Q Time Nurse"] = [0.0]
        # self.results_df["Time with Nurse"] = [0.0]
        # self.results_df.set_index("Patient ID", inplace=True)

        # # Create an attribute to store the mean queuing times across this run of
        # # the model
        # self.mean_duration_time = 0

    def generator_patient_arrivals(self):
        """
        Generate arrivals of patients into A&E.

        The inner loop here is always True, so this will always generate 
        samples.
        """
        while True:

            # Increment the patient counter by 1
            self.patient_counter += 1
            
            # Create a new patient - an instance of the Patient Class we
            # defined above - they arrive via A&E so are high priority
            current_patient = Patient(self.patient_counter, type="A&E Arrival")   
            current_patient.priority = 10   

            # The patient now has a chance to need an operation
            self.env.process(self.attend_operation(current_patient))

            # Randomly sample the time to the next patient arriving. Here, we
            # sample from an exponential distribution (common for inter-arrival
            # times), and pass in a lambda value of 1 / mean.  The mean
            # inter-arrival time is stored in the g class.
            sampled_inter_arrival_time = random.expovariate(
                1.0 / g.patient_inter_emerg
            )

            # Freeze this instance of this function in place until the
            # inter-arrival time we sampled above has elapsed. 
            yield self.env.timeout(sampled_inter_arrival_time)

    def generator_planned_arrivals(self):
        """
        Generate arrivals of patients for elective (planned) procedures.

        The inner loop here is always True, so this will always generate 
        samples.
        """
        while True:

            # Increment the patient counter by 1
            self.patient_counter += 1
            
            # Create a new patient - an instance of the Patient Class we
            # defined above - they arrive not via A&E so are low priority
            current_patient = Patient(self.patient_counter, type="Planned Arrival")   
            current_patient.priority = 1

            # The patient now has a chance to need an operation
            self.env.process(self.attend_operation(current_patient))

            # Randomly sample the time to the next planned patient arriving. 
            # Here, we sample from an exponential distribution (common for 
            # inter-arrival times), and pass in a lambda value of 1 / mean.
            # The mean inter-arrival time is stored in the g class.
            sampled_inter_arrival_time = random.expovariate(
                1.0 / g.patient_inter_planned
            )

            # Freeze this instance of this function in place until the
            # inter-arrival time we sampled above has elapsed. 
            yield self.env.timeout(sampled_inter_arrival_time)

    def attend_operation(self, patient):
        """
        When patients arrive at A&E, some of them will need an operation.

        This class determines if a given patient will need an operation or not.

        :param patient: The patient we are assigning to an operation (or not).
        """
        if random.uniform(0, 1) < g.prob_need_emerg_proc or patient.type == "Planned Arrival":

            # This person needs an emergency procedure (determined via random 
            # sampling) so add them to the slot requirement
            start_q_slot = self.env.now

            # TODO: Right now each person takes a single 4 hour slot, want to 
            # split it by some people taking up 2 slots 

            # They wait until they actually get the slot
            with self.operation_4_hour_slots.request(priority=patient.priority) as req:
                yield req

                # Record the time that the person went into the slot
                end_q_slot = self.env.now

                # How long did the person wait for this slot?
                patient.wait_time_for_slot = end_q_slot - start_q_slot

                # Record how long the person was having the operation for 
                # Right now we just use all 4 hour slots, so this is 4 * 60 
                # minutes
                time_in_slot = 8 * 60 * 10 # TODO: 120 here to make a queue, needs to be removed

                print(f'Patient {patient.id}, type {patient.type} needs an operation. Arrived at {start_q_slot}, got in at {end_q_slot}, waited {patient.wait_time_for_slot}.')


                # TODO: This is maybe not needed
                # sampled_doctor_act_time = random.expovariate(
                #     1.0 / g.mean_d_consult_time
                # )

                # self.results_df.at[patient.id, "Q Time Doctor"] = (
                #     patient.q_time_doctor
                # )
                # self.results_df.at[patient.id, "Time with Doctor"] = (
                #     sampled_doctor_act_time
                # )

                yield self.env.timeout(time_in_slot)


if __name__ == "__main__":
    
    # TODO: Get actual times of arrivals to validate model
    # TODO: We need to include the scheduled patients, we need a priority, where
    #   A&E patients get higher priority than scheduled patients, then when 
    #   there a free slot the person comes in based on priority, need to alter 
    #   patient.priority for different type of arrivals 
    # TODO: Think we need another generator for planned patients, put them as lower priority

    # Fix randomness
    random.seed(42)

    # Create the model
    my_model = Model(run_number=0)
    print('Start: ', my_model.patient_counter)
    my_model.env.process(my_model.generator_patient_arrivals())
    my_model.env.process(my_model.generator_planned_arrivals())
    my_model.env.run(until=g.sim_duration * g.number_of_runs)
    print('End: ', my_model.patient_counter)

    # # A patient arrives
    # arrival_times = []
    # for arrival_number in range(3):
    #     arrival_times.append(next(my_model.generator_patient_arrivals()))
    # print([i.value for i in arrival_times])

