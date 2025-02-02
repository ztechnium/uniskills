import frappe
from frappe import _
from frappe.utils.password import update_password

@frappe.whitelist(allow_guest=True)
def custom_login(usr):

    #check if there is a student with email field as usr in the student doctype
    if not frappe.db.exists('Student', {'email': usr}): 
        return {"success_key": 0, "message": "Student does not exist. Please contact Student Affairs"}
    #get the student_name
    student_name = frappe.get_value('Student', {'email': usr}, 'student_name')
    # check if there is a user
    if not frappe.db.exists('User', usr):
        # Create a new user if it doesn't exist
        user = frappe.new_doc('User')
        user.email = usr
        user.first_name = student_name
        user.send_welcome_email = 0
        user.save(ignore_permissions=True)



    try:
        # Attempt to authenticate the user
        frappe.local.login_manager = frappe.auth.LoginManager()
        frappe.local.login_manager.user = usr
        frappe.local.login_manager.post_login()

        # Generate or retrieve API keys
        api_key, api_secret, token = set_password_and_generate_keys(usr)
        # Successful login response
        return {
            "success_key": 1,
            "message": "Authentication success",
            "sid": frappe.session.sid,
            "token": token,
            "username": usr,
        }

    except frappe.exceptions.AuthenticationError:
        # Authentication failed
        return {"success_key": 0, "message": "Authentication Error"}
    




def set_password_and_generate_keys(user_email):
    # Check if the user exists
    user = frappe.get_doc('User', user_email)
    
    # Check if API key and API secret already exist
    if user.api_key and user.api_secret:
        api_key = user.api_key
        api_secret = user.get_password('api_secret')
    else:

        # Generate unique API key and secret with collision check
        api_key = frappe.generate_hash(length=15)
        while frappe.db.exists('User', {'api_key': api_key}):
            api_key = frappe.generate_hash(length=15)
        
        api_secret = frappe.generate_hash(length=15)
        while frappe.db.exists('User', {'api_secret': api_secret}):
            api_secret = frappe.generate_hash(length=15)

        # Save the API key and secret to the user document
        user.api_key = api_key
        user.api_secret = api_secret
        user.save(ignore_permissions=True)

    # Create and return the token
    token = f"token {api_key}:{api_secret}"
    return api_key, api_secret, token




@frappe.whitelist()
def test():
    #get the user email
    user = frappe.session.user
    #get the student by email
    student = frappe.get_doc('Student', {'email': user})
    return {"user":user , "student": student}