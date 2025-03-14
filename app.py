import os
import requests
import json
import time
from bs4 import BeautifulSoup
from flask import Flask, jsonify, request
from celery import Celery
from supabase import create_client, Client
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Celery Configuration
app.config['broker_url'] = 'redis://red-cumqv78gph6c7388hgg0:6379/0'
app.config['result_backend'] = 'redis://red-cumqv78gph6c7388hgg0:6379/0'
app.config['include'] = ['tasks']  # Include the module where the task is defined

def make_celery(app):
    celery = Celery(app.import_name, broker=app.config['broker_url'])
    celery.conf.update(app.config)
    return celery

celery = make_celery(app)

# Function to fetch jobs from Naukri
def fetch_naukri_jobs(keyword, location=None, max_pages=1):
    job_list = []
    headers = {
    "accept": "application/json",
    "accept-language": "en",
    "appid": "109",
    "authorization": "Bearer YOUR_AUTH_TOKEN",  # Replace with a valid token
    "clientid": "d3skt0p",
    "content-type": "application/json",
    "gid": "LOCATION,INDUSTRY,EDUCATION,FAREA_ROLE",
    "nkparam": "J7d/J9BikyAVwgh3YTbmnfqlKTPC3qFUzlCeZfYcW2BqRMnSq3lHcRupZ8WuD0kH0F3ARutT+sq/x2B6yHnyuw==",  # May need to fetch dynamically
    "priority": "u=1, i",
    "sec-ch-ua": "\"Chromium\";v=\"134\", \"Not:A-Brand\";v=\"24\", \"Google Chrome\";v=\"134\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "systemid": "Naukri",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "referrerPolicy": "strict-origin-when-cross-origin"
}
    for page in range(1, max_pages + 1):
        url = f"https://www.naukri.com/jobapi/v3/search?noOfResults=20&urlType=search_by_keyword&searchType=adv&keyword={keyword}&pageNo={page}&seoKey={keyword}-jobs&src=directSearch"
        if location:
            url += f"&location={location}"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            jobs = response.json().get("jobDetails", [])
            job_list.extend(parse_naukri_jobs(jobs, location))
        else:
            break
    print(job_list)
    return job_list

def parse_naukri_jobs(jobs, location):
    if not jobs:
        print(f"No jobs found for location {location}")
        return []

    job_list = []
    for job in jobs:
        job_list.append({
            "job_id": job.get("jobId", "N/A"),
            "title": job.get("title", "N/A"),
            "company": job.get("companyName", "N/A"),
            "location": location if location else job.get("placeholders", [{}])[1].get("label", "N/A"),
            "job_url": f"https://www.naukri.com/job-listings-{job.get('jobId', '')}",
            "job_description": job.get("jobDescription", "N/A"),
            "source": "Naukri"
        })
    return job_list


# Function to fetch jobs from LinkedIn
def fetch_linkedin_jobs(keyword, location):
    jobs = []
    headers = {"User-Agent": "Mozilla/5.0"}
    for start in range(0, 101, 25):
        url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={keyword}&location={location}&start={start}"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            jobs.extend(parse_jobs(response.text))
        else:
            break
    print(jobs)
    return jobs

def parse_jobs(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    job_list = []
    job_cards = soup.find_all('li')
    for job in job_cards:
        job_id = extract_job_id_from_urn(job)
        job_link_tag = job.find('a', class_='base-card__full-link')
        job_url = job_link_tag['href'] if job_link_tag else "N/A"
        job_title_tag = job.find('h3', class_='base-search-card__title')
        job_title = job_title_tag.get_text(strip=True) if job_title_tag else "N/A"
        company_tag = job.find('h4', class_='base-search-card__subtitle')
        company_name = company_tag.get_text(strip=True) if company_tag else "N/A"
        location_tag = job.find('span', class_='job-search-card__location')
        location = location_tag.get_text(strip=True) if location_tag else "N/A"
        job_description = fetch_job_description(job_id) if job_id else "N/A"
        job_list.append({
            "job_id": job_id,
            "title": job_title,
            "company": company_name,
            "location": location,
            "job_url": job_url,
            "job_description": job_description,
            "source": "LinkedIn"
        })
    return job_list

def extract_job_id_from_urn(job_li):
    job_div = job_li.find('div', class_='base-card')
    if job_div:
        data_urn = job_div.get("data-entity-urn", "")
        if "jobPosting:" in data_urn:
            return data_urn.split("jobPosting:")[-1]
    return None

def fetch_job_description(job_id):
    url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        job_description_div = soup.find("div", class_="decorated-job-posting__details")
        return job_description_div.get_text(separator="\n").strip() if job_description_div else "N/A"
    return "N/A"

# Store jobs in Supabase
def store_jobs_in_supabase(jobs): 
    print(jobs)
    for job in jobs:
        existing_job = supabase.table("jobs").select("job_id").eq("job_id", job["job_id"]).execute()
        if not existing_job.data:
            supabase.table("jobs").insert(job).execute()

@app.route('/fetch-jobs', methods=['GET'])
def manual_fetch_jobs():
    from tasks import fetch_and_store_jobs  # Import the task here
    keyword = request.args.get('keyword')
    location = request.args.get('location')
    fetch_and_store_jobs.delay(keyword, location)
    return jsonify({"message": "Job fetching started."})

@app.route('/get-jobs', methods=['GET'])
def get_jobs():
    query = supabase.table("jobs").select("*")

    # Extract query parameters
    keyword = request.args.get('keyword')
    location = request.args.get('location')
    company = request.args.get('company')
    technology = request.args.get('technology')
    source = request.args.get('source')  # New filter for job source
    limit = request.args.get('limit', default=10, type=int)  # Number of jobs per request
    offset = request.args.get('offset', default=0, type=int)  # Pagination offset

    # Apply filters if provided
    if keyword:
        query = query.ilike("title", f"%{keyword}%")
    if location:
        query = query.ilike("location", f"%{location}%")
    if company:
        query = query.ilike("company", f"%{company}%")
    if technology:
        query = query.ilike("job_description", f"%{technology}%")
    if source:
        query = query.ilike("source", f"%{source}%")  # Filtering jobs by source

    # Apply pagination
    query = query.range(offset, offset + limit - 1)  

    response = query.execute()
    return jsonify({
        "jobs": response.data,
        "next_offset": offset + limit,  # For fetching the next set of results
        "has_more": len(response.data) == limit  # If true, more data is available
    })



if __name__ == '__main__':
    app.run(debug=True)