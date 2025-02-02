# # Copyright (c) 2024, ZTechnium and contributors
# # For license information, please see license.txt

# import frappe
# from frappe.model.document import Document

# class Semester(Document):
#     def before_save(self):
#         # If the current semester is marked as active
#         if self.active == 1:
#             # Fetch all other semesters that are active
#             other_active_semesters = frappe.get_all("Semester", filters={
#                 "name": ["!=", self.name],
#                 "active": 1
#             }, fields=["name"])

#             # Set active = 0 for all other semesters
#             for semester in other_active_semesters:
#                 frappe.db.set_value("Semester", semester["name"], "active", 0)
			

#             # Commit the changes to the database to ensure no conflicts
#             frappe.db.commit()

# 			# Update the current_semester in NUCTA Settings
#             frappe.db.set_value("NUCTA Settings", None, "current_semester", self.name)
#             frappe.db.commit()

import frappe
from frappe.model.document import Document

class Semester(Document):
    def before_save(self):
        # If the current semester is marked as active
        if self.active == 1:
            # Fetch all other semesters that are active
            other_active_semesters = frappe.get_all("Semester", filters={
                "name": ["!=", self.name],
                "active": 1
            }, fields=["name"])

            # Set active = 0 for all other semesters
            for semester in other_active_semesters:
                frappe.db.set_value("Semester", semester["name"], "active", 0)

            # Commit the changes to the database to ensure no conflicts
            frappe.db.commit()

            # Update the current_semester in NUCTA Settings
            frappe.db.set_value("NUCTA Settings", None, "current_semester", self.name)

            # Update the last_semester in NUCTA Settings using the previous_semester of the active semester
            frappe.db.set_value("NUCTA Settings", None, "last_semester", self.previous_semester)
            
            # Commit the changes to the database for NUCTA Settings
            frappe.db.commit()
