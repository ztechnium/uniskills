import frappe
from frappe import _
from datetime import datetime, timedelta


@frappe.whitelist()
def student_profile():
    current_url = frappe.request.url
    #split the url from "/api/method/" and get the first part
    current_url = current_url.split("/api/method/")[0]
    user = frappe.session.user
    #get the student's id by the user's email
    student = frappe.get_all('Student', filters={'email': user}, fields=['name'])
    student_id = student[0]['name']
    #student_id = "211000390-Ahmed Hesham Almashad"
    #get the student's info
    student = frappe.get_doc('Student', student_id)
    #get the student name , college and department
    student_name = student.student_name
    college = student.college
    department = student.department
    if student.student_image:
        #check if the student image starts with /files or /private/files
        if student.student_image.startswith("/files") or student.student_image.startswith("/private/files"):
            student_image = current_url + student.student_image
        else:
            student_image = student.student_image
    else:
        student_image = ""
    #get the student's courses numbers
    number_of_enrolled_courses = get_course_counts(student_id=student_id)
    number_of_completed_courses = get_course_counts(student_id=student_id,status='Completed')
    number_of_pending_courses = get_course_counts(student_id=student_id,status='Pending')
    number_of_in_progress_courses = get_course_counts(student_id=student_id,status='Processing')
    #get the current semester
    if student.number_of_semesters:
        current_semester = int(student.number_of_semesters)
    else:
        current_semester = 0
    return {
        "student_name": student_name,
        "college": college,
        "department": department,
        "current_semester": current_semester,
        "number_of_enrolled_courses": number_of_enrolled_courses,
        "number_of_completed_courses": number_of_completed_courses,
        "number_of_pending_courses": number_of_pending_courses,
        "number_of_in_progress_courses": number_of_in_progress_courses,
        "student_image": student_image
    }


def get_course_counts(student_id,status=None):
    filters = {'student_id': student_id}
    if status:
        filters['status_type'] = status
    academic_courses = frappe.get_all('Academic Course Enrollment', filters=filters, fields=['name'])
    extra_courses = frappe.get_all('Extra Course Enrollment', filters=filters, fields=['name'])
    club_courses = frappe.get_all('Club Enrollment', filters=filters, fields=['name'])
    return len(academic_courses) + len(extra_courses) + len(club_courses)




@frappe.whitelist()
def get_student_activities(activity):
    current_url = frappe.request.url
    #split the url from "/api/method/" and get the first part
    current_url = current_url.split("/api/method/")[0]
    user = frappe.session.user
    #get the student's id by the user's email
    student = frappe.get_all('Student', filters={'email': user}, fields=['name'])
    student_id = student[0]['name']
    #student_id = "211000390-Ahmed Hesham Almashad"
    #check if activity has %20 in it and replace it with a space
    if "%20" in activity:
        activity = activity.replace("%20", " ")
    #get the doctype based on the activity
    if activity == "Internships":
        return "No internships available"
    if activity == "Academic Course":
        doctype_name = "Academic Course Enrollment"
        child_table_name = "Course Sub-Skill Contribution"
    elif activity == "Extra Course":
        doctype_name = "Extra Course Enrollment"
        child_table_name = "Extra Course Sub-Skill Contribution"
    else:
        doctype_name = "Club Enrollment"
        child_table_name = "Club Sub-Skill Contribution"

    #get the main skills
    main_skills = frappe.get_all('Skill Group', filters={'plot': 1}, fields=['name'])
    main_skills = [skill['name'] for skill in main_skills]
    #get the student's courses
    courses = frappe.get_all(doctype_name, filters={'student_id': student_id}, fields=['enrollment_to', 'status'])
    #get the courses' info from the course's doctype based on the activity
    courses_info = []
    for course in courses:
        course_info = {}
        if activity == "Academic Course":
            detailed_course_info = frappe.get_doc('Academic Course', course['enrollment_to'])
            course_info['course_name'] = detailed_course_info.course_name
        elif activity == "Extra Course":
            detailed_course_info = frappe.get_doc('Extra Course', course['enrollment_to'])
            course_info['course_name'] = detailed_course_info.name
        else:
            detailed_course_info = frappe.get_doc('Club', course['enrollment_to'])
            course_info['course_name'] = detailed_course_info.name
        if course['status']:
            try:
                #get the status_type from the status
                status_type = frappe.get_value('Enrollment Status', course['status'], 'status_type')
                course_info['status'] = status_type
            except:
                course_info['status'] = course['status']
        else:
            course_info['status'] = course['status']
        course_info['name'] = detailed_course_info.name
        course_info['school'] = detailed_course_info.school
        course_info['skills'] = frappe.get_all(child_table_name, filters={'parent': detailed_course_info.name}, fields=['skill_group'])
        course_info['skills'] = [skill['skill_group'] for skill in course_info['skills']]
        #remove duplicate skills
        course_info['skills'] = list(set(course_info['skills']))
        #remove the skill groups that are not in the main skills
        course_info['skills'] = [skill for skill in course_info['skills'] if skill in main_skills]
        course_info['semester'] = detailed_course_info.semester
        if detailed_course_info.image:
            course_info['image'] = current_url + detailed_course_info.image
        else:
            course_info['image'] = ""
        courses_info.append(course_info)

    return courses_info


@frappe.whitelist()
def student_internships():
    current_url = frappe.request.url
    #split the url from "/api/method/" and get the first part
    current_url = current_url.split("/api/method/")[0]
    user = frappe.session.user
    #get the student's id by the user's email
    student = frappe.get_all('Student', filters={'email': user}, fields=['name'])
    student_id = student[0]['name']
    #student_id = "211000390-Ahmed Hesham Almashad"
    #get the student's internships
    internships = frappe.get_all('Job Application', filters={'student_id': student_id}, fields=['apply_for', 'status'])
    internships_info = []
    for internship in internships:
        internship_info = {}
        detailed_internship_info = frappe.get_doc('Job Internship', internship['apply_for'])
        internship_info['name'] = detailed_internship_info.name
        internship_info['title'] = detailed_internship_info.activity_name
        internship_info['company'] = detailed_internship_info.hiring_company
        internship_info['experience_level'] = detailed_internship_info.experience_level
        internship_info['work_mode'] = detailed_internship_info.work_mode
        internship_info['location'] = detailed_internship_info.location
        internship_info['job_description'] = detailed_internship_info.job_description
        internship_info['skills'] = frappe.get_all('Internship Skills Requirement', filters={'parent': detailed_internship_info.name}, fields=['required_skill','minimum_requirement'])
        if internship['status']:
            internship_info['status'] = frappe.get_value('Enrollment Status', internship['status'], 'status_type')
        else:
            internship_info['status'] = ""
        #get customer image
        customer = frappe.get_all('Customer', filters={'name': detailed_internship_info.hiring_company}, fields=['image'])
        if customer:
            if customer[0]['image']:
                internship_info['image'] = current_url + customer[0]['image']
            else:
                internship_info['image'] = ""    
        else:
            internship_info['image'] = ""
        internships_info.append(internship_info)
    return internships_info


@frappe.whitelist()
def get_student_skills_percentage():
    user = frappe.session.user
    #get the student's id by the user's email
    student = frappe.get_all('Student', filters={'email': user}, fields=['name'])
    student_id = student[0]['name']
    #get the skill_group , sub_skill and the current_normalized_total from the skill_group_aggregation child table
    skills = frappe.get_all('Skill Groups Aggregation', filters={'parent': student_id}, fields=['skill_group', 'sub_skill', 'skill_total'])
    #sort them by the current_normalized_total in descending order and typecast the current_normalized_total to a float
    skills = sorted(skills, key=lambda x: float(x['skill_total']), reverse=True)
    #multiply the current_normalized_total by 100 to get the percentage
    for skill in skills:
        skill['current_normalized_total_percentage'] = round(float(skill['skill_total']) * 100 ,2)
    return {"skills": skills}
