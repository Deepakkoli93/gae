import webapp2
from handlers.misc import *
from handlers.admin import *
from handlers.student import *
from handlers.faculty import *

url_map = [
    webapp2.Route('/', MainHandler, name='main'),
    webapp2.Route('/admin/signup', SignupHandler),
    webapp2.Route('/<type:v|p>/<user_id:\d+>-<signup_token:.+>',
      handler=VerificationHandler, name='verification'),
    webapp2.Route('/password', SetPasswordHandler),
    webapp2.Route('/login', LoginHandler, name='login'),
    webapp2.Route('/logout', LogoutHandler, name='logout'),
    webapp2.Route('/forgot', ForgotPasswordHandler, name='forgot'),
    webapp2.Route('/authenticated', AuthenticatedHandler, name='authenticated'),
    webapp2.Route('/admin', AdminHandler, name='admin'),
    webapp2.Route('/admin/info', AdminInfoHandler),
    webapp2.Route('/admin/removeUser', removeUserHandler),
    webapp2.Route('/student', StudentHandler, name='student'),
    webapp2.Route('/faculty', FacultyHandler, name='faculty'),
    webapp2.Route('/faculty/info', FacultyInfoHandler),
    webapp2.Route('/faculty/courses', FacultyCoursesHandler, name='fac_courses'),
    webapp2.Route('/faculty/requests', FacultyRequestsHandler),
    webapp2.Route('/student/info', StudentInfoHandler),
    webapp2.Route('/student/cart', CartHandler, name='cart'),
    webapp2.Route('/faculty/resource_upload',facResourceuploadHandler),
    webapp2.Route('/student/courses',StudentCoursesHandler, name='stu_courses'),
    webapp2.Route('/student/view_resource', viewresourceHandler),
    webapp2.Route('/student/resources', studentresourcesHandler),
    webapp2.Route('/student/resource_upload',stuResourceuploadHandler),
    webapp2.Route('/admin/addDepartment', addDepartmentHandler),
    webapp2.Route('/admin/floatCourse',floatCourseHandler),
    webapp2.Route('/admin/resources',resourcesHandler),
    webapp2.Route('/admin/resource_upload',resourceuploadHandler),
    webapp2.Route('/admin/view_resource', viewresourceHandler),
    webapp2.Route('/godmode',GodmodeHandler)
]
app = webapp2.WSGIApplication(url_map, debug=True, config=config)

logging.getLogger().setLevel(logging.DEBUG)
