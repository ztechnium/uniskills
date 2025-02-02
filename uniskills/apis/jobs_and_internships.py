import frappe
from frappe import _
from datetime import datetime, timedelta


@frappe.whitelist()
def get_job_filters():
    locations = frappe.get_all('Country', fields=['name'])
    locations = [location['name'] for location in locations]
    experience_levels = ['Entry Level', 'Mid Level', 'Senior Level']
    work_mode = ['Remote', 'On-Site', 'Hybrid']
    job_types = ['Full Time', 'Part Time', 'Contract']
    return {
        'locations': locations,
        'experience_levels': experience_levels,
        'work_mode': work_mode,
        'job_types': job_types
    }


@frappe.whitelist()
def list_jobs(page_number=1):
    items_per_page = 10
    page_number = int(page_number)
    limit_start = (page_number - 1) * items_per_page
    user = frappe.session.user
    #get the student's id by the user's email
    student = frappe.get_all('Student', filters={'email': user}, fields=['name'])
    student_id = student[0]['name']
    current_url = frappe.request.url
    #split the url from "/api/method/" and get the first part
    current_url = current_url.split("/api/method/")[0]
    filters = []
    if 'location' in frappe.form_dict:
        location = frappe.form_dict['location'].replace('%20', ' ')
        filters.append(['location', '=', location])
    if 'experience_level' in frappe.form_dict:
        experience_level = frappe.form_dict['experience_level'].replace('%20', ' ')
        filters.append(['experience_level', '=', experience_level])
    if 'work_mode' in frappe.form_dict:
        work_mode = frappe.form_dict['work_mode'].replace('%20', ' ')
        filters.append(['work_mode', '=', work_mode])
    if 'job_type' in frappe.form_dict:
        job_type = frappe.form_dict['job_type'].replace('%20', ' ')
        filters.append(['job_type', '=', job_type])
    if 'search_text' in frappe.form_dict:
        search_text = frappe.form_dict['search_text'].replace('%20', ' ')
        filters.append(['activity_name', 'like', f"%{search_text}%"])

    filters.append(['internship_status', '=', 'Open'])

    jobs = frappe.get_all('Job Internship', filters=filters, fields=['name', 'activity_name', 'hiring_company', 'experience_level', 'work_mode', 'location', 'job_description'], limit_start=limit_start, limit=items_per_page)
    for job in jobs:
        company = frappe.get_doc('Customer', job['hiring_company'])
        job['about_company'] = company.custom_about_company
        job['employee_count'] = company.custom_head_count
        job['industry'] = company.industry
        job['works_here'] = company.custom_nu_alumni_work_here
        job['title'] = job.pop('activity_name')
        job['company'] = job.pop('hiring_company')
        job['skills'] = frappe.get_all('Internship Skills Requirement', filters={'parent': job['name']} , fields=['required_skill','minimum_requirement'])
        if company.image:
            job['image'] = current_url + company.image
        else:
            job['image'] = ""

        #check if the job the user has applied to or not 
        job_application = frappe.get_all('Job Application', filters={'student_id': student_id, 'apply_for': job['name']})
        if job_application:
            job['applied'] = True
        else:
            job['applied'] = False
    count = len(frappe.get_all('Job Internship', filters=filters, fields=['name']))
    return {
        'jobs': jobs,
        'count': count
    }
        


@frappe.whitelist()
def apply_to_job(job_id):
    user = frappe.session.user
    #get the student's id by the user's email
    student = frappe.get_all('Student', filters={'email': user}, fields=['name'])
    student_id = student[0]['name']
    #student_id = "211000390-Ahmed Hesham Almashad"
    #check if the student has already applied to this job
    job_application = frappe.get_all('Job Application', filters={'student_id': student_id, 'apply_for': job_id})
    if job_application:
        return {
            'message': 'You have already applied to this job'
        }
    job_application = frappe.new_doc('Job Application')
    job_application.student_id = student_id
    job_application.apply_for = job_id
    job_application.date_applied = frappe.utils.now()
    job_application.save(ignore_permissions=True)
    return {
        'message': 'Applied Successfully'
    }


@frappe.whitelist()
def get_job_information(job_id):
    #check if job has %20 in it and replace it with space
    job_id = job_id.replace('%20', ' ')
    current_url = frappe.request.url
    #split the url from "/api/method/" and get the first part
    current_url = current_url.split("/api/method/")[0]
    #get the main skills
    main_skills = frappe.get_all('Skill Group', filters={'plot': 1}, fields=['name'])
    main_skills = [skill['name'] for skill in main_skills]
    job = frappe.get_doc('Job Internship', job_id)
    company = frappe.get_doc('Customer', job.hiring_company)
    job_info = {
        'name': job_id,
        'title': job.activity_name,
        'company': job.hiring_company,
        'experience_level': job.experience_level,
        'work_mode': job.work_mode,
        'location': job.location,
        'job_description': job.job_description,
        'about_company': company.custom_about_company,
        'employee_count': company.custom_head_count,
        'industry': company.industry,
        'works_here': company.custom_nu_alumni_work_here,
        'skills': frappe.get_all('Internship Skills Requirement', filters={'parent': job_id} , fields=['required_skill','minimum_requirement'])
    }
    #check if all the main skills are in the job skills and if not add them with minimum requirement 0
    for skill in main_skills:
        if skill not in [skill['required_skill'] for skill in job_info['skills']]:
            job_info['skills'].append({'required_skill': skill, 'minimum_requirement': 0})

    if company.image:
        job_info['image'] = current_url + company.image
    else:
        job_info['image'] = ""
    return {"job_info": job_info}