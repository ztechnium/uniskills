import frappe
from frappe import _
from datetime import datetime, timedelta


@frappe.whitelist()
def list_activities():
    activities = ["Academic Course", "Extra Course", "Club"]
    return activities


@frappe.whitelist()
def get_filters():

    # list skills
    skills = frappe.get_all('Skill Group', filters={'plot': 1}, fields=['name'])
    #make them a list 
    skills = [skill['name'] for skill in skills]
    #list schools
    schools = frappe.get_all('College', fields=['name'])
    schools = [school['name'] for school in schools]

    return {"skills": skills, "schools": schools}


@frappe.whitelist()
def list_courses(page_number=1):
    items_per_page = 10
    page_number = int(page_number)
    limit_start = (page_number - 1) * items_per_page
    user = frappe.session.user
    #get the student's id by the user's email
    student = frappe.get_all('Student', filters={'email': user}, fields=['name'])
    student_id = student[0]['name']
    #student_id = "211000390-Ahmed Hesham Almashad"
    filters=[]
    #get the main skills 
    main_skills = frappe.get_all('Skill Group', filters={'plot': 1}, fields=['name'])
    main_skills = [skill['name'] for skill in main_skills]
    main_schools = frappe.get_all('College', fields=['name'])
    main_schools = [school['name'] for school in main_schools]
    filter_schools = {}
    filter_skills = {}
    child_table_name = ""
    current_url = frappe.request.url
    #split the url from "/api/method/" and get the first part
    current_url = current_url.split("/api/method/")[0]
    if 'activity' in frappe.form_dict:
        activity = frappe.form_dict['activity'].replace("%20", " ")
    else:
        activity = "Academic Course"
    
    if activity == "Academic Course":
        child_table_name = "Course Sub-Skill Contribution"
        enrollment_doctype = "Academic Course Enrollment"
    elif activity == "Extra Course":
        child_table_name = "Extra Course Sub-Skill Contribution"
        enrollment_doctype = "Extra Course Enrollment"
    else:
        child_table_name = "Club Sub-Skill Contribution"
        enrollment_doctype = "Club Enrollment"



    #get the skills if they are in the form_dict
    if 'skills' in frappe.form_dict:
        skills = frappe.form_dict['skills'].split(",")
        #check if any of them has %20 in it and replace with space
        skills = [skill.replace("%20", " ") for skill in skills]

    if 'schools' in frappe.form_dict:
        schools = frappe.form_dict['schools'].split(",")
        #check if any of them has %20 in it and replace with space
        schools = [school.replace("%20", " ") for school in schools]
        filters.append(['school', 'in', schools])

    if 'search_text' in frappe.form_dict:
        search_text = frappe.form_dict['search_text']    
        filters.append(['name', 'like', '%' + search_text + '%'])

    # Filter courses based on skills
    if 'skills' in frappe.form_dict:
        child_table_entries = frappe.get_all(child_table_name, 
                                             filters={'skill_group': ['in', skills]},
                                             fields=['parent'])
        # Extract unique course names from the result
        course_names = list(set([entry['parent'] for entry in child_table_entries]))
        filters.append(['name', 'in', course_names])
    filters.append(['enrollment_status', '=', "Open"])
    if activity == "Academic Course":
        courses = frappe.get_all(activity, filters=filters, fields=['name', 'course_name', 'school', 'description',"enrollment_link",'image','semester'], limit_start=limit_start, limit_page_length=items_per_page)
        filter_courses = frappe.get_all(activity, filters=filters, fields=['name','school'])
        if not courses:
            if 'search_text' in frappe.form_dict:
                filters.remove(['name', 'like', '%' + search_text + '%'])
                if 'search_text' in frappe.form_dict:
                    search_text = frappe.form_dict['search_text']    
                    filters.append(['course_name', 'like', '%' + search_text + '%'])
                    courses = frappe.get_all(activity, filters=filters, fields=['name', 'course_name', 'school', 'description',"enrollment_link",'image','semester'], limit_start=limit_start, limit_page_length=items_per_page)
                    filter_courses = frappe.get_all(activity, filters=filters, fields=['name','school'])

    else:
        courses = frappe.get_all(activity, filters=filters, fields=['name', 'description','school','image','semester'], limit_start=limit_start, limit_page_length=items_per_page)
        filter_courses = frappe.get_all(activity, filters=filters, fields=['name','school'])

    
    #get each course's skill groups 
    for course in courses:
        if activity == "Academic Course":
            course['course_id'] = course['name']
        else:
            #add course name as the same value as name
            course['course_name'] = course['name']
        course['skills'] = frappe.get_all(child_table_name, filters={'parent': course['name']}, fields=['skill_group'])
           
        course['skills'] = [skill['skill_group'] for skill in course['skills']]
        #remove duplicate skills
        course['skills'] = list(set(course['skills']))
        #remove the skill groups that are not in the main skills
        course['skills'] = [skill for skill in course['skills'] if skill in main_skills]
        if course['image']:
            image_url = current_url + course['image']
            course['image'] = image_url
        else:
            course['image'] = ""    

        #check if student is enrolled in the course
        enrollment = frappe.get_all(enrollment_doctype, filters={'student_id': student_id, 'enrollment_to': course['name']}, fields=['name'])
        if enrollment:
            course['is_enrolled'] = True
        else:
            course['is_enrolled'] = False

    #add the main skill to the filter skills with 0 courses
    for skill in main_skills:
        filter_skills[skill] = 0
    #add the filter skills with its number of courses while the key is the main skill
    # for course in courses:
    #     for skill in course['skills']:
    #         filter_skills[skill] += 1

    #add the schools to the filter schools with 0 courses
    for school in main_schools:
        filter_schools[school] = 0
    #add the filter schools with its number of courses while the key is the school
    # for course in courses:
    #     if course['school']:
    #         filter_schools[course['school']] += 1

    #get the number of courses in each skill group based on the activity and put it in the filter_skills
    for skill in main_skills:
        # Initialize a set to keep track of courses already counted for this skill
        counted_courses = set()
        for course in filter_courses:
            # Get the skills for the current course
            course_skills = [skill['skill_group'] for skill in frappe.get_all(child_table_name, filters={'parent': course['name']}, fields=['skill_group'])]
            # If the skill is in the course's skills and the course hasn't been counted yet, increment the count
            if skill in course_skills and course['name'] not in counted_courses:
                filter_skills[skill] += 1
                counted_courses.add(course['name'])

    for school in main_schools:
        #from filter_courses get the number of courses in each school, check if the course has a school
        count = len([course['name'] for course in filter_courses if course['school'] == school])
        filter_schools[school] = count

    return {"courses": courses, "filter_skills_count": filter_skills, "filter_schools_count": filter_schools}


@frappe.whitelist()
def enroll_to_course(activity,activity_id):
    user = frappe.session.user
    #get the student's id by the user's email
    student = frappe.get_all('Student', filters={'email': user}, fields=['name'])
    student_id = student[0]['name']
    #student_id = "211000390-Ahmed Hesham Almashad"
    #get the doctype based on the activity
    if activity == "Academic Course":
        doctype_name = "Academic Course Enrollment"
    elif activity == "Extra Course":
        doctype_name = "Extra Course Enrollment"
    else:
        doctype_name = "Club Enrollment"
    #check if the student is already enrolled in the course
    enrollment = frappe.get_all(doctype_name, filters={'student_id': student_id, 'enrollment_to': activity_id}, fields=['name'])
    if enrollment:
        #get the enrollment's status
        # status = frappe.get_value(doctype_name, enrollment[0]['name'], 'status')
        # return {"message": f"You are already enrolled in this course with status: {status}"}
        if doctype_name == "Club Enrollment":
            return {"message": "You are already enrolled in this club"}
        return {"message": "You are already enrolled in this course"}
    #create a new enrollment
    enrollment = frappe.new_doc(doctype_name)
    enrollment.student_id = student_id
    enrollment.enrollment_to = activity_id
    #get the course's semester
    activity_doc = frappe.get_doc(activity, activity_id)
    if activity_doc.semester:
        enrollment.semester = activity_doc.semester

    # enrollment.status = "Pending"
    enrollment.date_enrolled = frappe.utils.now()
    enrollment.save(ignore_permissions=True)
    if doctype_name == "Club Enrollment":
        return {"message": "You have successfully enrolled in this club"}
    return {"message": "You have successfully enrolled in this course"}


@frappe.whitelist(allow_guest=True)
def test():

    #create a loop that takes 3 minutes
    start_time = datetime.now()
    while True:
        current_time = datetime.now()
        if (current_time - start_time).seconds > 180:
            break
    #create a student 
    student = frappe.new_doc('Student')
    student.student_name = "en test"
    student.email = "tes@w.com"
    student.save(ignore_permissions=True)
    return {"message": "Done"}


@frappe.whitelist(allow_guest=True)
def test2():

    job = frappe.enqueue(test, queue='long', timeout=0)
    # Return the job ID for tracking
    return {"message": "Task has been started. It may take some time."}



@frappe.whitelist()
def course_points(activity,activity_id):
    #check if activity has %20 in it and replace with space
    if "%20" in activity:
        activity = activity.replace("%20", " ")
    #check if activity_id has %20 in it and replace with space
    if "%20" in activity_id:
        activity_id = activity_id.replace("%20", " ")    
    #get the doctype based on the activity
    if activity == "Academic Course":
        child_table_name = "Course Sub-Skill Contribution"
    elif activity == "Extra Course":
        child_table_name = "Extra Course Sub-Skill Contribution"
    else:
        child_table_name = "Club Sub-Skill Contribution"

    #get the main skills
    main_skills = frappe.get_all('Skill Group', filters={'plot': 1}, fields=['name'])
    main_skills = [skill['name'] for skill in main_skills]
    #get the course's skill groups
    course_skills = frappe.get_all(child_table_name, filters={'parent': activity_id}, fields=['skill_group','sub_skill_contribution','sub_skill'])
    #remove the skill groups that are not in the main skills
    course_skills = [skill for skill in course_skills if skill['skill_group'] in main_skills]
    # for each course skill, get the contribution from the field contribution_weight from the Sub-Skill doctype
    for skill in course_skills:
        skill['sub_skill_contribution_percentage'] = frappe.get_value('Sub-Skill', skill['sub_skill'], 'contribution_weight')
        skill['sub_skill_contribution_percentage'] = int((float(skill['sub_skill_contribution']) * float(skill['sub_skill_contribution_percentage'])) * 100)

    #group the sub skills by the skill group and get the total contribution for each skill group
    skill_groups = {}
    for skill in course_skills:
        if skill['skill_group'] not in skill_groups:
            skill_groups[skill['skill_group']] = 0
        skill_groups[skill['skill_group']] += float(skill['sub_skill_contribution_percentage'])
    return {"course_points": skill_groups}


@frappe.whitelist()
def under_maintenance():
    #get under_maintenance from the NUCTA Settings
    under_maintenance_flag = frappe.get_value('NUCTA Settings', 'NUCTA Settings', 'under_maintenance')
    if under_maintenance_flag == 1:
        under_maintenance = True
    else:
        under_maintenance = False

    return {"under_maintenance": under_maintenance}    

















@frappe.whitelist(allow_guest=True)
def list_skills_old(activity):#
    #check if activity has %20 in it and replace with space
    if "%20" in activity:
        activity = activity.replace("%20", " ")
    child_table_name = ""    
    skills = frappe.get_all('Skill Group', filters={'plot': 1}, fields=['name'])
    #make them a list 
    skills = [skill['name'] for skill in skills]
    #get the number of courses in each skill group based on the activity
    if activity == "Academic Course":
        child_table_name = "Course Sub-Skill Contribution"
    elif activity == "Extra Course":
        child_table_name = "Extra Course Sub-Skill Contribution"
    else:
        child_table_name = "Club Sub-Skill Contribution"
    #get the number of courses in each skill group based on the activity
    skills_details = []
    for skill in skills:
        courses = frappe.get_all(child_table_name, filters={'skill_group': skill,"parenttype":activity}, fields=['parent'])
        #remove duplicate courses
        courses = list(set([course['parent'] for course in courses]))
        count = len(courses)
        skills_details.append({"skill": skill, "count": count})
    return skills_details




# child_table_entries = frappe.get_all('Course Sub-Skill Contribution', 
#                                          filters={'skill_group': ['in', skill_groups]},
#                                          fields=['parent'])

#     #extract unique course names from the result
#     course_names = list(set([entry['parent'] for entry in child_table_entries]))