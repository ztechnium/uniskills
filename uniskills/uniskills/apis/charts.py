import frappe
from frappe import _
from datetime import datetime, timedelta


@frappe.whitelist()
def get_current_and_last_skill_chart():
    
    user = frappe.session.user
    #get the student's id by the user's email
    student = frappe.get_all('Student', filters={'email': user}, fields=['name'])
    student_id = student[0]['name']
    #get the main skills
    main_skills = frappe.get_all('Skill Group', filters={'plot': 1}, fields=['name'])
    main_skills = [skill['name'] for skill in main_skills]
    #get current_adjusted_total, previous_adjusted_total and skill_group from Skill Groups Totals child table
    skill_groups = frappe.get_all('Skill Groups Totals', filters={'parent': student_id}, fields=['current_adjusted_total', 'previous_adjusted_total', 'skill_group'])
    #check if all the main skills are in the skill_groups list if not add them with current_adjusted_total and previous_adjusted_total 0
    for skill in main_skills:
        if skill not in [skill_group['skill_group'] for skill_group in skill_groups]:
            skill_groups.append({'current_adjusted_total': 0, 'previous_adjusted_total': 0, 'skill_group': skill})

    current_semester = {}
    last_semester = {}

    for skill_group in skill_groups:
        current_semester[skill_group['skill_group']] = skill_group['current_adjusted_total']
        last_semester[skill_group['skill_group']] = skill_group['previous_adjusted_total']

    return {"result": skill_groups, "current_semester": current_semester, "last_semester": last_semester}



@frappe.whitelist()
def get_sub_skills_details(skill_group):
    #check if skill_group has %20 in it and replace it with space
    skill_group = skill_group.replace('%20', ' ')
    user = frappe.session.user
    #get the student's id by the user's email
    student = frappe.get_all('Student', filters={'email': user}, fields=['name'])
    student_id = student[0]['name']

    #get the sub_skill , current_normalized_total and previous_total while skill_group is the skill_group from the skill_groups_aggregation child table
    sub_skills = frappe.get_all('Skill Groups Aggregation', filters={'parent': student_id, 'skill_group': skill_group}, fields=['sub_skill', 'skill_total', 'previous_total'])
    current_semester = {}
    last_semester = {}
    for sub_skill in sub_skills:
        sub_skill['skill_total'] = round(sub_skill['skill_total'] * 100, 2)
        sub_skill['previous_total'] = round(sub_skill['previous_total'] * 100 , 2)
        current_semester[sub_skill['sub_skill']] = round(sub_skill['skill_total'] , 2)
        last_semester[sub_skill['sub_skill']] = round(sub_skill['previous_total'] , 2)

    return {"result": sub_skills, "current_semester": current_semester, "last_semester": last_semester}



@frappe.whitelist()
def charts_comparison():
    
    #get the current and last chart from get_current_and_last_skill_chart function
    skill_groups , current_semester, last_semester = get_current_and_last_skill_chart().values()
    
    #get from the NUCTA Settings doctype the values of the child tables NUCTA Top Stats , NUCTA Average Stats and Market Requirement Stats , get the fields skill_group and value and put them like current and last semester 
    top_stats = frappe.get_all('NUCTA Top Stats', filters={'parent': 'NUCTA Settings'}, fields=['skill_group', 'value'])
    top_stats = {top_stat['skill_group']: top_stat['value'] for top_stat in top_stats}
    average_stats = frappe.get_all('NUCTA Average Stats', filters={'parent': 'NUCTA Settings'}, fields=['skill_group', 'value'])
    average_stats = {average_stat['skill_group']: average_stat['value'] for average_stat in average_stats}
    market_requirement_stats = frappe.get_all('Market Requirement Stats', filters={'parent': 'NUCTA Settings'}, fields=['skill_group', 'value'])
    market_requirement_stats = {market_requirement_stat['skill_group']: market_requirement_stat['value'] for market_requirement_stat in market_requirement_stats}

    return {"current_semester": current_semester, "last_semester": last_semester, "top_stats": top_stats, "average_stats": average_stats, "market_requirement_stats": market_requirement_stats}


@frappe.whitelist()
def list_courses_for_charts(skill_group):
    user = frappe.session.user
    #get the student's id by the user's email
    student = frappe.get_all('Student', filters={'email': user}, fields=['name'])
    student_id = student[0]['name']
    #check if skill_group has %20 in it and replace it with space
    skill_group = skill_group.replace('%20', ' ')
    not_enrolled_academic_courses = []
    not_enrolled_extra_courses = []
    not_enrolled_clubs = []
    #list all the courses that have the skill_group in its child table 
    academic_courses = frappe.get_all('Course Sub-Skill Contribution', filters={'skill_group': skill_group}, fields=['parent'])
    academic_courses = [course['parent'] for course in academic_courses]
    #remove duplicates
    academic_courses = list(set(academic_courses))
    #add key activity
    academic_courses = [{"activity": "Academic Course", "course_id": course,"name": course} for course in academic_courses]
    #get the course's title 
    for course in academic_courses:
        course['course_title'] = frappe.get_value('Academic Course', course['course_id'], 'course_name')
        #add course skills points to the course 
        course['course_skill_groups'],course['sub_skills_contribution'] = course_skills_points("Academic Course", course['course_id']).values()
        #check if the student enrolled in the course
        enrollment = frappe.get_all('Academic Course Enrollment', filters={'student_id': student_id, 'enrollment_to': course['course_id']}, fields=['name'])
        course['status'] = frappe.get_value('Academic Course', course['course_id'], 'enrollment_status')
        if enrollment:
            course['is_enrolled'] = True
        else:
            course['is_enrolled'] = False
            if course['status'] == "Open":
                not_enrolled_academic_courses.append(course)
        

    extra_courses = frappe.get_all('Extra Course Sub-Skill Contribution', filters={'skill_group': skill_group}, fields=['parent'])
    extra_courses = [course['parent'] for course in extra_courses]
    extra_courses = list(set(extra_courses))
    extra_courses = [{"activity": "Extra Course", "course_id": course,"name": course} for course in extra_courses]
    for course in extra_courses:
        course['course_title'] = frappe.get_value('Extra Course', course['course_id'], 'name')
        course['course_skill_groups'],course['sub_skills_contribution'] = course_skills_points("Extra Course", course['course_id']).values()
        enrollment = frappe.get_all('Extra Course Enrollment', filters={'student_id': student_id, 'enrollment_to': course['course_id']}, fields=['name'])
        course['status'] = frappe.get_value('Extra Course', course['course_id'], 'enrollment_status')
        if enrollment:
            course['is_enrolled'] = True
        else:
            course['is_enrolled'] = False
            if course['status'] == "Open":
                not_enrolled_extra_courses.append(course)
    club_courses = frappe.get_all('Club Sub-Skill Contribution', filters={'skill_group': skill_group}, fields=['parent'])
    club_courses = [course['parent'] for course in club_courses]
    club_courses = list(set(club_courses))
    club_courses = [{"activity": "Club", "course_id": course,"name": course} for course in club_courses]
    for course in club_courses:
        course['course_title'] = frappe.get_value('Club', course['course_id'], 'name')
        course['course_skill_groups'],course['sub_skills_contribution'] = course_skills_points("Club", course['course_id']).values()
        enrollment = frappe.get_all('Club Enrollment', filters={'student_id': student_id, 'enrollment_to': course['course_id']}, fields=['name'])
        course['status'] = frappe.get_value('Club', course['course_id'], 'enrollment_status')
        if enrollment:
            course['is_enrolled'] = True
        else:
            course['is_enrolled'] = False
            if course['status'] == "Open":
                not_enrolled_clubs.append(course)



    return {"academic_courses": not_enrolled_academic_courses, "extra_courses": not_enrolled_extra_courses, "clubs": not_enrolled_clubs}



    





@frappe.whitelist()
def course_skills_points(activity,activity_id):
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
    if activity == "Club":
        total_course_skills = frappe.get_all(child_table_name, filters={'parent': activity_id}, fields=['skill_group','sub_skill_contribution','sub_skill','role'])
    else:    
        total_course_skills = frappe.get_all(child_table_name, filters={'parent': activity_id}, fields=['skill_group','sub_skill_contribution','sub_skill'])
    #remove the skill groups that are not in the main skills
    course_skills = [skill for skill in total_course_skills if skill['skill_group'] in main_skills]
    # for each course skill, get the contribution from the field contribution_weight from the Sub-Skill doctype
    for skill in course_skills:
        skill['sub_skill_contribution_percentage'] = frappe.get_value('Sub-Skill', skill['sub_skill'], 'contribution_weight')
        skill['sub_skill_contribution_percentage'] = int((float(skill['sub_skill_contribution']) * float(skill['sub_skill_contribution_percentage'])) * 100)

    #group the sub skills by the skill group and get the total contribution for each skill group
    skill_groups = {skill: 0 for skill in main_skills}
    sub_skill_contribution = {}
    for skill in course_skills:
        if skill['skill_group'] not in skill_groups:
            skill_groups[skill['skill_group']] = 0
        skill_groups[skill['skill_group']] += float(skill['sub_skill_contribution_percentage'])



    for skill in total_course_skills:
        #put in sub_skill_contribution the sub_skill_contribution for each sub_skill form the course_skills list
        if skill['sub_skill'] not in sub_skill_contribution and activity == "Club":
            sub_skill_contribution[f"{skill['role']}_{skill['sub_skill']}"] = 0

        if activity == "Club":    
            sub_skill_contribution[f"{skill['role']}_{skill['sub_skill']}"] += int(float(skill['sub_skill_contribution'])*100)
        else:
            sub_skill_contribution[skill['sub_skill']] = int(float(skill['sub_skill_contribution'])*100)

    

    return {"course_points": skill_groups, "sub_skill_contribution": sub_skill_contribution}
