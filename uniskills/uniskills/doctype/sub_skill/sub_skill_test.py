# # Copyright (c) 2024, ZTechnium and contributors
# # For license information, please see license.txt

# # import frappe
# from frappe.model.document import Document


# class SubSkill(Document):
# 	pass


#### Start of custom code:
# Copyright (c) 2024, ZTechnium and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class SubSkill(Document):
    def on_update(self):
        # Call the function to reset and update sub_skill_contributors
        self.reset_and_update_sub_skill_contributors()

    def reset_and_update_sub_skill_contributors(self):
        # Step 1: Clear existing child table entries by creating a dictionary of existing contributors
        # Key format is "source_doctype-source_id-role-sub_skill-sub_skill_contribution" to uniquely identify each contributor
        existing_contributors = {
            f"{c.source_doctype}-{c.source_id}-{c.role}-{c.sub_skill_contribution}": c
            for c in self.get('sub_skill_contributors')
        }
        
        new_contributors = []

        # Step 2: Fetch all contributions from Academic Course, Extra Course, and Club
        # Fetch contributions from all relevant child doctypes using their parent link to minimize database hits
        academic_courses = frappe.get_all("Course Sub-Skill Contribution", filters={
            'sub_skill': self.name,
            'parenttype': 'Academic Course'
        }, fields=["name", "parent", "sub_skill_contribution", "diminishing_returns_factor", "role"])

        extra_courses = frappe.get_all("Extra Course Sub-Skill Contribution", filters={
            'sub_skill': self.name,
            'parenttype': 'Extra Course'
        }, fields=["name", "parent", "sub_skill_contribution", "diminishing_returns_factor", "role"])

        clubs = frappe.get_all("Club Sub-Skill Contribution", filters={
            'sub_skill': self.name,
            'parenttype': 'Club'
        }, fields=["name", "parent", "sub_skill_contribution", "diminishing_returns_factor", "role"])

        # Process Academic Course contributions
        for contribution in academic_courses:
            key = f"Academic Course-{contribution['parent']}-{contribution['role']}-{contribution['sub_skill_contribution']}"
            new_contributor = {
                'source_doctype': "Academic Course",
                'source_id': contribution['parent'],
                'role': contribution['role'],
                'sub_skill_contribution': contribution['sub_skill_contribution'],
                'diminishing_returns_factor': contribution['diminishing_returns_factor']
            }
            # Append new contributors if they don't already exist or if there are changes
            if key not in existing_contributors:
                self.append('sub_skill_contributors', new_contributor)
            # Remove existing contributor from dictionary after processing
            existing_contributors.pop(key, None)

        # Process Extra Course contributions
        for contribution in extra_courses:
            key = f"Extra Course-{contribution['parent']}-{contribution['role']}-{contribution['sub_skill_contribution']}"
            new_contributor = {
                'source_doctype': "Extra Course",
                'source_id': contribution['parent'],
                'role': contribution['role'],
                'sub_skill_contribution': contribution['sub_skill_contribution'],
                'diminishing_returns_factor': contribution['diminishing_returns_factor']
            }
            # Append new contributors if they don't already exist or if there are changes
            if key not in existing_contributors:
                self.append('sub_skill_contributors', new_contributor)
            # Remove existing contributor from dictionary after processing
            existing_contributors.pop(key, None)

        # Process Club contributions
        for contribution in clubs:
            key = f"Club-{contribution['parent']}-{contribution['role']}-{contribution['sub_skill_contribution']}"
            new_contributor = {
                'source_doctype': "Club",
                'source_id': contribution['parent'],
                'role': contribution['role'],
                'sub_skill_contribution': contribution['sub_skill_contribution'],
                'diminishing_returns_factor': contribution['diminishing_returns_factor']
            }
            # Append new contributors if they don't already exist or if there are changes
            if key not in existing_contributors:
                self.append('sub_skill_contributors', new_contributor)
            # Remove existing contributor from dictionary after processing
            existing_contributors.pop(key, None)

        # Step 3: Remove stale contributors that no longer have a valid contribution
        for key, contributor in existing_contributors.items():
            self.remove(contributor)

        # Step 4: Save the updated sub-skill document only if changes were made to prevent unnecessary database operations
        if new_contributors or existing_contributors:
            self.flags.ignore_validate_update_after_submit = True
            self.save(ignore_permissions=True)