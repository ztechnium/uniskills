# # Copyright (c) 2024, ZTechnium and contributors
# # For license information, please see license.txt

# # import frappe
# from frappe.model.document import Document


# class ClubEnrollment(Document):
# 	pass


# Copyright (c) 2024, ZTechnium and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class ClubEnrollment(Document):
    def on_update(self):
        # Trigger the function to copy contributions from the linked Club
        if not self.flags.updating_contributions:
            self.update_enrollment_contributions()

    def update_enrollment_contributions(self):
        # Set flag to prevent recursion
        self.flags.updating_contributions = True

        # Clear the existing child table entries
        self.set('club_enrollment_contribution_table', [])

        # Fetch the linked Club contributions
        if not self.enrollment_to:
            frappe.throw("Enrollment must be linked to a Club.")

        # Fetch the enrolled_as value (Head or Member)
        enrolled_as = self.enrolled_as
        if not enrolled_as:
            frappe.throw("Enrollment must specify whether enrolled as Head or Member.")

        club_contributions = frappe.get_all(
            "Club Sub-Skill Contribution",
            filters={
                'parent': self.enrollment_to,
                'parenttype': 'Club',
                'role': enrolled_as  # Filter contributions based on the enrolled_as value
            },
            fields=["sub_skill", "sub_skill_contribution", "role"]
        )

        # Debugging: Log fetched contributions
        print(f"Fetched contributions for club {self.enrollment_to} with role {enrolled_as}: {club_contributions}")

        # Populate the child table with fetched contributions
        for contribution in club_contributions:
            # Debugging: Log each contribution before filtering
            print(f"Processing contribution: {contribution}")
            if contribution['sub_skill'] and contribution['sub_skill_contribution']:
                self.append('club_enrollment_contribution_table', {
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
        print(f"Updated contributions for enrollment {self.name} linked to club {self.enrollment_to}")
        for contribution in self.club_enrollment_contribution_table:
            print(f"Added contribution: {contribution.sub_skill} - {contribution.sub_skill_contribution} - {contribution.role}")