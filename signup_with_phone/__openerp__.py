{
    'name': 'Signup with Mobile Number',
    'category': 'Website',
    'summary': 'Signup with Mobile(If not Email).',
    'website': '',
    'version': '1.0',
    'description': """
    This module can create users from the Odoo main screen as an external user and signup with the same credentials. 
    It mainly provides validation of emailid and mobile number during signup. 
    User id has to be  unique for every account so email id and mobile number cannot be duplicated.
    """,
    'depends': ['auth_signup'],
    'data': [
        'views/auth_signup_inherit.xml',
    ],
    'installable': True,
    'application': True,
}