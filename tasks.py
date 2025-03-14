from celery import Celery
from app import celery, fetch_linkedin_jobs, fetch_naukri_jobs, store_jobs_in_supabase

@celery.task(bind=True)
def fetch_and_store_jobs(self, keyword=None, location=None):
    try:
        keywords = [
            "Software Engineer", "Python Developer", "Data Scientist", "Machine Learning Engineer",
            "Frontend Developer", "Backend Developer", "Full Stack Developer", "DevOps Engineer",
            "Cloud Engineer", "Cybersecurity Analyst", "Mobile App Developer", "Blockchain Developer",
            "AI Engineer", "Game Developer", "Embedded Systems Engineer"
        ]

        locations = [
            "Bangalore, India", "Hyderabad, India", "Mumbai, India", "Pune, India", "Chennai, India",
            "Delhi, India", "Gurgaon, India", "Noida, India", "Kolkata, India", "Ahmedabad, India", "United States"
        ]

        if keyword and location:
            keywords = [keyword]
            locations = [location]

        for keyword in keywords:
            for location in locations:
                naukri_jobs = fetch_naukri_jobs(keyword, location)
                linkedin_jobs = fetch_linkedin_jobs(keyword, location)

                if naukri_jobs is None or linkedin_jobs is None:
                    print(f"Skipping storage for {keyword} in {location} due to empty response.")
                    continue

                store_jobs_in_supabase(naukri_jobs + linkedin_jobs)
    except Exception as e:
        self.retry(exc=e, countdown=60, max_retries=3)
        raise e