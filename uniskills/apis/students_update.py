import frappe
from frappe import _
from datetime import datetime, timedelta
from statistics import mean
@frappe.whitelist(allow_guest=True)
def update_students_earned_points():
    
    main_skills = frappe.get_all('Skill Group', filters={'plot': 1}, fields=['name'])
    #make them a list 
    main_skills = [skill['name'] for skill in main_skills]
    
    #get the values of the current_semester and last_semester from the NUCTA Settings doctype
    settings = frappe.get_doc('NUCTA Settings')
    current_semester = settings.current_semester
    last_semester = settings.last_semester
    #get all enrollments from the academic course , extra course and clubs that have status_type = 'Completed'
    academic_courses_enrollments = frappe.get_all('Academic Course Enrollment', filters={'status_type': 'Completed'}, fields=['name', 'student_id', 'enrollment_to', 'semester'])
    extra_courses_enrollments = frappe.get_all('Extra Course Enrollment', filters={'status_type': 'Completed'}, fields=['name', 'student_id', 'enrollment_to', 'semester'])
    clubs_enrollments = frappe.get_all('Club Enrollment', filters={'status_type': 'Completed'}, fields=['name', 'student_id', 'enrollment_to', 'semester'])
    #for each enrollment , get the sub_skill and sub_skill_contribution from the child tables and add them to the enrollments list
    for enrollment in academic_courses_enrollments:
        enrollment['sub_skill'] = frappe.get_all('Academic Course Enrollment Contribution Table', filters={'parent': enrollment['name']}, fields=['sub_skill', 'sub_skill_contribution'])
    for enrollment in extra_courses_enrollments:
        enrollment['sub_skill'] = frappe.get_all('Extra Course Enrollment Contribution Table', filters={'parent': enrollment['name']}, fields=['sub_skill', 'sub_skill_contribution'])
    for enrollment in clubs_enrollments:
        enrollment['sub_skill'] = frappe.get_all('Club Enrollment Contribution Table', filters={'parent': enrollment['name']}, fields=['sub_skill', 'sub_skill_contribution'])

    enrollments = academic_courses_enrollments + extra_courses_enrollments + clubs_enrollments
    #in skills points child table inside the student doctype , put the enrollments while the fields are semester, sub_skill, role for the name and points for the sub_skill_contribution
    # for enrollment in enrollments:
    #     student = frappe.get_doc('Student', enrollment['student_id'])
    #     #remove what's inside the skills_points child table
    #     student.skills_points = []
    #     student.save(ignore_permissions=True)
    students = frappe.get_all('Student', fields=['name'])
    for student in students:
        student_doc = frappe.get_doc('Student', student['name'])
        student_doc.skills_points = []
        student_doc.save(ignore_permissions=True)

    for enrollment in enrollments:
        student = frappe.get_doc('Student', enrollment['student_id'])    
        #add the enrollments to the skills_points child table
        for sub_skill in enrollment['sub_skill']:
            student.append('skills_points', {
                'semester': enrollment['semester'],
                'sub_skill': sub_skill['sub_skill'],
                'role': enrollment['enrollment_to'],
                'points': sub_skill['sub_skill_contribution']
            })
        student.save(ignore_permissions=True)

    #for each student from the skill_points child table, calculate the total points for each sub_skill and calculate how many times the sub skill apeared and get each sub skill diminishing_return_factor from the Sub-Skill doctype  and put it in the skills_totals  child table with the fields sub_skill, current_points and current_diminished_points (which is the (points/number_of_appearances + ((number_of_apperances-1)*(1-diminishing_return_factor)*(points/number_of_appearances))) ) 
    students = frappe.get_all('Student', fields=['name'])
    for student in students:
        student_doc = frappe.get_doc('Student', student['name'])
        student_doc.skills_totals = []
        student_doc.save(ignore_permissions=True)
        
        sub_skill_totals = {}
        previous_sub_skill_totals = {}

        #calculate totals for current and previous semesters separately
        for sub_skill in student_doc.skills_points:

            if sub_skill.sub_skill not in sub_skill_totals:
                sub_skill_totals[sub_skill.sub_skill] = {
                    'total_points': 0,
                    'number_of_appearances': 0,
                    'diminishing_return_factor': frappe.get_doc('Sub-Skill', sub_skill.sub_skill).diminishing_return_factor
                }
            sub_skill_totals[sub_skill.sub_skill]['total_points'] += sub_skill.points
            sub_skill_totals[sub_skill.sub_skill]['number_of_appearances'] += 1
            if sub_skill.semester != current_semester:
                #for previous semesters
                if sub_skill.sub_skill not in previous_sub_skill_totals:
                    previous_sub_skill_totals[sub_skill.sub_skill] = {
                        'total_points': 0,
                        'number_of_appearances': 0,
                        'diminishing_return_factor': frappe.get_doc('Sub-Skill', sub_skill.sub_skill).diminishing_return_factor
                    }
                previous_sub_skill_totals[sub_skill.sub_skill]['total_points'] += sub_skill.points
                previous_sub_skill_totals[sub_skill.sub_skill]['number_of_appearances'] += 1

        #update skills_totals with both current and previous calculations
        for sub_skill, totals in sub_skill_totals.items():
            total_points = totals['total_points']
            number_of_appearances = totals['number_of_appearances']
            diminishing_return_factor = totals['diminishing_return_factor']
            if diminishing_return_factor == 0:
                current_diminished_points = total_points
            else:
                current_diminished_points = (float(total_points) / float(number_of_appearances)) + \
                                            ((float(number_of_appearances) - 1) * (1 - float(diminishing_return_factor)) *
                                            (float(total_points) / float(number_of_appearances)))
            if current_diminished_points > 1:
                current_diminished_points = 1
            
            #calculate previous_points if data is available for previous semesters
            if sub_skill in previous_sub_skill_totals:
                previous_totals = previous_sub_skill_totals[sub_skill]
                previous_total_points = previous_totals['total_points']
                previous_number_of_appearances = previous_totals['number_of_appearances']
                previous_diminishing_return_factor = previous_totals['diminishing_return_factor']
                if previous_diminishing_return_factor == 0:
                    previous_points = previous_total_points
                else:
                    previous_points = (float(previous_total_points) / float(previous_number_of_appearances)) + \
                                    ((float(previous_number_of_appearances) - 1) * (1 - float(previous_diminishing_return_factor)) *
                                    (float(previous_total_points) / float(previous_number_of_appearances)))
                if previous_points > 1:
                    previous_points = 1
            else:
                #if no data for previous semesters, set to 0
                previous_points = 0  

            #append the calculated values to the student's skills_totals table
            student_doc.append('skills_totals', {
                'sub_skill': sub_skill,
                'current_points': total_points,
                'current_diminished_points': current_diminished_points,
                'previous_points': previous_points
            })

        student_doc.save(ignore_permissions=True)

    #calculate the number_of_semesters for each student and put it in the student doctype but if the student has no enrollments, set it to 0 and calculate the semester only once 
    for student in students:
        student_doc = frappe.get_doc('Student', student['name'])
        if not student_doc.skills_points:
            student_doc.number_of_semesters = 0
        else:
            student_doc.number_of_semesters = int(len(set([sub_skill.semester for sub_skill in student_doc.skills_points])))

        student_doc.save(ignore_permissions=True)




    #normalization steps remain the same for current_diminished_points
    #minimum value after normalization
    a = 0.1  
    #maximum value after normalization
    b = 1.0  

    all_sub_skill_totals = {}
    all_sub_skill_previous_totals = {}
    sub_skill_averages = {}
    sub_skill_previous_averages = {}
    for student in students:
        student_doc = frappe.get_doc('Student', student['name'])
        for sub_skill in student_doc.skills_totals:
            if sub_skill.sub_skill not in all_sub_skill_totals:
                all_sub_skill_totals[sub_skill.sub_skill] = []
            all_sub_skill_totals[sub_skill.sub_skill].append(sub_skill.current_diminished_points)
            if sub_skill.semester != current_semester:
                if sub_skill.sub_skill not in all_sub_skill_previous_totals:
                    all_sub_skill_previous_totals[sub_skill.sub_skill] = []
                all_sub_skill_previous_totals[sub_skill.sub_skill].append(sub_skill.previous_points)
    #calculate averages for current and previous points
    for sub_skill, points in all_sub_skill_totals.items():
        sub_skill_averages[sub_skill] = sum(points) / len(points)

    for sub_skill, points in all_sub_skill_previous_totals.items():
        sub_skill_previous_averages[sub_skill] = sum(points) / len(points)
    #normalize the points for each sub_skill for each student to the range [a, b]
    for student in students:
        student_doc = frappe.get_doc('Student', student['name'])
        for sub_skill in student_doc.skills_totals:
            sub_skill_points = all_sub_skill_totals[sub_skill.sub_skill]
            max_points = max(sub_skill_points)
            min_points = min(sub_skill_points)
            average = mean(sub_skill_points)
            if average == 0:
                sub_skill.current_normalized_points = sub_skill.current_diminished_points 
            else:
                relative_value = (sub_skill.current_diminished_points) / average
                normalized_value = a + (relative_value * (b - a))
                if normalized_value > 1:
                    normalized_value = 1
                #map back to the original range
                mapped_value = min_points + (normalized_value * (max_points - min_points))
                sub_skill.current_normalized_points = mapped_value
        student_doc.save(ignore_permissions=True)

    for student in students:
        student_doc = frappe.get_doc('Student', student['name'])
        for sub_skill in student_doc.skills_totals:
            #normalize previous_points
            if sub_skill.sub_skill in all_sub_skill_previous_totals:
                sub_skill_previous_points = all_sub_skill_previous_totals[sub_skill.sub_skill]
            else:
                continue
            max_previous_points = max(sub_skill_previous_points)
            min_previous_points = min(sub_skill_previous_points)
            average_previous = mean(sub_skill_previous_points)
            if average_previous == 0:
                sub_skill.previous_normalized_points = sub_skill.previous_points
            else:
                relative_previous_value = (sub_skill.previous_points) / average_previous
                normalized_previous_value = a + (relative_previous_value * (b - a))
                if normalized_previous_value > 1:
                    normalized_previous_value = 1
                #map back to the original range
                mapped_previous_value = min_previous_points + (normalized_previous_value * (max_previous_points - min_previous_points))
                sub_skill.previous_normalized_points = mapped_previous_value

        #save the updated student document after normalizing previous_points
        student_doc.save(ignore_permissions=True)
        
    # from skills_totals child table, get the current_normalized_points and previous_normalized_points and get each sub skill its skill_group and contibution_weight from the Sub-Skill doctype and remove the sub skills that it's skill_group is not in the main_skills list and put in skill_groups_aggregation child table the fields skill_group, sub_skill, skill_total(which is the current_normalized_points) , current_normalized_total(which is the current_normalized_points * contribution_weight) , previous_total(which is the previous_normalized_points) and previous_normalized_total(which is the previous_normalized_points * contribution_weight)
    for student in students:
        student_doc = frappe.get_doc('Student', student['name'])
        student_doc.skill_groups_aggregation = []
        student_doc.save(ignore_permissions=True)
        for sub_skill in student_doc.skills_totals:
            sub_skill_doc = frappe.get_doc('Sub-Skill', sub_skill.sub_skill)
            if sub_skill_doc.skill_group not in main_skills:
                continue
            student_doc.append('skill_groups_aggregation', {
                'skill_group': sub_skill_doc.skill_group,
                'sub_skill': sub_skill.sub_skill,
                'skill_total': sub_skill.current_normalized_points,
                'current_normalized_total': sub_skill.current_normalized_points * sub_skill_doc.contribution_weight,
                'previous_total': sub_skill.previous_normalized_points,
                'previous_normalized_total': sub_skill.previous_normalized_points * sub_skill_doc.contribution_weight
            })
        student_doc.save(ignore_permissions=True)

    #from the skill_groups_aggregation child table, get the skill_group , current_normalized_total and previous_normalized_total and put them in the skill_groups_totals child table with the fields skill_group , current_skill_group_total (which is the sum of the current_normalized_total for each sub_skill in the skill_group *100) , previous_skill_group_total (which is the sum of the previous_normalized_total for each sub_skill in the skill_group *100) , current_adjusted_total (which is current_skill_group_total but if it's greater than 100, it's 100) and previous_adjusted_total (which is previous_skill_group_total but if it's greater than 100, it's 100)
    for student in students:
        student_doc = frappe.get_doc('Student', student['name'])
        student_doc.skill_groups_totals = []
        student_doc.save(ignore_permissions=True)
        skill_groups = {}
        for skill_group in student_doc.skill_groups_aggregation:
            if skill_group.skill_group not in skill_groups:
                skill_groups[skill_group.skill_group] = {
                    'current_skill_group_total': 0,
                    'previous_skill_group_total': 0
                }
            skill_groups[skill_group.skill_group]['current_skill_group_total'] += skill_group.current_normalized_total * 100
            skill_groups[skill_group.skill_group]['previous_skill_group_total'] += skill_group.previous_normalized_total * 100

        for skill_group, totals in skill_groups.items():
            current_skill_group_total = totals['current_skill_group_total']
            previous_skill_group_total = totals['previous_skill_group_total']
            current_adjusted_total = current_skill_group_total if current_skill_group_total <= 100 else 100
            previous_adjusted_total = previous_skill_group_total if previous_skill_group_total <= 100 else 100
            student_doc.append('skill_groups_totals', {
                'skill_group': skill_group,
                'current_skill_group_total': current_skill_group_total,
                'previous_skill_group_total': previous_skill_group_total,
                'current_adjusted_total': current_adjusted_total,
                'previous_adjusted_total': previous_adjusted_total
            })
        student_doc.save(ignore_permissions=True)

    return 'Students updated successfully'    



@frappe.whitelist(allow_guest=True)
def student_update_background_jobs():

    job = frappe.enqueue(update_students_earned_points, queue='long', timeout=0)

    return {"message": "Task has been started. It may take some time."}

        

