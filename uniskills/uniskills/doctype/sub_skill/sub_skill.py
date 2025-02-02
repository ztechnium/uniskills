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
        # Avoid recursion by setting a flag before updating
        if not getattr(self, '_sub_skill_updated', False):
            self._sub_skill_updated = True
            # Call the function to reset and update sub_skill_contributors only if necessary
            if self.should_update_sub_skill_contributors():
                self.reset_and_update_sub_skill_contributors()

    def should_update_sub_skill_contributors(self):
        # Add a condition to check if updating sub_skill_contributors is necessary
        # This could involve checking timestamps, modification flags, or other relevant conditions
        # For now, we'll assume it always needs updating (placeholder for future optimization)
        return True

    def reset_and_update_sub_skill_contributors(self):
        # Step 1: Clear all existing child table entries
        self.set('sub_skill_contributors', [])

        # Step 2: Fetch all contributions from Academic Course, Extra Course, and Club
        # Fetch contributions from all relevant child doctypes using their parent link to minimize database hits
        academic_courses = frappe.get_all("Course Sub-Skill Contribution", filters={
            'sub_skill': self.name,
            'parenttype': 'Academic Course'
        }, fields=["parent", "parenttype", "sub_skill_contribution", "diminishing_returns_factor", "role"])

        extra_courses = frappe.get_all("Extra Course Sub-Skill Contribution", filters={
            'sub_skill': self.name,
            'parenttype': 'Extra Course'
        }, fields=["parent", "parenttype", "sub_skill_contribution", "diminishing_returns_factor", "role"])

        clubs = frappe.get_all("Club Sub-Skill Contribution", filters={
            'sub_skill': self.name,
            'parenttype': 'Club'
        }, fields=["parent", "parenttype", "sub_skill_contribution", "diminishing_returns_factor", "role"])

        # Step 3: Append all contributions to the sub_skill_contributors child table
        for contribution in academic_courses + extra_courses + clubs:
            new_contributor = {
                'source_doctype': contribution['parenttype'],
                'source_id': contribution['parent'],
                'role': contribution['role'],
                'sub_skill_contribution': contribution['sub_skill_contribution'],
                'diminishing_returns_factor': contribution['diminishing_returns_factor']
            }
            self.append('sub_skill_contributors', new_contributor)

        # Step 4: Save the updated sub-skill document
        self.flags.ignore_validate_update_after_submit = True
        self.save(ignore_permissions=True)