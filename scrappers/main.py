import os
import psycopg2

from scripts import *

def main():
    nofluffjobs.NoFluffJobs().get_jobs_from_api()
    justjoinit.JustJoinIT().get_jobs_from_api()
    pracujpl.PracujPl().scrapp_jobs_from_page()
    print("finito?!")

if __name__ == "__main__":
    main()