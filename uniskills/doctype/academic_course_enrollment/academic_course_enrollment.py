# # Copyright (c) 2024, ZTechnium and contributors
# # For license information, please see license.txt

# # import frappe
# from frappe.model.document import Document


# class AcademicCourseEnrollment(Document):
# 	pass

# Copyright (c) 2024, ZTechnium and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class AcademicCourseEnrollment(Document):
    def on_update(self):
        # Trigger the function to copy contributions from the linked Academic Course
        if not self.flags.updating_contributions:
            self.update_enrollment_contributions()

    def update_enrollment_contributions(self):
        # Set flag to prevent recursion
        self.flags.updating_contributions = True

        # Clear the existing child table entries
        self.set('academic_course_enrollment_contribution_table', [])

        # Fetch the linked Academic Course contributions
        if not self.enrollment_to:
            frappe.throw("Enrollment must be linked to an Academic Course.")

        course_contributions = frappe.get_all(
            "Course Sub-Skill Contribution",
            filters={
                'parent': self.enrollment_to,
                'parenttype': 'Academic Course'
            },
            fields=["sub_skill", "sub_skill_contribution", "role"]
        )

        # Debugging: Log fetched contributions
        print(f"Fetched contributions for course {self.enrollment_to}: {course_contributions}")

        # Populate the child table with fetched contributions
        for contribution in course_contributions:
            # Debugging: Log each contribution before filtering
            print(f"Processing contribution: {contribution}")
            if contribution['sub_skill'] and contribution['sub_skill_contribution'] and contribution['role']:
                self.append('academic_course_enrollment_contribution_table', {
                    'sub_skill': contribution['sub_skill'],
                    'sub_skill_contribution': contribution['sub_skill_contribution'],
                    'role': contribution['role']
                })
            else:
                # Debugging: Log skipped contributions
                print(f"Skipped contribution due to missing fields: {contribution}")

        # Ensure changes are saved, bypassing validation if necessary
        self.flags.ignore_validate_update_after_submit = True
        self.save(ignore_permissions=True)

        # Unset the flag after updating
        self.flags.updating_contributions = False

        # Print statements for debugging purposes
        print(f"Updated contributions for enrollment {self.name} linked to course {self.enrollment_to}")
        for contribution in self.academic_course_enrollment_contribution_table:
            print(f"Added contribution: {contribution.sub_skill} - {contribution.sub_skill_contribution} - {contribution.role}")