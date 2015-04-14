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
    webapp2.Route('/admin/removeUser', removeUserHandler),
    webapp2.Route('/student', StudentHandler, name='student'),
    webapp2.Route('/faculty', FacultyHandler, name='faculty'),
    webapp2.Route('/faculty/info', FacultyInfoHandler),
    webapp2.Route('/faculty/courses', FacultyCoursesHandler),
    webapp2.Route('/faculty/requests', FacultyRequestsHandler),
    webapp2.Route('/student/info', StudentInfoHandler),
    webapp2.Route('/student/cart', CartHandler),
    webapp2.Route('/admin/addDepartment', addDepartmentHandler),
    webapp2.Route('/admin/floatCourse',floatCourseHandler),
    webapp2.Route('/admin/resources',resourcesHandler)
]
app = webapp2.WSGIApplication(url_map, debug=True, config=config)

logging.getLogger().setLevel(logging.DEBUG)
